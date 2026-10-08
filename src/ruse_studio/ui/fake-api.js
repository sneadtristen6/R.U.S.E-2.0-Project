// A made-up StudioApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=noindex shows the "no index yet" state, ?fake=nomod the Studio before any mod is picked, ?fake=notfound no
// game found, ?fake=testfails a Test in game that fails, with its Troubleshoot link; ?fake=testmistakes one the build
// stopped on two mistakes in the mods, each with its fix; ?fake=backup, ?fake=oldbackup,
// ?fake=nospace and ?fake=running the clean game backup's states, in Settings; ?fake=firstbackup the installer's
// "Keep a clean copy" ask, made on the first start; ?fake=lang "Choose your language" with the game set to French in
// Steam). Only English, French
// and Chinese words are included here; the real Studio has all ten languages. It does nothing in the real Studio window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  // ?fake=testmistakes: the two mistakes that stopped the owner's tests on 2026-10-02, as the build words them
  const FAKE_MISTAKES = [
    "test, test2: M04_cotentin: scenario.toml: the spawn of Unit_Konoe_Shidan at (2029166, 1329890) in "
      + "leveldesign_3v3_v01.scenario is for camp 1, but leveldesign_3v3_v01.scenario is a skirmish map's scenario, and a "
      + "skirmish game spawns only neutral items: the game would leave it out without a word. Set camp = -1 (or leave "
      + "camp out), or spawn it in an Operation's scenario",
    "test, test2: M04_cotentin: road 2 (its ends joined no road within 12 m) would be cut off from the rest of the map's "
      + "roads; every road network the game ships is one piece, and supply routes between two pieces fail. Draw each "
      + "end onto a road, or give the road a larger join"];
  const prefs = {};  // what the real app keeps in settings.json (rusemod.home.PrefsCalls)
  const words = {
    us: { update_out: "{app} {version} is out.", update_now: "Update", whats_new: "What's new", release_page: "Release page", layers_title: "See-through layers", tip_layer_alpha: "How much of this layer shows: 0 % hides it, 100 % is as usual.", legend_title: "Colours on the ground", legend_cover_own: "Cover the map has: units hide here", legend_cover_painted: "Cover you painted (Cover brush, Forest)", legend_cover_town: "Cover the Town tool painted around a town", legend_move_none: "No unit can go here (water, cliffs, Block)", legend_move_infantry: "No tanks: infantry go, and supply trucks drive through woods (woods, Block vehicles)", legend_move_vehicles: "Vehicles only: infantry can't go (Block infantry)", legend_erase: "Erased: taken away when the mod is built", changes_before: "In your version ({version})", changes_now: "In {version}", changes_none: "The release notes list no changes: open the release page for them.", update_progress: "Downloading the update… {pct}", update_installing: "Installing: {app} closes and opens again by itself.", update_repo: "(This copy runs from the repo: update it with git pull.)", update_failed: "The update didn't work: {why}",
      language: "Language", game_names: "Code names", search: "Search", all: "All", ground: "Ground",
      infantry: "Infantry", air: "Air", buildings: "Buildings", units: "{n} units", parts: "Parts", uses: "Uses",
      own_part: "its own", shared_part: "shared with other units", used_by: "Used by", copy_address: "Copy address",
      no_index: "No game index yet. Build it once (about a minute).", build_index: "Build the index",
      pick_unit: "Pick a unit on the left.", mod: "Unit mod", new_mod: "New mod…", open_folder: "Open a mod folder…",
      export_mod: "Export mod…", version: "Version", author: "Author", description: "Description", export: "Export",
      export_help: "One file to share: the mod folder packed. The version, author and description are kept in the mod.",
      mod_name: "Name of the new mod", map_project: "Map changes", no_map: "Pick or start a set of map changes to save them in.", new_map: "New map changes…", export_map: "Export map…", map_name: "Name for these map changes", tip_pick_mod: "The mod your unit changes are saved in. Maps have their own list on the Maps tab.", tip_pick_map: "Where your changes to the game's maps are saved (ground, roads, buildings, scenario), apart from your unit mod: changes to any of the game's own maps, and the new maps you make with Duplicate map. Test in game plays them with your unit mod.", create: "Create", cancel: "Cancel", close: "Close",
      no_mod: "Pick or make a mod to save changes in.", test_in_game: "Test in game", was: "was {v}", reset: "Undo",
      saved: "Saved in {file}", users_warning: "Changing this changes it for every unit that uses it ({n}).",
      shared_by: "Shared by {n}: {names}", change_for: "Change it for", only_unit: "only {name} (it gets its own copy)",
      all_units: "all {n} of them", no_via: "Open it from one of their pages to change it for that one only.",
      not_stable: "No stable address, so it can't be edited yet.", locked: "Ids and nation stay as they are.",
      edited: "edited", units_tab: "Units", maps_tab: "Maps",
      pick_map: "Pick a map to see its ground in 3D.", map_loading: "Loading the map…", detail_high: "Full detail",
      detail_low: "Light", water: "Water", scenery_building: "Buildings", scenery_prop: "Props", scenery_vegetation: "Trees",
      place_title: "Place on the map", place_on: "Place", place_turn: "Turn", place_pick: "Pick something to place first.",
      place_help: "Click the ground to place the picked object · right-drag to move · wheel to zoom",
      place_count: "{n} placed on this map by this mod",
      scenery_loading: "Reading what stands on the map…",
      scenery_stats: "{buildings} buildings · {props} of {props_total} props · {trees} of {trees_total} trees shown", map_help: "Drag to turn · right-drag to move · wheel to zoom",
      map_stats: "{points} points, {triangles} triangles",
      no_viewer: "The map view couldn't load its 3D library (it needs the internet the first time).",
      ground_loading: "Loading the real ground textures… {progress}", shape_ground: "Shape the ground",
      brush_hill: "Hill", brush_raise: "Raise", brush_lower: "Lower", brush_crater: "Crater", brush_plateau: "Plateau",
      brush_flatten: "Flatten", brush_level: "Level", scen_show: "Scenario", scen_start_what: "Starting point: a player's HQ and camera start here", scen_kind_word_buildings: "building", scen_kind_word_ground: "ground unit", scen_kind_word_infantry: "infantry", scen_kind_word_air: "aircraft", legend_start: "Pillars: starting points, where a player's HQ and camera start (colour: the team)", legend_spawn_icons: "Icons: what a scenario puts there at the start: house = building, tank = ground unit, soldier = infantry, plane = aircraft; the letters are its country, the colour its side", legend_neutral: "Grey: neutral, no side (like the map's supply depots)", maps_all: "All maps", tip_map_kind: "Show only the maps the game offers this way: skirmish, Operations, campaign, demo or test.", settings_tab: "Settings", tip_tab_settings: "Language, keys, the game folder and updates.", settings_title: "Settings", set_language_title: "Language", set_language_help: "Code names show the game's own names; any of the game's ten languages shows the names players know.", set_keys_title: "Map view keys", set_keys_help: "Click a key, then press the one you want.", set_game_title: "Game folder", set_game_path: "R.U.S.E. is in {path}.", set_game_none: "R.U.S.E. wasn't found. Pick its folder.", set_game_change: "Choose folder…", set_updates_title: "Updates", set_updates_latest: "This is RUSE Studio {version}. It looks for a newer one each time it opens.", set_updates_check: "Check now", set_updates_checking: "Looking for a newer version…", scen_kind_skirmish: "Battles", scen_kind_operation: "Operation", scen_kind_campaign: "Campaign", scen_kind_demo: "Demo", scen_kind_test: "Test setups", scen_kind_unused: "Not in any menu", tip_scen_show: "Show the scenario's zones, starting points (pillars in each alliance's colour) with the camera each match opens on, spawns (an icon for what each is, with its country's roundel) and town names.", tip_scen_pick: "The map's scenarios: the skirmish one first, then challenges and campaign chapters.", scen_main: "main", scen_none: "This map has no scenario.", scen_stats: "{zones} zones · {starts} starting points · {spawns} spawns · {names} names", scen_zone: "Zone", scen_start: "Starting point, alliance {n}", scen_spawn: "Spawn", tip_panel_grip: "Drag to move this panel. Double-click to put it back.", tip_panel_fold: "Fold this panel away.", tip_panel_unfold: "Open this panel again.", scen_where: "In the game: {where}", scen_players: "{n} players", tip_scen_where: "Start this in the game to see what you changed on this setup (after Test in game).", dock_roads: "Roads", tip_dock_roads: "Draw new roads: supply trucks follow them. Ends snap onto the roads they touch.", road_straight: "Straight", road_curve: "Curve", road_free: "Freeform", tip_road_straight: "A straight road: click where it starts, then where it ends.", tip_road_curve: "A curved road: click the start, then the bend it's pulled toward, then the end.", tip_road_free: "A road that follows your clicks: click along the way, then double-click or press Enter to finish.", road_help_straight: "Click where the road starts, then where it ends. An end near a road snaps onto it (a ring shows where).", road_help_curve: "Click the start, then the bend, then the end.", road_help_free: "Click along the road's way; double-click, press Enter or click Finish to end it. Esc drops it.", road_finish: "Finish", tip_road_finish: "End the road at its last point.", tip_road_undo: "Take back the last road (Ctrl+Z).", road_count: "{n} new road(s) on this map", scen_seat: "team {n}, place {p}", scen_start_tool: "Add starting point", tip_scen_start: "A new player's starting point: pick the team, then click the map. More players need one each.", scen_team_n: "Team {n}", tip_scen_team: "The team it's for: in a 4v4, teams 1 and 2 each need places 1 to 4.", scen_start_help: "Click the map where this team's next player starts (open ground, away from the others).", scen_start_place: "Starting point: team {n}, place {p}", scen_players_label: "Players", tip_scen_players: "How many players this map takes in this mod (up to 8). Each needs a starting point.", scen_players_game: "{n} (game)", scen_players_missing: "{n} players need a starting point at: {list} (scenario {where}). Add them with Add starting point.", scen_players_ok: "Every player has a starting point.", scen_players_none: "This map isn't played online, so its player count can't change.", road_part: "this part {len}", road_total: "{len} in all", road_note: "Supply trucks follow new roads, and they're painted on the ground (both proven in the game). A road over water gets a bridge.", roads_show: "Roads", tip_roads_show: "Show the map's roads in gold, on the ground as you shape it.", check_rename: "Rename to {name}", tip_check_rename: "Renames the map's folder in your mod to the pack name the game uses. Nothing inside it changes.", report_problem: "Report a problem", tip_report_problem: "Opens a bug report in your browser, with the app and its version filled in. You read it and post it yourself.", report: "Report", tip_report: "Report this as a bug: your browser opens a report with this message filled in (paths without your user name).", set_help_title: "Help & community", set_help_help: "The wiki is the field manual: a guide for every tool. Ask, suggest, show your mods or report a bug in Discussions.", help_wiki: "Wiki (field manual)", tip_help_wiki: "Opens the wiki in your browser: step-by-step guides for every tool.", help_discussions: "Discussions", tip_help_discussions: "Opens Discussions in your browser: questions, ideas, mods and maps.", check_title: "Mod check: {n} problem(s). The game build would stop here.", check_set_aside: "Set aside", tip_check_set_aside: "Rename the file <name>.broken.toml beside it: the build skips it, nothing is lost, and the map starts clean.", check_aside_done: "Set aside as {file}.", check_stop: "Fix the mod's problems first (the bar at the top).", scen_count_n: "How many: {n}", tip_scen_count: "How many one click adds, in the shape picked below.", formation_line: "Line", formation_column: "Column", formation_wedge: "Wedge", formation_box: "Box", formation_circle: "Circle", tip_scen_formation: "The shape they stand in. It faces up the screen, its middle where you click; the dots show where each goes.", tip_scen_gap: "How far apart they stand, in metres.", tip_maps_hide: "Fold the map list away: more room for the map.", tip_maps_show: "Show the map list again.", dock_terrain: "Ground", dock_movement: "Movement", tip_dock_terrain: "Hills, craters, plateaus, ramps: shape the ground.", tip_dock_water: "Lakes and rivers: flood the ground up to a level, or dry it up.", tip_dock_cover: "Where units hide: paint cover, take it away, or cover a whole town in one click.", tip_dock_movement: "Where units go: close ground to every unit, to infantry or to vehicles.", tip_dock_building: "Place the map's own buildings: one, an area, or a row.", tip_dock_prop: "Place the map's own objects: fences, crates, wrecks and the like.", tip_dock_vegetation: "Plant the map's own trees: one, a wood, or a tree line.", tip_dock_scenario: "The picked scenario: move starting points and spawns, or add units and buildings.", brush_block: "Block", brush_block_infantry: "Block infantry", brush_block_vehicles: "Block vehicles", tip_brush_block: "No unit can go here: they plan around it (a cliff, a lake, a wall). Proven in the game.", tip_brush_block_infantry: "Infantry can't go here; vehicles still can.", tip_brush_block_vehicles: "Vehicles can't go here; infantry still can (like a wood).", brush_open: "Open", brush_open_infantry: "Open to infantry", brush_open_vehicles: "Open to vehicles", tip_brush_open: "Every unit can go here, where the map kept them out (the reverse of Block). On water they stand on the bottom: the build warns.", tip_brush_open_infantry: "Infantry can go here, where the map kept them out; vehicles stay as they were.", tip_brush_open_vehicles: "Vehicles can go here, where the map kept them out (a wood they couldn't drive into); infantry stay as they were.", brush_forest: "Forest", tip_brush_forest: "Trees and cover in one stroke: trees scattered as Place's Area does (the tree picked there, else the map's most used), and cover under them so units hide. Undo takes back both.", forest_no_trees: "This map has no trees to place: a map takes only the kinds it already uses.", forest_done: "{n} trees, with cover under them.", move_show: "Where units go", tip_move_show: "Show where units can go: red is closed to every unit (water, cliffs, off the map), yellow to vehicles only (woods).", place_solid: "Solid", tip_place_solid: "Units can't go through the buildings you place (proven in the game). Off: they're only drawn.", brush_cover: "Cover", brush_uncover: "Uncover", brush_town: "Town", tip_brush_cover: "Paints cover: units there are hidden, as in a wood (green). Proven in the game.", tip_brush_uncover: "Takes cover away: units there can be seen, even in a wood.", tip_brush_town: "Click a town: cover goes around every building of it (Size: how far around each), so units hide in it.", cover_show: "Cover", tip_cover_show: "Show where units hide (green): the map's woods and towns, and what this mod paints.", town_none: "No building here: click on a town or a group of buildings.", town_done: "Cover around {n} buildings.", group_ap: "AP shells (anti-tank)", group_he: "HE shells (explosive)", group_aa: "Anti-aircraft", group_mg: "Machine guns", group_infantry_weapons: "Infantry weapons", group_antitank_weapons: "Infantry anti-tank", group_bombs: "Bombs", group_rockets: "Rockets", scen_move_tool: "Move", tip_scen_move: "Move a starting point or a spawn: click it, then click where it goes. Saved in the mod.", scen_spawn_tool: "Add unit", tip_scen_spawn: "Add a unit or building that appears when this scenario starts: pick its kind, type and name, pick a side, then click the map.", tip_scen_kind: "Buildings, ground units, infantry or planes.", tip_scen_unit: "The unit or building, listed by nation.", tip_scen_camp: "The side it belongs to. Which number is which player: test it in the game.", scen_side_neutral: "Neutral", tip_scen_camp_skirmish: "A skirmish game spawns only neutral items, like the map's depots: a unit for a player's side would never appear, so this scenario takes Neutral only.", scen_side_n: "Side {n}", scen_pick_item: "Click a starting point or a spawn to move it.", scen_pick_place: "Now click where it goes: {what}.", scen_remove: "Remove", scen_put_back: "Put back", scen_take_out: "Take out", scen_taken_out: "taken out", scen_take_out_depots: "Take out every depot", scen_take_out_names: "Take out every map name", tip_scen_take_out: "The match leaves the map's own item out (seen in the game: D-Day's depots and names gone). It stays in the map's files, so Put back brings it back.", scen_sectors_whole: "Sectors over the whole map", tip_scen_sectors_whole: "Every scenario of this map: each place its sectors leave out (the sea, the edges) goes to the sector nearest it, so all of the map can be taken. Seen in the game.", road_take_out_roads: "Take out the map's roads", tip_road_take_out_roads: "The map's own roads go: the road network supply trucks follow (they drive across country instead), the roads drawn from high up and on the map table, and the road stickers up close. Your new roads stay. Seen in the game: the roads go. Supply trucks driving across country aren't tried yet.", road_take_out_bridges: "Take out the map's bridges", tip_road_take_out_bridges: "The map's own bridges go, and the floors units stood on with them. Units still cross where they stood, on the ground under them: dry the rivers up (Water, Drain) to cross anywhere. Your new bridges stay. Not tested in the game yet.", water_whole: "Water over the whole map", tip_water_whole: "A thin layer of water over all of the map: its surface Strength above the ground's middle height, so lower ground is under water and higher ground stays dry. Units go under it (their movement takes it for dry ground), like the painted sea of a navy map. Undo takes it back. Seen in the game; units going under it aren't tried yet.", scen_spawn_help: "Click the map where it appears.", scen_pick_unit: "Pick a unit or building first.", scen_moved: "moved in this mod", scen_mine: "added in this mod", group_all: "All types", tip_group: "What it's for: a building's job (HQ, money, factory, fort, fake) or the factory that builds a unit.", group_hq: "HQ", group_money: "Money (depots, admin)", group_factory: "Factories", group_fort: "Forts and defenses", group_fake: "Fake (decoys)", group_barracks: "Barracks", group_armor: "Armor", group_antitank: "Anti-tank", group_artillery: "Artillery", group_prototype: "Prototypes", group_airfield: "Airfield", group_turret: "Fort guns", group_other: "Other", brush_water: "Water", brush_drain: "Drain", tip_brush_water: "Floods the ground below a water level: the height where you start dragging, plus Strength. The ground itself is unchanged.", tip_brush_drain: "Puts the water back to the map's base level: lakes and rivers there dry up.", tip_brush_level: "Paints the ground flat at one height: the height where you start dragging. Start on ground at the height you want.", brush_smooth: "Smooth", brush_size: "Size", brush_strength: "Strength",
      brush_look: "Look around", brush_undo: "Undo",
      brush_help: "Click or drag on the ground to paint · middle-drag to turn · right-drag to move · wheel to zoom",
      brush_count: "Strokes on this map: {n}", brush_note: "Saved in the mod. \"Test in game\" builds it into the map.",
      brush_ramp: "Ramp", ramp_help: "Click where the ramp starts, then where it ends. Esc cancels.",
      brush_shape_round: "Round", brush_shape_square: "Square", brush_shape_line: "Line",
      tip_brush_shape_round: "A round brush.",
      tip_brush_shape_square: "A square brush; the angle below turns it (a beach's line, a field's edge).",
      tip_brush_shape_line: "A line: click where it starts, then where it ends (a ridge, a ditch, a hedge of cover, a wall).",
      brush_edge_soft: "Soft edge", brush_edge_hard: "Hard edge",
      tip_brush_edge_soft: "The brush fades out toward its edge.",
      tip_brush_edge_hard: "Full strength nearly to the edge, then a short slope: crisp shapes.",
      brush_angle: "Angle {deg}°", brush_line_help: "Line: click where it starts, then where it ends. Esc cancels.",
      brush_line_next: "Now click where the line ends.",
      brush_clear: "Start over", really_clear: "Remove all {n} strokes on this map?", remove_all: "Remove them",
      all_values: "all {n}", each_value: "set each",
      price_dates: "One price per battle date: the host picks the date (1939, 1942, 1945, Total War) when setting up a battle.",
      new_unit: "New unit…", new_unit_name: "Name of the new unit (shown in every language)",
      price: "Price (every battle date)", build_menu: "Build menu", same_menu: "The same as {name}",
      other_menu: "Another one", nation: "Nation", factory: "Factory (shown by the units in it)",
      more_units: "and {n} more", copy_of: "A copy of {name}, made in this mod.", delete_unit: "Delete this unit",
      really_delete: "Delete {name}? Its changes go with it.", new_mark: "new",
      unit_made: "{name} is in the mod. Test in game to see it in its build menu.",
      unit_deleted: "{name} was deleted from the mod.",
      shot: "Muzzle flash and sound: {fx}. Picking another ammo takes the flash and sound of a weapon that fires it.", ammo: "Ammo", fired_by: "Fired by {names}", fired_by_nobody: "No unit fires it", weapons: "Weapons", models_loading: "Loading the game's 3D models… {progress}", weapon_n: "Weapon {n}",
      weapons_help: "Each weapon fires one ammo, which several units may share: change the ammo's numbers on its page for all of them, or copy it there for a weapon of this unit's own.",
      range: "Range", range_slider: "Range slider", range_metres: "about {m} m",
      tip_range: "How far this weapon shoots: the range of the ammo it fires.",
      tip_range_slider: "Drag to change how far it shoots; it's saved when you let go. For an exact number, type it in the box.",
      tip_range_box: "The range in the game's own units: about 260 make a metre. Type a number; it's saved when you press Enter or click away.",
      range_all: "all {n} units that fire this ammo",
      tip_range_only: "Only this unit's weapon gets the new range: the Studio makes this weapon its own copy of the ammo, and the other units keep theirs.",
      tip_range_all: "Every unit that fires this ammo gets the new range: {names}",
      range_own_copy: "This weapon fires its own copy of the ammo, so a change here is for this unit only.",
      tip_range_reset: "Put this ammo's range back to the game's.",
      dock_group_paint: "Map Paint", tip_dock_group_paint: "Paint the ground's picture with a colour or with the map's own ground, and erase trees and props.",
      dock_paint: "Paint", tip_dock_paint: "Paint the ground's picture: a colour, or the map's own ground copied from another spot. It changes how the ground looks, not its shape.",
      brush_paint: "Colour", tip_brush_paint: "Paint a colour on the ground: pick it on the wheel, from the map's own colours, or take it from the ground with the eyedropper.",
      brush_stamp: "Texture", tip_brush_stamp: "Paint with the map's own ground from another spot (grass, sand, rock, fields): pick the spot, then paint where it should go.",
      brush_opacity: "Opacity {n}%", tip_brush_opacity: "How much each dab covers the ground: low for a light tint, 100% to cover it. Going over a place again builds it up.",
      tip_paint_swatch_now: "The colour you paint with.", tip_paint_hex: "The colour as #rrggbb (red, green, blue in hex): type one and press Enter.",
      tip_paint_wheel: "Drag round the ring to pick the colour, and in the square to make it stronger or paler, lighter or darker.",
      paint_eyedropper: "Eyedropper", tip_paint_eyedropper: "Take a colour to match: press this, then click the ground, or a building, prop or tree to match its own colour (without the light on it). Alt+click with the Colour brush does the same.",
      paint_took_object: "Colour taken from {name}: {hex}",
      tip_paint_swatch: "Paint with this colour", paint_map_colours: "The map's own colours",
      tip_paint_map_colours: "The colours this map's ground is painted in most (grass, fields, sand, rock, roads), so new paint matches it.",
      paint_recent: "Recent", stamp_pick: "Pick the spot to copy from",
      tip_stamp_pick: "Press this, then click the ground the texture should come from (Alt+click does the same). Your first stroke after it sets the distance: the copy follows your brush.",
      stamp_pick_help: "Click the ground the texture should come from.",
      stamp_from: "Copying from the spot you picked: the second ring shows where. Pick again for another spot.",
      stamp_from_none: "Pick the spot to copy from first: press the button above, or Alt+click the ground.",
      stamp_picked: "Spot picked: now paint where its ground should go.", stamp_same: "That's the spot you copy from: paint somewhere else.",
      paint_note: "Shown here on the map's picture; the build paints every level of the game's ground tiles (seen in the game).", paint_clear: "Clear the ground under it", tip_paint_clear: "Up close the game draws the map's grass, crops, stones and ground stickers over its picture, so paint shows only from afar. With this on, the build takes those off where the paint is at least half strength, so it shows at every height (seen in the game). Trees, buildings, cover and movement stay.",
      paint_took: "Colour taken: {hex}", paint_pick_help: "Click the ground to take its colour.", paint_hex_bad: "A colour is # and six hex digits, like #8a7a4e.",
      fires: "What this weapon fires", open_ammo: "Open the ammo", copy_ammo: "Copy this ammo…",
      copy_name: "Name of the copy (only shown here)",
      copy_ammo_help: "The copy starts the same as the original and keeps its name in game. Change its numbers, then pick it for a weapon on the unit's page.",
      copy_made: "{name} is in the mod. Pick it for a weapon on a unit's page.", delete_copy: "Delete this copy",
      flag_add: "Add a flag…", flag_add_number: "Another number…", flag_remove: "Take this flag off",
      flag_used_by: "{n} units have it, e.g. {names}", flag_count: "{n} units",
      old_index: "The game index was made by an older Studio. Build it again (about a minute).",
      keys_head: "Keys: ", keys_move: "{k} or arrows move", keys_turn: "{k} turn", keys_zoom: "{k} zoom", keys_fast: "Shift faster", keys_brushes: "1-9 0 brushes", keys_brush: "{k} brush", keys_place: "{k} place", keys_look: "Esc look around", keys_undo: "Ctrl+Z undo", keys_size: "{k} size", keys_strength: "{k} strength or turn", keys_change: "Change keys…", tip_keys_change: "Pick your own keys for the map view.", keys_press: "Press a key…", keys_reset: "Defaults", keys_fixed: "Click a key and press another. The arrows, Esc, Ctrl+Z and the digits stay as they are.", key_forward: "Forward", key_back: "Back", key_left: "Left", key_right: "Right", key_turn_left: "Turn left", key_turn_right: "Turn right", key_zoom_in: "Zoom in", key_zoom_out: "Zoom out", key_brush: "Brush", key_place: "Place", key_size_down: "Smaller", key_size_up: "Bigger", key_strength_down: "Weaker, or turn left", key_strength_up: "Stronger, or turn right",
      scenery_note: "Placed trees and buildings give no cover by themselves: paint it with the Cover brush, or click a town with the Town brush. Buildings stop units (Solid).", undone: "Undone: {name} is back to what it was.",
      tip_tab_units: "Browse the game's units and change their numbers.",
      tip_tab_maps: "See a map's ground in 3D, shape it and place objects on it.",
      tip_mod: "The mod your changes are saved in.", tip_test: "Build the mod into a copy of the game and start it.",
      tip_lang: "The language of names and labels; Code names shows the game's own.",
      tip_update_now: "Download and install the newer release; the app opens again by itself.",
      tip_update_info: "Open the release notes in your browser.",
      tip_create_mod: "Make a new, empty mod and pick it.", tip_cancel: "Close this without changing anything.",
      tip_export: "Pack the mod into one file to share.", tip_close: "Hide the log.",
      tip_build_index: "Read the game's files once, so its units can be browsed (about a minute).",
      tip_search: "Filter the list by name. / focuses this box, Esc clears it, Up and Down walk the list.",
      tip_kind: "Show only this kind of unit.", tip_nation: "Show only this nation's units.",
      tip_open_unit: "Open this unit (Up and Down move through the list).",
      tip_copy_address: "Copy this unit's address to the clipboard.",
      tip_value: "Type a new value and press Enter or leave the box: it's saved in the mod at once.",
      tip_each_value: "Show one box per value, to change them one by one.",
      tip_reset: "Put the value back as the game has it (Ctrl+Z takes back the last change).",
      tip_change_for: "Whether a change here is for this unit only, or for every unit sharing this part.",
      tip_new_unit: "Make a copy of this unit with its own name, price and build menu.",
      unit_view: "3D model", unit_view_loading: "Making the 3D model… (a few seconds, the first time only)",
      unit_view_hint: "Drag to turn · scroll to zoom", unit_view_paint: "Showing your mod's paint.",
      card_frame: "Card", card_now: "The unit's card in the build menu now",
      card_note: "Its picture in the build menu. Turn and zoom the model until it looks right inside the dashed frame, then use this view.",
      card_use: "Use this view as the card", tip_card_use: "Takes what's inside the dashed frame, with your paint, as this unit's picture in the build menu.",
      card_reset: "Game's card", tip_card_reset: "Puts the game's own card for this unit back.",
      unit_look: "Repaint in Blender", tip_unit_look: "Open this unit's 3D model in Blender (a free 3D program), paint it there, and bring the paint back into your mod.",
      look_working: "Looking for its 3D model…", look_open: "Open in Blender", tip_look_open: "Opens Blender with this unit's model loaded and textured.",
      look_how: "Open in Blender and paint on the model. Then click Bring back: it saves your paint and puts it in your mod. Test in game shows it.",
      look_opening: "Opening in Blender…", look_back: "Bring back", tip_look_back: "Saves what you painted in Blender and puts it in your mod.",
      look_bringing: "Bringing the paint back…", look_no_blender: "Blender isn't found on this PC. It's free: get it, then show the Studio where blender.exe is.",
      look_get_blender: "Get Blender (free)", tip_look_get_blender: "Opens Blender's download page, blender.org.",
      look_choose_blender: "Choose Blender…", tip_look_choose_blender: "Pick blender.exe in Blender's folder; the Studio remembers it.",
      look_painted: "Your mod repaints {n} of this unit's pictures.",
      tip_unit_name: "The name players see, in every language.",
      tip_price: "What it costs to build, at every battle date.",
      tip_menu: "The build menu the new unit appears in.", tip_create_unit: "Add the new unit to the mod.",
      tip_delete_unit: "Take this unit out of the mod, with its changes.", tip_part: "Open this part.",
      tip_source: "Open the unit this one was copied from.", tip_open_map: "Show this map's ground in 3D ({file}).",
      tip_detail: "Switch between the light and the full mesh of the ground.", tip_water: "Show or hide the water.",
      tip_show_group: "Show or hide these on the map (only what is drawn changes).",
      tip_brush: "Shape the ground with this brush (key {n}).",
      tip_brush_size: "How wide a stroke is, as a share of the map ([ and ] keys).",
      tip_brush_strength: "How far a stroke moves the ground (- and = keys).",
      tip_look: "Stop painting or placing: drag then turns the view (Esc).",
      tip_brush_undo: "Take back the last stroke (Ctrl+Z).",
      tip_brush_clear: "Remove every stroke this mod makes on this map.", tip_remove_all: "Yes, remove them all.",
      tip_place_group: "Pick the kind of object to place.",
      tip_place_search: "Filter the list. A map can only take types it already uses.",
      tip_place_type: "The object to place; picking one turns placing on.",
      tip_place_turn: "How the object is turned, in degrees (- and = keys while placing).",
      tip_place_size: "How big the object is, compared with the game's ([ and ] keys while placing).",
      tip_place_on: "Place the picked object where you click the ground (P).",
      tip_place_undo: "Take the last placed object off the map (Ctrl+Z).",
      place_one: "One", place_area: "Area", place_line: "Line", tip_place_one: "Each click on the ground places one object.", tip_place_area: "Drag over the ground to fill an area: a wood, a village. Objects keep at least the spacing apart.", tip_place_line: "Click where the line starts, then where it ends: objects every spacing, turned along it (a hedgerow, a row of houses).", place_spacing: "Spacing {m} m", tip_place_spacing: "How far apart the objects of an area or a line are, for this kind of object.", place_area_size: "Area {m} m", tip_place_area_size: "The radius of the area brush: how wide a stroke fills.", place_area_help: "Drag over the ground to fill it with the object picked. Middle-drag turns the view, right-drag moves it.", place_line_help: "Click where the line starts, then where it ends. Esc drops a line half made.", place_line_next: "Now click where the line ends.", place_none_room: "No room here: everything within the spacing already has an object.", place_placed: "{n} objects placed and saved in the mod. Ctrl+Z takes them back in one go.", place_most: "That's the most one stroke can place; go again for more." },
    fr: { update_out: "{app} {version} est disponible.", update_now: "Mettre à jour", whats_new: "Nouveautés", update_progress: "Téléchargement de la mise à jour… {pct}", update_installing: "Installation : {app} se ferme puis se rouvre automatiquement.", update_repo: "(Cette copie s'exécute depuis le dépôt Git : mettez-la à jour avec git pull.)", update_failed: "La mise à jour n'a pas fonctionné : {why}",
      language: "Langue", game_names: "Noms internes", search: "Rechercher", all: "Tous", ground: "Terrestre",
      infantry: "Infanterie", air: "Aérien", buildings: "Bâtiments", units: "{n} unités", parts: "Composants",
      uses: "Utilise", own_part: "le sien", shared_part: "partagé avec d'autres unités", used_by: "Utilisé par",
      copy_address: "Copier l'adresse", no_index: "Pas encore d'index du jeu.", build_index: "Construire l'index",
      pick_unit: "Choisissez une unité à gauche.", mod: "Mod", new_mod: "Nouveau mod…",
      export_mod: "Exporter le mod…", version: "Version", author: "Auteur", description: "Description", export: "Exporter",
      export_help: "Un seul fichier à partager : le dossier du mod empaqueté. La version, l'auteur et la description restent dans le mod.",
      open_folder: "Ouvrir un dossier de mod…", mod_name: "Nom du nouveau mod", create: "Créer", cancel: "Annuler",
      close: "Fermer", no_mod: "Choisissez ou créez un mod pour enregistrer les modifications.",
      test_in_game: "Tester en jeu", was: "avant : {v}", reset: "Annuler", saved: "Enregistré dans {file}",
      users_warning: "Le modifier le change pour toutes les unités qui l'utilisent ({n}).",
      shared_by: "Partagé par {n} : {names}", change_for: "Modifier pour",
      only_unit: "seulement {name} (il reçoit sa propre copie)", all_units: "les {n}",
      no_via: "Ouvrez-le depuis la page de l'un d'eux pour ne modifier que celui-là.",
      not_stable: "Pas d'adresse stable : pas encore modifiable.",
      locked: "Les identifiants et la nation restent tels quels.", edited: "modifié", units_tab: "Unités",
      maps_tab: "Cartes", pick_map: "Choisissez une carte pour voir son terrain en 3D.",
      map_loading: "Chargement de la carte…", detail_high: "Détail complet", detail_low: "Allégé", water: "Eau", scenery_building: "Bâtiments", scenery_prop: "Objets", scenery_vegetation: "Arbres",
      place_title: "Placer sur la carte", place_on: "Placer", place_turn: "Rotation", place_pick: "Choisissez d'abord quoi placer.",
      place_help: "Cliquez sur le sol pour placer l'objet choisi · clic droit glissé pour déplacer · molette pour zoomer",
      place_count: "{n} placés sur cette carte par ce mod",
      scenery_loading: "Lecture de ce qui se trouve sur la carte…",
      scenery_stats: "{buildings} bâtiments · {props} objets sur {props_total} · {trees} arbres sur {trees_total} affichés",
      map_help: "Glisser pour tourner · clic droit pour déplacer · molette pour zoomer",
      map_stats: "{points} points, {triangles} triangles",
      no_viewer: "La vue de carte n'a pas pu charger sa bibliothèque 3D (il faut Internet la première fois).",
      ground_loading: "Chargement des vraies textures du sol… {progress}", shape_ground: "Modeler le terrain",
      brush_hill: "Colline", brush_raise: "Surélever", brush_lower: "Abaisser", brush_crater: "Cratère",
      brush_plateau: "Plateau", brush_flatten: "Aplanir", brush_level: "Niveler", scen_show: "Scénario", maps_all: "Toutes les cartes", tip_map_kind: "Afficher seulement les cartes que le jeu propose ainsi : escarmouche, opérations, campagne, démo ou test.", settings_tab: "Réglages", tip_tab_settings: "Langue, touches, dossier du jeu et mises à jour.", settings_title: "Réglages", set_language_title: "Langue", set_language_help: "Les noms de code montrent les noms internes du jeu ; chacune des dix langues montre les noms que voient les joueurs.", set_keys_title: "Touches de la vue carte", set_keys_help: "Cliquez sur une touche, puis appuyez sur celle que vous voulez.", set_game_title: "Dossier du jeu", set_game_path: "R.U.S.E. est dans {path}.", set_game_none: "R.U.S.E. est introuvable. Choisissez son dossier.", set_game_change: "Choisir le dossier…", set_updates_title: "Mises à jour", set_updates_latest: "Ceci est RUSE Studio {version}. Il cherche une version plus récente à chaque ouverture.", set_updates_check: "Vérifier", set_updates_checking: "Recherche d'une version plus récente…", scen_kind_skirmish: "Batailles", scen_kind_operation: "Opération", scen_kind_campaign: "Campagne", scen_kind_demo: "Démo", scen_kind_test: "Réglages de test", scen_kind_unused: "Dans aucun menu", tip_scen_show: "Afficher les zones du scénario, les points de départ (piliers à la couleur de chaque alliance) avec la caméra d'ouverture de la partie, les apparitions (une icône pour chacune, avec la cocarde de son pays) et les noms de villes.", tip_scen_pick: "Les scénarios de la carte : l'escarmouche d'abord, puis les défis et les chapitres de campagne.", scen_main: "principal", scen_none: "Cette carte n'a pas de scénario.", scen_stats: "{zones} zones · {starts} points de départ · {spawns} apparitions · {names} noms", scen_zone: "Zone", scen_start: "Point de départ, alliance {n}", scen_spawn: "Apparition", tip_panel_grip: "Glissez pour déplacer ce panneau. Double-cliquez pour le remettre en place.", tip_panel_fold: "Replier ce panneau.", tip_panel_unfold: "Rouvrir ce panneau.", scen_where: "En jeu : {where}", scen_players: "{n} joueurs", tip_scen_where: "Lancez ceci en jeu pour voir vos changements sur cette configuration (après Tester en jeu).", dock_roads: "Routes", tip_dock_roads: "Tracez de nouvelles routes : les camions de ravitaillement les suivent. Les extrémités s'accrochent aux routes touchées.", road_straight: "Droite", road_curve: "Courbe", road_free: "Libre", tip_road_straight: "Une route droite : cliquez là où elle commence, puis là où elle finit.", tip_road_curve: "Une route courbe : cliquez le début, puis le point vers lequel elle se courbe, puis la fin.", tip_road_free: "Une route qui suit vos clics : cliquez le long du tracé, puis double-cliquez ou appuyez sur Entrée.", road_help_straight: "Cliquez là où la route commence, puis là où elle finit. Une extrémité près d'une route s'y accroche (un cercle le montre).", road_help_curve: "Cliquez le début, puis la courbe, puis la fin.", road_help_free: "Cliquez le long du tracé ; double-cliquez, Entrée ou Terminer pour finir. Échap l'annule.", road_finish: "Terminer", tip_road_finish: "Terminer la route à son dernier point.", tip_road_undo: "Retirer la dernière route (Ctrl+Z).", road_count: "{n} nouvelle(s) route(s) sur cette carte", scen_seat: "équipe {n}, place {p}", scen_start_tool: "Ajouter un point de départ", tip_scen_start: "Un nouveau point de départ de joueur : choisissez l'équipe, puis cliquez sur la carte. Plus de joueurs en demandent un chacun.", scen_team_n: "Équipe {n}", tip_scen_team: "L'équipe concernée : en 4c4, les équipes 1 et 2 ont chacune besoin des places 1 à 4.", scen_start_help: "Cliquez sur la carte là où commence le prochain joueur de cette équipe (terrain dégagé, loin des autres).", scen_start_place: "Point de départ : équipe {n}, place {p}", scen_players_label: "Joueurs", tip_scen_players: "Combien de joueurs cette carte accepte dans ce mod (jusqu'à 8). Chacun a besoin d'un point de départ.", scen_players_game: "{n} (jeu)", scen_players_missing: "{n} joueurs demandent un point de départ : {list} (scénario {where}). Ajoutez-les avec Ajouter un point de départ.", scen_players_ok: "Chaque joueur a un point de départ.", scen_players_none: "Cette carte ne se joue pas en ligne : son nombre de joueurs ne peut pas changer.", road_part: "cette partie {len}", road_total: "{len} au total", road_note: "Les camions de ravitaillement suivent les nouvelles routes, peintes au sol (vérifié en jeu). Une route sur l'eau reçoit un pont.", roads_show: "Routes", tip_roads_show: "Afficher les routes de la carte en doré, sur le terrain que vous modelez.", check_rename: "Renommer en {name}", tip_check_rename: "Renomme le dossier de la carte dans votre mod avec le nom de pack du jeu. Rien à l'intérieur ne change.", report_problem: "Signaler un problème", tip_report_problem: "Ouvre un rapport de bug dans votre navigateur, avec l'application et sa version déjà remplies. Vous le relisez et le publiez vous-même.", report: "Signaler", tip_report: "Signaler ce bug : le navigateur ouvre un rapport avec ce message (chemins sans votre nom d'utilisateur).", set_help_title: "Aide et communauté", set_help_help: "Le wiki est le manuel : un guide pour chaque outil. Questions, idées, mods et bugs vont dans les Discussions.", help_wiki: "Wiki (manuel)", tip_help_wiki: "Ouvre le wiki dans le navigateur : des guides pas à pas pour chaque outil.", help_discussions: "Discussions", tip_help_discussions: "Ouvre les Discussions dans le navigateur : questions, idées, mods et cartes.", check_title: "Vérification du mod : {n} problème(s). La construction pour le jeu s'arrêterait ici.", check_set_aside: "Mettre de côté", tip_check_set_aside: "Renomme le fichier en <nom>.broken.toml à côté : la construction l'ignore, rien n'est perdu, la carte repart à zéro.", check_aside_done: "Mis de côté : {file}.", check_stop: "Corrigez d'abord les problèmes du mod (la barre en haut).", scen_count_n: "Combien : {n}", tip_scen_count: "Combien un clic en ajoute, dans la forme choisie dessous.", formation_line: "Ligne", formation_column: "Colonne", formation_wedge: "Coin", formation_box: "Carré", formation_circle: "Cercle", tip_scen_formation: "La forme dans laquelle ils se placent. Elle fait face au haut de l'écran, son centre là où vous cliquez ; les ronds montrent où va chacun.", tip_scen_gap: "L'écart entre eux, en mètres.", tip_maps_hide: "Replier la liste des cartes : plus de place pour la carte.", tip_maps_show: "Afficher à nouveau la liste des cartes.", dock_terrain: "Terrain", dock_movement: "Mouvement", tip_dock_terrain: "Collines, cratères, plateaux, rampes : modelez le terrain.", tip_dock_water: "Lacs et rivières : inondez jusqu'à un niveau, ou asséchez.", tip_dock_cover: "Où les unités se cachent : peignez du couvert, retirez-le, ou couvrez une ville en un clic.", tip_dock_movement: "Où vont les unités : fermez le terrain à toutes, à l'infanterie ou aux véhicules.", tip_dock_building: "Posez les bâtiments de la carte : un seul, une zone ou une rangée.", tip_dock_prop: "Posez les objets de la carte : clôtures, caisses, épaves, etc.", tip_dock_vegetation: "Plantez les arbres de la carte : un seul, un bois ou une rangée.", tip_dock_scenario: "Le scénario choisi : déplacez points de départ et apparitions, ou ajoutez unités et bâtiments.", brush_block: "Bloquer", brush_block_infantry: "Bloquer l'infanterie", brush_block_vehicles: "Bloquer les véhicules", tip_brush_block: "Aucune unité ne passe ici : elles contournent (falaise, lac, mur). Vérifié en jeu.", tip_brush_block_infantry: "L'infanterie ne passe pas ici ; les véhicules si.", tip_brush_block_vehicles: "Les véhicules ne passent pas ici ; l'infanterie si (comme un bois).", brush_open: "Ouvrir", brush_open_infantry: "Ouvrir à l'infanterie", brush_open_vehicles: "Ouvrir aux véhicules", tip_brush_open: "Toutes les unités passent ici, là où la carte les en empêchait (l'inverse de Bloquer). Sur l'eau, elles marchent au fond : la construction prévient.", tip_brush_open_infantry: "L'infanterie passe ici, là où la carte l'en empêchait ; les véhicules ne changent pas.", tip_brush_open_vehicles: "Les véhicules passent ici, là où la carte les en empêchait (un bois infranchissable) ; l'infanterie ne change pas.", brush_forest: "Forêt", tip_brush_forest: "Arbres et couvert d'un seul trait : des arbres semés comme avec Zone de Placer (l'arbre choisi là, sinon le plus courant de la carte), et du couvert dessous pour cacher les unités. Annuler retire les deux.", forest_no_trees: "Cette carte n'a aucun arbre à placer : une carte n'accepte que les types qu'elle utilise déjà.", forest_done: "{n} arbres, avec du couvert dessous.", move_show: "Où vont les unités", tip_move_show: "Afficher où les unités peuvent aller : rouge = fermé à toutes (eau, falaises, hors carte), jaune = fermé aux véhicules (bois).", place_solid: "Solide", tip_place_solid: "Les unités ne traversent pas les bâtiments posés (vérifié en jeu). Désactivé : ils ne sont que dessinés.", brush_cover: "Couvert", brush_uncover: "Découvrir", brush_town: "Ville", tip_brush_cover: "Peint du couvert : les unités y sont cachées, comme dans un bois (en vert). Vérifié en jeu.", tip_brush_uncover: "Retire le couvert : les unités y sont visibles, même dans un bois.", tip_brush_town: "Cliquez sur une ville : du couvert est posé autour de chacun de ses bâtiments (Taille : jusqu'où), pour y cacher les unités.", cover_show: "Couvert", tip_cover_show: "Afficher où les unités se cachent (en vert) : bois et villes de la carte, et ce que peint ce mod.", town_none: "Pas de bâtiment ici : cliquez sur une ville ou un groupe de bâtiments.", town_done: "Couvert autour de {n} bâtiments.", group_ap: "Obus perforants (antichar)", group_he: "Obus explosifs", group_aa: "Antiaérien", group_mg: "Mitrailleuses", group_infantry_weapons: "Armes d'infanterie", group_antitank_weapons: "Antichar d'infanterie", group_bombs: "Bombes", group_rockets: "Roquettes", scen_move_tool: "Déplacer", tip_scen_move: "Déplacer un point de départ ou une apparition : cliquez dessus, puis là où il va. Enregistré dans le mod.", scen_spawn_tool: "Ajouter une unité", tip_scen_spawn: "Ajouter une unité ou un bâtiment qui apparaît au début de ce scénario : choisissez sa catégorie, son type et son nom, un camp, puis cliquez sur la carte.", tip_scen_kind: "Bâtiments, unités terrestres, infanterie ou avions.", tip_scen_unit: "L'unité ou le bâtiment, par nation.", tip_scen_camp: "Le camp auquel il appartient. Quel numéro correspond à quel joueur : testez dans le jeu.", scen_side_neutral: "Neutre", tip_scen_camp_skirmish: "Une partie en escarmouche ne fait apparaître que des éléments neutres, comme les dépôts de la carte : une unité pour le camp d'un joueur n'apparaîtrait jamais, ce scénario ne prend donc que Neutre.", scen_side_n: "Camp {n}", scen_pick_item: "Cliquez sur un point de départ ou une apparition à déplacer.", scen_pick_place: "Cliquez maintenant là où il va : {what}.", scen_remove: "Retirer", scen_put_back: "Remettre", scen_take_out: "Retirer", scen_taken_out: "retiré", scen_take_out_depots: "Retirer tous les dépôts", scen_take_out_names: "Retirer tous les noms de la carte", tip_scen_take_out: "La partie laisse de côté cet élément de la carte (vu en jeu : les dépôts et les noms du Jour J disparus). Il reste dans les fichiers de la carte, Remettre le fait revenir.", scen_sectors_whole: "Secteurs sur toute la carte", tip_scen_sectors_whole: "Tous les scénarios de cette carte : chaque endroit hors des secteurs (la mer, les bords) rejoint le secteur le plus proche, toute la carte peut être prise. Vérifié en jeu.", road_take_out_roads: "Retirer les routes de la carte", tip_road_take_out_roads: "Les routes de la carte disparaissent : le réseau que suivent les camions de ravitaillement (ils roulent à travers champs), les routes vues de haut et sur la table, et les autocollants de route de près. Vos nouvelles routes restent. Vérifié en jeu : les routes disparaissent. Les camions qui roulent à travers champs ne sont pas encore essayés.", road_take_out_bridges: "Retirer les ponts de la carte", tip_road_take_out_bridges: "Les ponts de la carte disparaissent, avec les sols où se tenaient les unités. Les unités traversent encore à leur place, sur le sol en dessous : asséchez les rivières (Eau, Assécher) pour traverser partout. Vos nouveaux ponts restent. Pas encore testé en jeu.", water_whole: "Eau sur toute la carte", tip_water_whole: "Une fine couche d'eau sur toute la carte : sa surface à Force au-dessus de la hauteur moyenne du sol, le sol plus bas sous l'eau, le plus haut au sec. Les unités passent dessous (leurs déplacements la prennent pour du sol sec), comme la mer peinte d'une carte navale. Annuler la retire. Vérifié en jeu ; le passage des unités dessous n'est pas encore essayé.", scen_spawn_help: "Cliquez sur la carte là où il apparaît.", scen_pick_unit: "Choisissez d'abord une unité ou un bâtiment.", scen_moved: "déplacé dans ce mod", scen_mine: "ajouté dans ce mod", group_all: "Tous les types", tip_group: "À quoi il sert : le rôle d'un bâtiment (QG, argent, usine, fort, factice) ou l'usine qui produit une unité.", group_hq: "QG", group_money: "Argent (dépôts, administration)", group_factory: "Usines", group_fort: "Forts et défenses", group_fake: "Factices (leurres)", group_barracks: "Caserne", group_armor: "Blindés", group_antitank: "Antichar", group_artillery: "Artillerie", group_prototype: "Prototypes", group_airfield: "Aérodrome", group_turret: "Canons de fort", group_other: "Autres", brush_water: "Eau", brush_drain: "Assécher", tip_brush_water: "Inonde le sol sous un niveau d'eau : la hauteur où vous commencez à glisser, plus la force. Le sol lui-même ne change pas.", tip_brush_drain: "Remet l'eau au niveau de base de la carte : les lacs et rivières s'y assèchent.", tip_brush_level: "Peint le terrain à plat à une hauteur : celle où vous commencez à glisser. Commencez sur un terrain à la hauteur voulue.", brush_smooth: "Adoucir", brush_size: "Taille",
      brush_strength: "Force", brush_look: "Regarder", brush_undo: "Annuler",
      brush_help: "Cliquez ou glissez sur le sol pour peindre · glisser du milieu pour tourner · clic droit pour déplacer · molette pour zoomer",
      brush_count: "Coups de pinceau sur cette carte : {n}",
      brush_note: "Enregistré dans le mod. « Tester en jeu » l'intègre à la carte.", brush_ramp: "Rampe",
      ramp_help: "Cliquez au début de la rampe, puis à sa fin. Échap annule.", brush_clear: "Tout effacer",
      really_clear: "Supprimer les {n} coups de pinceau de cette carte ?", remove_all: "Les supprimer",
      all_values: "les {n}", each_value: "régler chacun",
      price_dates: "Un prix par date de bataille : l'hôte choisit la date (1939, 1942, 1945, Guerre totale) en préparant la partie.",
      new_unit: "Nouvelle unité…", new_unit_name: "Nom de la nouvelle unité (affiché dans toutes les langues)",
      price: "Prix (à chaque date de bataille)", build_menu: "Menu de production", same_menu: "Le même que {name}",
      other_menu: "Un autre", nation: "Nation", factory: "Usine (indiquée par ses unités)", more_units: "et {n} autres",
      copy_of: "Une copie de {name}, créée dans ce mod.", delete_unit: "Supprimer cette unité",
      really_delete: "Supprimer {name} ? Ses modifications disparaissent aussi.", new_mark: "nouveau",
      unit_made: "{name} est dans le mod. Testez en jeu pour le voir dans son menu de production.",
      unit_deleted: "{name} a été supprimé du mod.",
      shot: "Éclair et son du tir : {fx}. Choisir une autre munition prend l'éclair et le son d'une arme qui la tire.", ammo: "Munitions", fired_by: "Tirée par {names}", fired_by_nobody: "Aucune unité ne la tire", weapons: "Armes", models_loading: "Chargement des modèles 3D du jeu… {progress}", weapon_n: "Arme {n}",
      weapons_help: "Chaque arme tire une munition, que plusieurs unités peuvent partager : changez ses valeurs sur sa page pour toutes, ou copiez-la là pour une arme propre à cette unité.",
      range: "Portée", range_slider: "Curseur de portée", range_metres: "environ {m} m",
      tip_range: "Jusqu'où tire cette arme : la portée de la munition qu'elle tire.",
      tip_range_slider: "Faites glisser pour changer la portée ; c'est enregistré quand vous relâchez. Pour un nombre exact, tapez-le dans la case.",
      tip_range_box: "La portée en unités du jeu : environ 260 font un mètre. Tapez un nombre ; c'est enregistré avec Entrée ou en cliquant ailleurs.",
      range_all: "les {n} unités qui tirent cette munition",
      tip_range_only: "Seule l'arme de cette unité change de portée : le Studio lui fait sa propre copie de la munition, les autres unités gardent la leur.",
      tip_range_all: "Toutes les unités qui tirent cette munition changent de portée : {names}",
      range_own_copy: "Cette arme tire sa propre copie de la munition : un changement ici ne vaut que pour cette unité.",
      tip_range_reset: "Remettre la portée de cette munition comme dans le jeu.",
      dock_group_paint: "Peinture de carte", tip_dock_group_paint: "Peindre l'image du sol avec une couleur ou avec le sol de la carte elle-même, et effacer arbres et objets.",
      dock_paint: "Peindre", tip_dock_paint: "Peindre l'image du sol : une couleur, ou le sol de la carte copié depuis un autre endroit. Cela change l'aspect du sol, pas sa forme.",
      brush_paint: "Couleur", tip_brush_paint: "Peindre une couleur sur le sol : choisissez-la sur la roue, parmi les couleurs de la carte, ou prenez-la sur le sol avec la pipette.",
      brush_stamp: "Texture", tip_brush_stamp: "Peindre avec le sol de la carte pris à un autre endroit (herbe, sable, roche, champs) : choisissez l'endroit, puis peignez là où il doit aller.",
      brush_opacity: "Opacité {n} %", tip_brush_opacity: "À quel point chaque touche couvre le sol : faible pour une légère teinte, 100 % pour le couvrir. Repasser au même endroit renforce l'effet.",
      tip_paint_swatch_now: "La couleur avec laquelle vous peignez.", tip_paint_hex: "La couleur au format #rrvvbb (rouge, vert, bleu en hexadécimal) : tapez-en une et appuyez sur Entrée.",
      tip_paint_wheel: "Faites glisser sur l'anneau pour choisir la couleur, et dans le carré pour la rendre plus vive ou plus pâle, plus claire ou plus sombre.",
      paint_eyedropper: "Pipette", tip_paint_eyedropper: "Prendre une couleur à assortir : appuyez ici, puis cliquez sur le sol, ou sur un bâtiment, un objet ou un arbre pour reprendre sa propre couleur (sans la lumière). Alt+clic avec le pinceau Couleur fait de même.",
      paint_took_object: "Couleur prise sur {name} : {hex}",
      tip_paint_swatch: "Peindre avec cette couleur", paint_map_colours: "Les couleurs de la carte",
      tip_paint_map_colours: "Les couleurs les plus présentes sur le sol de cette carte (herbe, champs, sable, roche, routes), pour que la peinture s'y accorde.",
      paint_recent: "Récentes", stamp_pick: "Choisir l'endroit à copier",
      tip_stamp_pick: "Appuyez ici, puis cliquez sur le sol d'où doit venir la texture (Alt+clic fait de même). Votre premier coup de pinceau fixe la distance : la copie suit le pinceau.",
      stamp_pick_help: "Cliquez sur le sol d'où doit venir la texture.",
      stamp_from: "Copie depuis l'endroit choisi : le second anneau montre où. Choisissez à nouveau pour un autre endroit.",
      stamp_from_none: "Choisissez d'abord l'endroit à copier : appuyez sur le bouton ci-dessus, ou Alt+clic sur le sol.",
      stamp_picked: "Endroit choisi : peignez maintenant là où son sol doit aller.", stamp_same: "C'est l'endroit que vous copiez : peignez ailleurs.",
      paint_note: "Montré ici sur l'image de la carte ; la compilation peint chaque niveau des tuiles de sol du jeu (vérifié en jeu).", paint_clear: "Dégager le sol dessous", tip_paint_clear: "De près, le jeu dessine l'herbe, les cultures, les pierres et les autocollants de sol de la carte par-dessus son image : la peinture ne se voit alors que de loin. Activé, la compilation les retire là où la peinture est au moins à moitié de sa force, pour qu'elle se voie à toute hauteur (vérifié en jeu). Arbres, bâtiments, couvert et déplacement restent.",
      paint_took: "Couleur prise : {hex}", paint_pick_help: "Cliquez sur le sol pour prendre sa couleur.", paint_hex_bad: "Une couleur s'écrit # suivi de six chiffres hexadécimaux, comme #8a7a4e.",
      fires: "Ce que tire cette arme", open_ammo: "Ouvrir la munition", copy_ammo: "Copier cette munition…",
      copy_name: "Nom de la copie (affiché ici seulement)",
      copy_ammo_help: "La copie part identique à l'originale et garde son nom en jeu. Changez ses valeurs, puis choisissez-la pour une arme sur la page de l'unité.",
      copy_made: "{name} est dans le mod. Choisissez-la pour une arme sur la page d'une unité.", delete_copy: "Supprimer cette copie",
      flag_add: "Ajouter un drapeau…", flag_add_number: "Un autre numéro…", flag_remove: "Retirer ce drapeau",
      flag_used_by: "{n} unités l'ont, p. ex. {names}", flag_count: "{n} unités",
      old_index: "L'index du jeu vient d'un Studio plus ancien. Reconstruisez-le (environ une minute).",
      keys_head: "Touches : ", keys_move: "{k} ou flèches pour déplacer", keys_turn: "{k} tourner", keys_zoom: "{k} zoom", keys_fast: "Maj plus vite", keys_brushes: "1-9 0 pinceaux", keys_brush: "{k} pinceau", keys_place: "{k} placer", keys_look: "Échap regarder", keys_undo: "Ctrl+Z annuler", keys_size: "{k} taille", keys_strength: "{k} force ou rotation", keys_change: "Changer les touches…", tip_keys_change: "Choisissez vos propres touches pour la vue carte.", keys_press: "Appuyez sur une touche…", keys_reset: "Par défaut", keys_fixed: "Cliquez sur une touche et appuyez sur une autre. Les flèches, Échap, Ctrl+Z et les chiffres ne changent pas.", key_forward: "Avancer", key_back: "Reculer", key_left: "Gauche", key_right: "Droite", key_turn_left: "Tourner à gauche", key_turn_right: "Tourner à droite", key_zoom_in: "Zoom avant", key_zoom_out: "Zoom arrière", key_brush: "Pinceau", key_place: "Placer", key_size_down: "Plus petit", key_size_up: "Plus grand", key_strength_down: "Moins fort, ou tourner à gauche", key_strength_up: "Plus fort, ou tourner à droite",
      scenery_note: "Les arbres et bâtiments posés n'offrent pas de couvert d'eux-mêmes : peignez-le avec le pinceau Couvert, ou cliquez sur une ville avec le pinceau Ville. Les bâtiments arrêtent les unités (Solide).", undone: "Annulé : {name} est revenu à sa valeur précédente.",
      tip_tab_units: "Parcourir les unités du jeu et modifier leurs valeurs.",
      tip_tab_maps: "Voir le terrain d'une carte en 3D, le modeler et y placer des objets.",
      tip_mod: "Le mod dans lequel vos modifications sont enregistrées.",
      tip_test: "Intégrer le mod dans une copie du jeu et la lancer.",
      tip_lang: "La langue des noms et des libellés ; Noms internes affiche ceux du jeu.",
      tip_update_now: "Télécharger et installer la nouvelle version ; l'application se rouvre toute seule.",
      tip_update_info: "Ouvrir les notes de version dans votre navigateur.",
      tip_create_mod: "Créer un nouveau mod vide et le sélectionner.", tip_cancel: "Fermer sans rien changer.",
      tip_export: "Empaqueter le mod en un seul fichier à partager.", tip_close: "Masquer le journal.",
      tip_build_index: "Lire une fois les fichiers du jeu pour pouvoir parcourir ses unités (environ une minute).",
      tip_search: "Filtrer la liste par nom. / place le curseur ici, Échap efface, Haut et Bas parcourent la liste.",
      tip_kind: "N'afficher que ce type d'unité.", tip_nation: "N'afficher que les unités de cette nation.",
      tip_open_unit: "Ouvrir cette unité (Haut et Bas parcourent la liste).",
      tip_copy_address: "Copier l'adresse de cette unité dans le presse-papiers.",
      tip_value: "Saisissez une nouvelle valeur puis Entrée ou quittez la case : elle est enregistrée aussitôt dans le mod.",
      tip_each_value: "Afficher une case par valeur, pour les modifier une à une.",
      tip_reset: "Remettre la valeur du jeu (Ctrl+Z annule la dernière modification).",
      tip_change_for: "Si une modification ici vaut pour cette unité seule ou pour toutes celles qui partagent ce composant.",
      tip_new_unit: "Créer une copie de cette unité avec son propre nom, prix et menu de production.",
      tip_unit_name: "Le nom que voient les joueurs, dans toutes les langues.",
      tip_price: "Son coût de production, à chaque date de bataille.",
      tip_menu: "Le menu de production où apparaît la nouvelle unité.",
      tip_create_unit: "Ajouter la nouvelle unité au mod.",
      tip_delete_unit: "Retirer cette unité du mod, avec ses modifications.", tip_part: "Ouvrir ce composant.",
      tip_source: "Ouvrir l'unité dont celle-ci est la copie.",
      tip_open_map: "Afficher le terrain de cette carte en 3D ({file}).",
      tip_detail: "Basculer entre le maillage allégé et le maillage complet du terrain.",
      tip_water: "Afficher ou masquer l'eau.",
      tip_show_group: "Afficher ou masquer ces objets sur la carte (seul l'affichage change).",
      tip_brush: "Modeler le terrain avec ce pinceau (touche {n}).",
      tip_brush_size: "La largeur d'un coup de pinceau, en part de la carte (touches [ et ]).",
      tip_brush_strength: "De combien un coup de pinceau déplace le terrain (touches - et =).",
      tip_look: "Arrêter de peindre ou de placer : glisser tourne alors la vue (Échap).",
      tip_brush_undo: "Annuler le dernier coup de pinceau (Ctrl+Z).",
      tip_brush_clear: "Supprimer tous les coups de pinceau de ce mod sur cette carte.",
      tip_remove_all: "Oui, tout supprimer.", tip_place_group: "Choisir le type d'objet à placer.",
      tip_place_search: "Filtrer la liste. Une carte ne peut recevoir que des types qu'elle utilise déjà.",
      tip_place_type: "L'objet à placer ; en choisir un active le placement.",
      tip_place_turn: "L'orientation de l'objet, en degrés (touches - et = pendant le placement).",
      tip_place_size: "La taille de l'objet par rapport à celle du jeu (touches [ et ] pendant le placement).",
      tip_place_on: "Placer l'objet choisi là où vous cliquez sur le sol (P).",
      tip_place_undo: "Retirer de la carte le dernier objet placé (Ctrl+Z).",
      place_one: "Un", place_area: "Zone", place_line: "Ligne", tip_place_one: "Chaque clic sur le sol place un objet.", tip_place_area: "Glissez sur le sol pour remplir une zone : un bois, un village. Les objets restent espacés d'au moins l'écart choisi.", tip_place_line: "Cliquez où commence la ligne, puis où elle finit : un objet à chaque écart, tourné dans son sens (une haie, une rangée de maisons).", place_spacing: "Écart {m} m", tip_place_spacing: "La distance entre les objets d'une zone ou d'une ligne, pour ce type d'objet.", place_area_size: "Zone {m} m", tip_place_area_size: "Le rayon du pinceau de zone : la largeur que remplit un trait.", place_area_help: "Glissez sur le sol pour le remplir avec l'objet choisi. Glisser avec le bouton du milieu tourne la vue, avec le droit la déplace.", place_line_help: "Cliquez où commence la ligne, puis où elle finit. Échap abandonne une ligne commencée.", place_line_next: "Cliquez maintenant où la ligne finit.", place_none_room: "Pas de place ici : tout ce qui est à moins de l'écart a déjà un objet.", place_placed: "{n} objets placés et enregistrés dans le mod. Ctrl+Z les retire d'un coup.", place_most: "C'est le maximum pour un trait ; recommencez pour en mettre plus." },
    sc: { update_out: "{app} {version} 已发布。", update_now: "更新", whats_new: "更新内容", update_progress: "正在下载更新… {pct}", update_installing: "正在安装：{app} 会自动关闭并重新打开。", update_repo: "（此副本从代码仓库运行：请用 git pull 更新。）", update_failed: "更新失败：{why}",
      language: "语言", game_names: "内部名称", search: "搜索", all: "全部", ground: "地面", infantry: "步兵",
      air: "空军", buildings: "建筑", units: "{n} 个单位", parts: "组件", uses: "使用", own_part: "自有",
      shared_part: "与其他单位共享", used_by: "被引用于", copy_address: "复制地址", no_index: "尚无游戏索引。",
      build_index: "建立索引", pick_unit: "请在左侧选择一个单位。", mod: "模组", new_mod: "新建模组…",
      export_mod: "导出模组…", version: "版本", author: "作者", description: "描述", export: "导出",
      export_help: "一个可分享的文件：打包后的模组文件夹。版本、作者和描述会保存在模组中。",
      open_folder: "打开模组文件夹…", mod_name: "新模组名称", create: "创建", cancel: "取消", close: "关闭",
      no_mod: "请选择或新建一个模组来保存修改。", test_in_game: "在游戏中测试", was: "原为 {v}", reset: "撤销",
      saved: "已保存到 {file}", users_warning: "修改后,所有使用它的单位都会改变({n})。",
      shared_by: "{n} 个单位共用:{names}", change_for: "修改范围", only_unit: "仅 {name}(为其创建独立副本)",
      all_units: "全部 {n} 个", no_via: "从其中一个单位的页面打开,即可只修改那一个。", not_stable: "没有固定地址,暂时无法编辑。",
      locked: "编号和国家保持不变。", edited: "已修改", units_tab: "单位", maps_tab: "地图",
      pick_map: "选择一张地图，以 3D 查看其地形。", map_loading: "正在加载地图…", detail_high: "完整细节", detail_low: "简化",
      water: "水面", place_title: "放置到地图上", place_on: "放置", place_turn: "朝向", place_pick: "请先选择要放置的物体。",
      place_help: "点击地面放置所选物体 · 右键拖动平移 · 滚轮缩放", place_count: "此模组在该地图上放置了 {n} 个", scenery_building: "建筑", scenery_prop: "道具", scenery_vegetation: "树木", scenery_loading: "正在读取地图上的物体…",
      scenery_stats: "已显示：建筑 {buildings} · 道具 {props}/{props_total} · 树木 {trees}/{trees_total}", map_help: "拖动旋转 · 右键拖动平移 · 滚轮缩放", map_stats: "{points} 个点，{triangles} 个三角形",
      no_viewer: "地图视图无法加载 3D 库（首次需要联网）。", ground_loading: "正在加载真实地面纹理… {progress}",
      shape_ground: "塑造地形", brush_hill: "山丘", brush_raise: "抬高", brush_lower: "降低", brush_crater: "弹坑", brush_plateau: "高台",
      brush_flatten: "压平", brush_level: "整平", scen_show: "剧本", maps_all: "所有地图", tip_map_kind: "只显示游戏以此方式提供的地图：遭遇战、作战、战役、演示或测试。", settings_tab: "设置", tip_tab_settings: "语言、按键、游戏文件夹和更新。", settings_title: "设置", set_language_title: "语言", set_language_help: "代号显示游戏内部名称；十种语言中的任何一种显示玩家看到的名称。", set_keys_title: "地图视图按键", set_keys_help: "点击一个按键，然后按下想要的键。", set_game_title: "游戏文件夹", set_game_path: "R.U.S.E. 位于 {path}。", set_game_none: "未找到 R.U.S.E.，请选择其文件夹。", set_game_change: "选择文件夹…", set_updates_title: "更新", set_updates_latest: "这是 RUSE Studio {version}。每次打开时都会检查新版本。", set_updates_check: "立即检查", set_updates_checking: "正在查找新版本…", scen_kind_skirmish: "战斗", scen_kind_operation: "任务", scen_kind_campaign: "战役", scen_kind_demo: "演示", scen_kind_test: "测试用", scen_kind_unused: "不在任何菜单中", tip_scen_show: "显示剧本的区域、起始点（各同盟颜色的柱子）及对局开始时的镜头、出生点（按种类的图标，带国家圆徽）和城镇名称。", tip_scen_pick: "地图的剧本：先是遭遇战，然后是挑战和战役章节。", scen_main: "主要", scen_none: "此地图没有剧本。", scen_stats: "{zones} 个区域 · {starts} 个起始点 · {spawns} 个出生点 · {names} 个名称", scen_zone: "区域", scen_start: "起始点，同盟 {n}", scen_spawn: "出生点", tip_panel_grip: "拖动可移动此面板。双击可复位。", tip_panel_fold: "收起此面板。", tip_panel_unfold: "重新展开此面板。", scen_where: "游戏中：{where}", scen_players: "{n}人", tip_scen_where: "测试后在游戏中开始此项，即可看到你对该布局的更改。", dock_roads: "道路", tip_dock_roads: "绘制新道路：补给卡车会沿着它行驶。端点会吸附到接触的道路上。", road_straight: "直线", road_curve: "曲线", road_free: "自由", tip_road_straight: "直线道路：先点击起点，再点击终点。", tip_road_curve: "弯曲道路：依次点击起点、弯向的点、终点。", tip_road_free: "沿点击路线的道路：沿途点击，然后双击或按回车完成。", road_help_straight: "点击道路起点，再点击终点。靠近道路的端点会吸附上去（圆圈会显示）。", road_help_curve: "依次点击起点、弯曲处、终点。", road_help_free: "沿路线点击；双击、回车或“完成”结束。Esc 放弃。", road_finish: "完成", tip_road_finish: "在最后一个点结束道路。", tip_road_undo: "撤销最后一条道路（Ctrl+Z）。", road_count: "此地图上的新道路：{n}", scen_seat: "队伍 {n} 第 {p} 位", scen_start_tool: "添加起始点", tip_scen_start: "新的玩家起始点：选择队伍，然后点击地图。增加玩家需要每人一个。", scen_team_n: "队伍 {n}", tip_scen_team: "它属于哪个队伍：4对4时，队伍1和2各需要第1到第4个位置。", scen_start_help: "在地图上点击该队下一名玩家开始的位置（开阔地，远离其他人）。", scen_start_place: "起始点：队伍 {n}，第 {p} 位", scen_players_label: "玩家", tip_scen_players: "此模组中这张地图可容纳的玩家数（最多 8）。每人需要一个起始点。", scen_players_game: "{n}（游戏）", scen_players_missing: "{n} 名玩家需要起始点：{list}（剧本 {where}）。用“添加起始点”添加。", scen_players_ok: "每名玩家都有起始点。", scen_players_none: "这张地图不能在线游玩，玩家数无法更改。", road_part: "本段 {len}", road_total: "共 {len}", road_note: "补给卡车会走新道路，道路也会绘制在地面上（已在游戏中验证）。跨越水面的道路会架桥。", roads_show: "道路", tip_roads_show: "以金色显示地图的道路，贴在你塑造的地形上。", check_rename: "重命名为 {name}", tip_check_rename: "把模组中的地图文件夹改名为游戏使用的包名。其中内容不变。", report_problem: "报告问题", tip_report_problem: "在浏览器中打开错误报告，已填好应用和版本。由你检查后自行发布。", report: "报告", tip_report: "作为错误报告：浏览器会打开包含此消息的报告（路径中不含你的用户名）。", set_help_title: "帮助与社区", set_help_help: "Wiki 是使用手册：每个工具都有指南。提问、建议、展示模组或报告错误请到 Discussions。", help_wiki: "Wiki（手册）", tip_help_wiki: "在浏览器中打开 Wiki：每个工具的分步指南。", help_discussions: "Discussions", tip_help_discussions: "在浏览器中打开 Discussions：提问、建议、模组和地图。", check_title: "模组检查：{n} 个问题。游戏构建会在此停止。", check_set_aside: "搁置", tip_check_set_aside: "把文件改名为 <名称>.broken.toml 放在旁边：构建会跳过它，不会丢失任何内容，地图从头开始。", check_aside_done: "已搁置为 {file}。", check_stop: "请先修复模组的问题（顶部的横条）。", scen_count_n: "数量：{n}", tip_scen_count: "一次点击添加的数量（按下方所选队形）。", formation_line: "横队", formation_column: "纵队", formation_wedge: "楔形", formation_box: "方阵", formation_circle: "圆阵", tip_scen_formation: "它们站立的队形。朝向屏幕上方，中心在点击处；圆圈显示每个单位的位置。", tip_scen_gap: "单位之间的间距（米）。", tip_maps_hide: "收起地图列表：给地图更多空间。", tip_maps_show: "再次显示地图列表。", dock_terrain: "地形", dock_movement: "通行", tip_dock_terrain: "山丘、弹坑、高地、坡道：塑造地形。", tip_dock_water: "湖泊与河流：淹没到某一水位，或将其排干。", tip_dock_cover: "单位隐藏之处：绘制掩护、移除掩护，或一键覆盖整个城镇。", tip_dock_movement: "单位可达之处：对所有单位、步兵或车辆封锁地面。", tip_dock_building: "放置地图自带的建筑：单个、区域或一排。", tip_dock_prop: "放置地图自带的物件：栅栏、箱子、残骸等。", tip_dock_vegetation: "种植地图自带的树木：单棵、树林或一排树。", tip_dock_scenario: "所选剧本：移动起始点和出生点，或添加单位和建筑。", brush_block: "封锁", brush_block_infantry: "封锁步兵", brush_block_vehicles: "封锁车辆", tip_brush_block: "任何单位都不能通过：它们会绕行（悬崖、湖、墙）。已在游戏中验证。", tip_brush_block_infantry: "步兵不能通过；车辆可以。", tip_brush_block_vehicles: "车辆不能通过；步兵可以（如同树林）。", brush_open: "开放", brush_open_infantry: "对步兵开放", brush_open_vehicles: "对车辆开放", tip_brush_open: "所有单位都能到达地图原本不让进入的地方（与封锁相反）。在水上它们会站在水底：构建时会警告。", tip_brush_open_infantry: "步兵能到达地图原本不让进入的地方；车辆不变。", tip_brush_open_vehicles: "车辆能到达地图原本不让进入的地方（原本开不进的树林）；步兵不变。", brush_forest: "森林", tip_brush_forest: "一笔画出树木和掩护：像“放置”的“区域”那样撒树（使用那里选的树，否则用地图上最常见的树），并在其下加掩护让单位隐藏。撤销会同时移除两者。", forest_no_trees: "此地图没有可放置的树：地图只接受它已使用的种类。", forest_done: "{n} 棵树，其下有掩护。", move_show: "单位可达", tip_move_show: "显示单位可达之处：红色对所有单位关闭（水、悬崖、地图外），黄色仅对车辆关闭（树林）。", place_solid: "实体", tip_place_solid: "单位不能穿过你放置的建筑（已在游戏中验证）。关闭时：仅绘制。", brush_cover: "掩护", brush_uncover: "移除掩护", brush_town: "城镇", tip_brush_cover: "绘制掩护：单位在其中会像在树林里一样隐藏（绿色）。已在游戏中验证。", tip_brush_uncover: "移除掩护：单位在其中可被看见，即使在树林里。", tip_brush_town: "点击一个城镇：在其每栋建筑周围加上掩护（大小：范围），让单位能在城中隐藏。", cover_show: "掩护", tip_cover_show: "显示单位隐藏之处（绿色）：地图的树林和城镇，以及本模组绘制的区域。", town_none: "这里没有建筑：请点击城镇或一组建筑。", town_done: "{n} 栋建筑周围已加掩护。", group_ap: "穿甲弹（反坦克）", group_he: "高爆弹", group_aa: "防空", group_mg: "机枪", group_infantry_weapons: "步兵武器", group_antitank_weapons: "步兵反坦克武器", group_bombs: "炸弹", group_rockets: "火箭", scen_move_tool: "移动", tip_scen_move: "移动起始点或出生点：点击它，再点击要放的位置。保存在模组中。", scen_spawn_tool: "放置单位", tip_scen_spawn: "添加在此剧本开始时出现的单位或建筑：选择类别、类型和名称，选择阵营，然后点击地图。", tip_scen_kind: "建筑、地面单位、步兵或飞机。", tip_scen_unit: "单位或建筑（按国家）。", tip_scen_camp: "所属阵营。哪个编号对应哪个玩家：请在游戏中测试。", scen_side_neutral: "中立", tip_scen_camp_skirmish: "遭遇战只会生成中立物体，例如地图上的补给站：属于玩家阵营的单位永远不会出现，因此本剧本只能选择中立。", scen_side_n: "阵营 {n}", scen_pick_item: "点击要移动的起始点或出生点。", scen_pick_place: "现在点击 {what} 要放的位置。", scen_remove: "移除", scen_put_back: "放回", scen_take_out: "移除", scen_taken_out: "已移除", scen_take_out_depots: "移除所有补给站", scen_take_out_names: "移除地图上所有地名", tip_scen_take_out: "对局会略去地图上的这个物体（已在游戏中验证：D日地图的补给站和地名消失了）。它仍留在地图文件中，“放回”可恢复。", scen_sectors_whole: "扇区覆盖整张地图", tip_scen_sectors_whole: "此地图的所有场景：扇区之外的每个地方（海面、边缘）都归入最近的扇区，整张地图都可以占领。已在游戏中验证。", road_take_out_roads: "移除地图上的道路", tip_road_take_out_roads: "地图自带的道路会消失：补给卡车行驶的道路网（卡车会改为越野行驶）、从高处和地图桌上看到的道路，以及近处的道路贴图。你新画的道路会保留。已在游戏中验证：道路会消失。卡车越野行驶尚未测试。", road_take_out_bridges: "移除地图上的桥", tip_road_take_out_bridges: "地图自带的桥会消失，部队站立的桥面也一并移除。部队仍可从原桥位置经下方地面通过：要随处过河，请把河流排干（水、排干）。你新建的桥会保留。尚未在游戏中测试。", water_whole: "整张地图铺水", tip_water_whole: "在整张地图上铺一层薄水：水面比地面中间高度高出“强度”，较低的地面在水下，较高的保持干燥。部队可以在水下通行（移动按干地处理），就像海战地图上画出的海。撤销可将其撤回。已在游戏中验证；部队在水下通行尚未测试。", scen_spawn_help: "在地图上点击它出现的位置。", scen_pick_unit: "请先选择单位或建筑。", scen_moved: "已在此模组中移动", scen_mine: "已在此模组中添加", group_all: "所有类型", tip_group: "用途：建筑的作用（司令部、资金、工厂、要塞、假的）或生产该单位的工厂。", group_hq: "司令部", group_money: "资金（补给站、行政）", group_factory: "工厂", group_fort: "要塞与防御", group_fake: "假的（诱饵）", group_barracks: "兵营", group_armor: "装甲", group_antitank: "反坦克", group_artillery: "炮兵", group_prototype: "原型", group_airfield: "机场", group_turret: "要塞火炮", group_other: "其他", brush_water: "水", brush_drain: "排干", tip_brush_water: "把低于水位的地面淹没：水位为开始拖动处的高度加上强度。地面本身不变。", tip_brush_drain: "把水恢复到地图的基准水位：那里的湖泊和河流会干涸。", tip_brush_level: "把地面刷平到同一高度：即开始拖动处的高度。请从所需高度的地面开始。", brush_smooth: "平滑", brush_size: "大小", brush_strength: "强度", brush_look: "查看", brush_undo: "撤销",
      brush_help: "在地面上点击或拖动来绘制 · 中键拖动旋转 · 右键拖动平移 · 滚轮缩放", brush_count: "此地图上的笔画：{n}",
      brush_note: "已保存到模组。“在游戏中测试”会将其构建进地图。", brush_ramp: "斜坡",
      ramp_help: "先点击斜坡的起点，再点击终点。按 Esc 取消。", brush_clear: "重新开始", really_clear: "删除此地图上的全部 {n} 个笔画？",
      remove_all: "删除",
      all_values: "全部 {n} 个", each_value: "逐个设置", price_dates: "每个战役年代一个价格：房主在创建游戏时选择年代（1939、1942、1945、全面战争）。",
      new_unit: "新单位…", new_unit_name: "新单位的名称(所有语言均显示)", price: "价格(所有战役年代)", build_menu: "生产菜单",
      same_menu: "与 {name} 相同", other_menu: "另一个", nation: "国家", factory: "工厂(按其中的单位显示)", more_units: "及另外 {n} 个",
      copy_of: "在此模组中创建的 {name} 的副本。", delete_unit: "删除此单位", really_delete: "删除 {name}?它的修改也会一并删除。",
      new_mark: "新", unit_made: "{name} 已加入模组。在游戏中测试即可在生产菜单中看到它。", unit_deleted: "已从模组中删除 {name}。",
      shot: "开火闪光与声音：{fx}。选择其他弹药时，会换成发射该弹药的武器的闪光与声音。", ammo: "弹药", fired_by: "由 {names} 使用", fired_by_nobody: "没有单位使用", weapons: "武器", models_loading: "正在加载游戏的3D模型… {progress}", weapon_n: "武器 {n}",
      weapons_help: "每件武器使用一种弹药，多个单位可能共用：在弹药页面改数值会影响所有单位；要让本单位拥有专属武器，请在那里复制一份弹药。",
      range: "射程", range_slider: "射程滑块", range_metres: "约 {m} 米",
      tip_range: "这件武器能打多远：它所用弹药的射程。",
      tip_range_slider: "拖动以修改射程，松开即保存。要输入精确数值，请在框中键入。",
      tip_range_box: "以游戏自身单位表示的射程（约260为1米）。输入数字后按回车或点击别处即保存。",
      range_all: "使用此弹药的全部 {n} 个单位",
      tip_range_only: "只有该单位的武器获得新射程：Studio 为这件武器复制一份专用弹药，其他单位保持不变。",
      tip_range_all: "所有使用此弹药的单位都会获得新射程：{names}",
      range_own_copy: "这件武器使用自己的弹药副本，因此此处的修改只影响该单位。",
      tip_range_reset: "将此弹药的射程恢复为游戏原值。",
      dock_group_paint: "地图绘制", tip_dock_group_paint: "用颜色或地图自身的地面绘制地面图像，并移除树木和道具。",
      dock_paint: "绘制", tip_dock_paint: "绘制地面图像：用颜色，或从别处复制的地图自身地面。改变的是地面的外观，而不是形状。",
      brush_paint: "颜色", tip_brush_paint: "在地面上涂颜色：可在色轮上选、从地图自身的颜色中选，或用吸管从地面取色。",
      brush_stamp: "纹理", tip_brush_stamp: "用别处的地图自身地面（草地、沙地、岩石、田地）来绘制：先选好来源处，再在要放的地方涂。",
      brush_opacity: "不透明度 {n}%", tip_brush_opacity: "每一笔覆盖地面的程度：低则淡淡着色，100% 则完全覆盖。在同一处反复涂抹会叠加。",
      tip_paint_swatch_now: "当前绘制所用的颜色。", tip_paint_hex: "以 #rrggbb（红、绿、蓝的十六进制）表示颜色：输入后按回车。",
      tip_paint_wheel: "沿圆环拖动选颜色，在方块里拖动调浓淡和明暗。",
      paint_eyedropper: "吸管", tip_paint_eyedropper: "取色以便匹配：按下此按钮，然后点击地面，或点击建筑、道具、树木，取它自身的颜色（不含光照）。用颜色画笔按 Alt+点击也一样。",
      paint_took_object: "已从 {name} 取色：{hex}",
      tip_paint_swatch: "用此颜色绘制", paint_map_colours: "地图自身的颜色",
      tip_paint_map_colours: "这张地图地面上最常用的颜色（草地、田地、沙地、岩石、道路），让新涂的颜色与之协调。",
      paint_recent: "最近使用", stamp_pick: "选择复制来源",
      tip_stamp_pick: "按下此按钮，然后点击纹理的来源地面（Alt+点击也一样）。之后的第一笔决定距离：复制来源会跟随画笔移动。",
      stamp_pick_help: "点击纹理的来源地面。", stamp_from: "正在从所选位置复制：第二个圆环显示来源。重新选择可换别的位置。",
      stamp_from_none: "请先选择复制来源：按上方按钮，或按 Alt+点击地面。", stamp_picked: "已选好来源：现在在要放置该地面的地方涂抹。",
      stamp_same: "这里就是复制来源：请在别处涂抹。",
      paint_note: "这里在地图图像上显示；构建会绘制游戏地面瓦片的每一级（已在游戏中验证）。", paint_clear: "清理下方地面", tip_paint_clear: "近处时，游戏会在地图图像上绘制草、作物、石头和地面贴花，所以颜料只能从远处看到。开启后，构建会在颜料强度至少一半的地方移除它们，使其在任何高度都可见（已在游戏中验证）。树木、建筑、掩护和移动保持不变。",
      paint_took: "已取色：{hex}", paint_pick_help: "点击地面以吸取其颜色。", paint_hex_bad: "颜色写作 # 加六位十六进制数字，例如 #8a7a4e。",
      fires: "此武器使用的弹药", open_ammo: "打开弹药", copy_ammo: "复制此弹药…", copy_name: "副本名称（仅在此显示）",
      copy_ammo_help: "副本初始与原版相同，游戏内沿用原名。修改数值后，在单位页面为某件武器选用它。",
      copy_made: "{name} 已加入mod。请在单位页面为某件武器选用它。", delete_copy: "删除此副本",
      flag_add: "添加标志位…", flag_add_number: "其他编号…", flag_remove: "移除此标志位",
      flag_used_by: "{n} 个单位具有，例如 {names}", flag_count: "{n} 个单位",
      old_index: "游戏索引由旧版Studio生成。请重新构建（约一分钟）。",
      keys_head: "按键：", keys_move: "{k} 或方向键移动", keys_turn: "{k} 旋转", keys_zoom: "{k} 缩放", keys_fast: "Shift 加速", keys_brushes: "1-9 0 选笔刷", keys_brush: "{k} 笔刷", keys_place: "{k} 放置", keys_look: "Esc 查看", keys_undo: "Ctrl+Z 撤销", keys_size: "{k} 大小", keys_strength: "{k} 强度或旋转", keys_change: "更改按键…", tip_keys_change: "为地图视图选择自己的按键。", keys_press: "按下一个键…", keys_reset: "默认", keys_fixed: "点击一个按键再按下新键。方向键、Esc、Ctrl+Z 和数字键保持不变。", key_forward: "前进", key_back: "后退", key_left: "左", key_right: "右", key_turn_left: "向左旋转", key_turn_right: "向右旋转", key_zoom_in: "放大", key_zoom_out: "缩小", key_brush: "笔刷", key_place: "放置", key_size_down: "变小", key_size_up: "变大", key_strength_down: "减弱，或向左旋转", key_strength_up: "增强，或向右旋转",
      scenery_note: "放置的树木和建筑本身不提供掩护：用“掩护”画笔绘制，或用“城镇”画笔点击城镇。建筑会阻挡单位（实体）。", place_ground: "请点击地图的地面。",
      undone: "已撤销：{name} 恢复原值。", tip_tab_units: "浏览游戏单位并修改其数值。", tip_tab_maps: "以 3D 查看地图地形，塑造它并放置物体。",
      tip_mod: "保存你修改的模组。", tip_test: "将模组构建进游戏副本并启动。", tip_lang: "名称和标签的语言；内部名称显示游戏自己的名称。",
      tip_update_now: "下载并安装新版本；应用会自动重新打开。", tip_update_info: "在浏览器中打开更新说明。", tip_create_mod: "新建一个空模组并选中它。",
      tip_cancel: "关闭且不做任何更改。", tip_export: "将模组打包成一个可分享的文件。", tip_close: "隐藏日志。",
      tip_build_index: "读取一次游戏文件，以便浏览其单位（约一分钟）。", tip_search: "按名称筛选列表。/ 键聚焦此框，Esc 清空，上下键在列表中移动。",
      tip_kind: "只显示这一类单位。", tip_nation: "只显示该国家的单位。", tip_open_unit: "打开此单位（上下键在列表中移动）。",
      tip_copy_address: "将此单位的地址复制到剪贴板。", tip_value: "输入新值后按回车或离开输入框：会立即保存到模组。", tip_each_value: "每个值单独一个输入框，逐个修改。",
      tip_reset: "恢复游戏原值（Ctrl+Z 撤销最后一次修改）。", tip_change_for: "此处的修改只影响该单位，还是影响所有共享此组件的单位。",
      tip_new_unit: "复制此单位，赋予它自己的名称、价格和生产菜单。", tip_unit_name: "玩家看到的名称（所有语言相同）。", tip_price: "生产成本（所有战役年代相同）。",
      tip_menu: "新单位出现的生产菜单。", tip_create_unit: "将新单位加入模组。", tip_delete_unit: "将此单位连同其修改从模组中移除。", tip_part: "打开此组件。",
      tip_source: "打开此单位的复制来源。", tip_open_map: "以 3D 显示此地图的地形（{file}）。", tip_detail: "在简化和完整的地形网格之间切换。",
      tip_water: "显示或隐藏水面。", tip_show_group: "在地图上显示或隐藏它们（只影响绘制）。", tip_brush: "用此笔刷塑造地形（按键 {n}）。",
      tip_brush_size: "笔画的宽度，按地图的比例（按键 [ 和 ]）。", tip_brush_strength: "笔画对地形的改动幅度（按键 - 和 =）。",
      tip_look: "停止绘制或放置：此后拖动即旋转视角（Esc）。", tip_brush_undo: "撤销最后一笔（Ctrl+Z）。", tip_brush_clear: "删除此模组在该地图上的全部笔画。",
      tip_remove_all: "是，全部删除。", tip_place_group: "选择要放置的物体种类。", tip_place_search: "筛选列表。地图只能放置它已在使用的类型。",
      tip_place_type: "要放置的物体；选中即进入放置模式。", tip_place_turn: "物体的朝向，单位为度（放置时用按键 - 和 =）。",
      tip_place_size: "物体的大小，相对于游戏原尺寸（放置时用按键 [ 和 ]）。", tip_place_on: "在你点击地面的位置放置所选物体（P）。",
      tip_place_undo: "从地图上移除最后放置的物体（Ctrl+Z）。",
      place_one: "单个", place_area: "区域", place_line: "直线", tip_place_one: "每次点击地面放置一个物体。", tip_place_area: "在地面上拖动以填满区域：树林、村庄。物体之间至少保持所设间距。", tip_place_line: "先点击直线起点，再点击终点：按间距放置物体，并沿直线方向摆放（树篱、一排房屋）。", place_spacing: "间距 {m} 米", tip_place_spacing: "区域或直线中物体之间的距离（针对此类物体）。", place_area_size: "区域 {m} 米", tip_place_area_size: "区域笔刷的半径：一笔填充的宽度。", place_area_help: "在地面上拖动，用所选物体填满。中键拖动旋转视角，右键拖动平移。", place_line_help: "点击直线起点，再点击终点。按 Esc 取消未完成的直线。", place_line_next: "现在点击直线的终点。", place_none_room: "此处没有空间：间距范围内已都有物体。", place_placed: "已放置 {n} 个物体并保存到mod。Ctrl+Z 可一次撤销。", place_most: "一笔最多放置这么多；如需更多请再画一次。" },
  };
  // the troubleshooter's words (words.toml doc_*)
  Object.assign(words.us, { doc_button: "Troubleshoot", doc_title: "Troubleshooter", doc_intro: "What can stop a test or Play, checked in one go.", doc_checking: "Checking…", doc_again: "Check again", doc_copy: "Copy report", doc_copied: "Report copied: paste it into your bug report or on Discord.", doc_close: "Close", doc_fix_close_game: "Close R.U.S.E.", doc_fix_clear_leftovers: "Clear them", doc_fix_choose_game: "Choose folder…", doc_fixed: "Done ({done}).", doc_fix_left: "Not everything could be done: {left}", doc_game_ok: "R.U.S.E. found: {path}", doc_game_missing: "R.U.S.E. wasn't found. Choose its folder (the one with RUSE.exe).", doc_steam_ok: "Steam is running.", doc_steam_off: "Steam isn't running. It's started for you when you play.", doc_running_none: "No R.U.S.E. left running.", doc_running_copy: "R.U.S.E. is still running from a modded copy: {names}. Close it before the next test or Play.", doc_running_game: "R.U.S.E. is running (the Steam game): {names}. Close it before testing mods.", doc_drive_ok: "Modded copies go to {path} ({fs}).", doc_drive_other: "Modded copies go to {path}, on a {fs} drive: each copy is a full copy, and Windows may refuse to delete one while R.U.S.E. runs. An NTFS drive is best.", doc_space_ok: "{gb} GB free for modded copies.", doc_space_low: "Only {gb} GB free where modded copies go: a copy may need {need} GB.", doc_left_none: "No leftover copies.", doc_left: "Leftover copies: {names}. They only take up space; you can clear them now.", doc_left_held: "Leftover copies: {names}, held by {held}. Close that program, then clear them.", doc_readonly: "{n} of the game's files are marked read-only. That's fine: modded copies never keep the mark.", doc_write_ok: "The app can write where modded copies go.", doc_write_fail: "The app can't write to {path} ({why}). Modded copies always go there, on the game's drive: check that folder's permissions, or whether an antivirus blocks it.", doc_troubleshoot_link: "Troubleshoot" });
  Object.assign(words.fr, { doc_button: "Dépannage", doc_title: "Dépannage", doc_intro: "Ce qui peut bloquer un test ou « Jouer », vérifié en une fois.", doc_checking: "Vérification…", doc_again: "Vérifier à nouveau", doc_copy: "Copier le rapport", doc_copied: "Rapport copié : collez-le dans votre rapport de bug ou sur Discord.", doc_close: "Fermer", doc_fix_close_game: "Fermer R.U.S.E.", doc_fix_clear_leftovers: "Les supprimer", doc_fix_choose_game: "Choisir le dossier…", doc_fixed: "Fait ({done}).", doc_fix_left: "Tout n'a pas pu être fait : {left}", doc_game_ok: "R.U.S.E. trouvé : {path}", doc_game_missing: "R.U.S.E. est introuvable. Choisissez son dossier (celui qui contient RUSE.exe).", doc_steam_ok: "Steam est lancé.", doc_steam_off: "Steam n'est pas lancé. Il est démarré pour vous quand vous jouez.", doc_running_none: "Aucun R.U.S.E. resté ouvert.", doc_running_copy: "R.U.S.E. tourne encore depuis une copie avec mods : {names}. Fermez-le avant le prochain test ou « Jouer ».", doc_running_game: "R.U.S.E. est lancé (le jeu Steam) : {names}. Fermez-le avant de tester des mods.", doc_drive_ok: "Les copies avec mods vont dans {path} ({fs}).", doc_drive_other: "Les copies avec mods vont dans {path}, sur un disque {fs} : chaque copie est complète, et Windows peut refuser d'en supprimer une pendant que R.U.S.E. tourne. Un disque NTFS est préférable.", doc_space_ok: "{gb} Go libres pour les copies avec mods.", doc_space_low: "Seulement {gb} Go libres là où vont les copies avec mods : une copie peut demander {need} Go.", doc_left_none: "Aucune copie restante.", doc_left: "Copies restantes : {names}. Elles ne font qu'occuper de la place ; vous pouvez les supprimer dès maintenant.", doc_left_held: "Copies restantes : {names}, bloquées par {held}. Fermez ce programme, puis supprimez-les.", doc_readonly: "{n} fichiers du jeu sont en lecture seule. Ce n'est pas un problème : les copies avec mods ne gardent jamais cet attribut.", doc_write_ok: "L'application peut écrire là où vont les copies avec mods.", doc_write_fail: "L'application ne peut pas écrire dans {path} ({why}). Les copies avec les mods vont toujours là, sur le disque du jeu : vérifiez les autorisations de ce dossier, ou si un antivirus le bloque.", doc_troubleshoot_link: "Dépannage" });
  Object.assign(words.sc, { doc_button: "故障排查", doc_title: "故障排查", doc_intro: "一次检查所有可能阻止测试或“开始游戏”的问题。", doc_checking: "正在检查…", doc_again: "重新检查", doc_copy: "复制报告", doc_copied: "报告已复制：请粘贴到你的错误报告或 Discord 中。", doc_close: "关闭", doc_fix_close_game: "关闭 R.U.S.E.", doc_fix_clear_leftovers: "清除", doc_fix_choose_game: "选择文件夹…", doc_fixed: "已完成（{done}）。", doc_fix_left: "部分操作未能完成：{left}", doc_game_ok: "已找到 R.U.S.E.：{path}", doc_game_missing: "未找到 R.U.S.E.。请选择其文件夹（包含 RUSE.exe 的那个）。", doc_steam_ok: "Steam 正在运行。", doc_steam_off: "Steam 未运行。开始游戏时会自动为你启动。", doc_running_none: "没有仍在运行的 R.U.S.E.。", doc_running_copy: "R.U.S.E. 仍在从模组版副本运行：{names}。请在下次测试或“开始游戏”前关闭它。", doc_running_game: "R.U.S.E.（Steam 游戏）正在运行：{names}。测试模组前请先关闭它。", doc_drive_ok: "模组版副本保存在 {path}（{fs}）。", doc_drive_other: "模组版副本保存在 {fs} 驱动器上的 {path}：每份都是完整副本，且 R.U.S.E. 运行时 Windows 可能拒绝删除它。最好使用 NTFS 驱动器。", doc_space_ok: "模组版副本可用空间：{gb} GB。", doc_space_low: "模组版副本所在位置仅剩 {gb} GB 可用空间：一份副本可能需要 {need} GB。", doc_left_none: "没有残留的副本。", doc_left: "残留的副本：{names}。它们只占用空间；你可以现在就清除。", doc_left_held: "残留的副本：{names}，被 {held} 占用。请关闭该程序，然后清除它们。", doc_readonly: "游戏有 {n} 个文件被标记为只读。这没有问题：模组版副本不会保留此标记。", doc_write_ok: "应用可以写入模组版副本所在的位置。", doc_write_fail: "应用无法写入 {path}（{why}）。模组版副本总是放在那里，即游戏所在的驱动器：请检查该文件夹的权限，或是否被杀毒软件拦截。", doc_troubleshoot_link: "故障排查" });
  // the clean game backup's words (words.toml backup_*, set_backup_*)
  Object.assign(words.us, { set_backup_title: "Clean game backup", set_backup_help: "RUSE Launcher and RUSE Studio never change the game's own folder, but other mod managers and hand edits can. Make a backup while the game is clean, right after Steam installs or verifies it. Check game files then shows what has changed since, and Restore clean files puts the game's files back.", backup_none: "No backup yet. It takes {need} GB; {free} GB is free on {drive}.", backup_have: "Backup of build {build}, made {date} ({size} GB): {path}", backup_other: "The backup is of build {build} (made {date}), but Steam has updated the game since (build {now}), so it can't be used. Verify with Steam, then make a new backup.", backup_make: "Make backup", backup_make_again: "Make backup again", backup_replace_ask: "This replaces the backup made {date}. Do it only if the game is clean now (use Verify with Steam first). Replace it?", backup_replace_yes: "Replace", backup_check: "Check game files", backup_deep: "Compare every byte (slower)", backup_restore: "Restore clean files", backup_restore_ask: "{n} file(s) will be copied back from the backup, and {m} file(s) that aren't the game's will be moved into a folder in {path}. Nothing is deleted. Restore?", backup_restore_yes: "Restore", backup_verify: "Verify with Steam", backup_verify_tip: "Steam's own repair: it checks every file and downloads the ones that changed. No backup needed.", backup_verify_opened: "Steam is checking the game's files and downloads any that changed; Steam shows how far it is.", backup_making: "Making the backup… {pct}", backup_checking: "Checking the game's files… {pct}", backup_restoring: "Restoring the game's files… {pct}", backup_made: "Backup made: {files} files, {size} GB.", backup_clean: "The game's files match the backup: nothing has changed.", backup_differs: "{n} file(s) differ from the backup:", backup_changed: "Changed ({n})", backup_missing: "Missing ({n})", backup_added: "Not the game's ({n})", backup_more: "…and {n} more", backup_nothing: "Nothing to restore: the game's files match the backup.", backup_restored: "Done: {n} file(s) restored.", backup_set_aside: "{m} file(s) that weren't the game's are now in {path}.", backup_kept: "The {k} changed file(s) that were replaced are kept in {path}." });
  Object.assign(words.fr, { set_backup_title: "Sauvegarde propre du jeu", set_backup_help: "RUSE Launcher et RUSE Studio ne modifient jamais le dossier du jeu, mais d'autres gestionnaires de mods et des modifications à la main peuvent le faire. Faites une sauvegarde pendant que le jeu est propre, juste après que Steam l'a installé ou vérifié. « Vérifier les fichiers du jeu » montre ensuite ce qui a changé depuis, et « Restaurer les fichiers propres » remet les fichiers du jeu en place.", backup_none: "Pas encore de sauvegarde. Elle demande {need} Go ; {free} Go sont libres sur {drive}.", backup_have: "Sauvegarde de la version {build}, faite le {date} ({size} Go) : {path}", backup_other: "La sauvegarde est de la version {build} (faite le {date}), mais Steam a mis le jeu à jour depuis (version {now}) : elle ne peut pas servir. Vérifiez avec Steam, puis faites une nouvelle sauvegarde.", backup_make: "Faire une sauvegarde", backup_make_again: "Refaire la sauvegarde", backup_replace_ask: "Ceci remplace la sauvegarde faite le {date}. Ne le faites que si le jeu est propre maintenant (utilisez d'abord « Vérifier avec Steam »). La remplacer ?", backup_replace_yes: "Remplacer", backup_check: "Vérifier les fichiers du jeu", backup_deep: "Comparer chaque octet (plus lent)", backup_restore: "Restaurer les fichiers propres", backup_restore_ask: "{n} fichier(s) seront recopiés depuis la sauvegarde, et {m} fichier(s) qui ne sont pas ceux du jeu seront déplacés dans un dossier de {path}. Rien n'est supprimé. Restaurer ?", backup_restore_yes: "Restaurer", backup_verify: "Vérifier avec Steam", backup_verify_tip: "La réparation de Steam : il vérifie chaque fichier et retélécharge ceux qui ont changé. Aucune sauvegarde nécessaire.", backup_verify_opened: "Steam vérifie les fichiers du jeu et retélécharge ceux qui ont changé ; Steam affiche sa progression.", backup_making: "Sauvegarde en cours… {pct}", backup_checking: "Vérification des fichiers du jeu… {pct}", backup_restoring: "Restauration des fichiers du jeu… {pct}", backup_made: "Sauvegarde faite : {files} fichiers, {size} Go.", backup_clean: "Les fichiers du jeu correspondent à la sauvegarde : rien n'a changé.", backup_differs: "{n} fichier(s) diffèrent de la sauvegarde :", backup_changed: "Modifiés ({n})", backup_missing: "Manquants ({n})", backup_added: "Pas du jeu ({n})", backup_more: "…et {n} de plus", backup_nothing: "Rien à restaurer : les fichiers du jeu correspondent à la sauvegarde.", backup_restored: "Terminé : {n} fichier(s) restauré(s).", backup_set_aside: "{m} fichier(s) qui n'étaient pas ceux du jeu sont maintenant dans {path}.", backup_kept: "Les {k} fichier(s) modifié(s) qui ont été remplacés sont conservés dans {path}." });
  Object.assign(words.sc, { set_backup_title: "游戏的干净备份", set_backup_help: "RUSE Launcher 和 RUSE Studio 从不修改游戏本身的文件夹，但其他模组管理器和手动修改可能会。请在游戏干净时（Steam 刚安装或验证完之后）创建备份。之后，“检查游戏文件”会显示自那以后改变了什么，“恢复干净文件”会把游戏文件还原。", backup_none: "还没有备份。需要 {need} GB；{drive} 上有 {free} GB 可用。", backup_have: "版本 {build} 的备份，创建于 {date}（{size} GB）：{path}", backup_other: "备份来自版本 {build}（创建于 {date}），但 Steam 之后更新了游戏（版本 {now}），因此无法使用。请先通过 Steam 验证，然后创建新的备份。", backup_make: "创建备份", backup_make_again: "重新创建备份", backup_replace_ask: "这将替换创建于 {date} 的备份。只有在游戏现在是干净的时候才这样做（请先使用“通过 Steam 验证”）。要替换吗？", backup_replace_yes: "替换", backup_check: "检查游戏文件", backup_deep: "逐字节比较（较慢）", backup_restore: "恢复干净文件", backup_restore_ask: "将从备份复制回 {n} 个文件，并把 {m} 个不属于游戏的文件移到 {path} 中的一个文件夹。不会删除任何东西。要恢复吗？", backup_restore_yes: "恢复", backup_verify: "通过 Steam 验证", backup_verify_tip: "Steam 自带的修复：检查每个文件并重新下载有变化的文件。不需要备份。", backup_verify_opened: "Steam 正在检查游戏文件，并重新下载有变化的文件；进度显示在 Steam 中。", backup_making: "正在创建备份… {pct}", backup_checking: "正在检查游戏文件… {pct}", backup_restoring: "正在恢复游戏文件… {pct}", backup_made: "备份已创建：{files} 个文件，{size} GB。", backup_clean: "游戏文件与备份一致：没有任何变化。", backup_differs: "与备份不同的文件：{n} 个", backup_changed: "已更改（{n}）", backup_missing: "缺失（{n}）", backup_added: "不属于游戏（{n}）", backup_more: "…还有 {n} 个", backup_nothing: "无需恢复：游戏文件与备份一致。", backup_restored: "完成：已恢复 {n} 个文件。", backup_set_aside: "{m} 个不属于游戏的文件现在位于 {path}。", backup_kept: "被替换的 {k} 个已更改文件保存在 {path}。" });
  // a panel's size handle (words.toml tip_panel_size)
  Object.assign(words.us, { tip_panel_size: "Size {n}%: drag down to make this panel smaller, up to make it bigger (the mouse wheel works too). Double-click: normal size." });
  Object.assign(words.fr, { tip_panel_size: "Taille {n} % : glissez vers le bas pour réduire ce panneau, vers le haut pour l'agrandir (la molette marche aussi). Double-clic : taille normale." });
  // what's selected on the map (words.toml scen_sel_*)
  Object.assign(words.us, { scen_sel_count: "{n} selected", scen_sel_ground: "vehicles", scen_sel_infantry: "infantry", scen_sel_air: "aircraft", scen_sel_buildings: "buildings", scen_sel_other: "others", scen_sel_only: "Click to keep only these selected.", scen_sel_hint: "Drag a box on the ground to select several · Shift+click adds or takes one off · Esc clears", scen_sel_clear: "Clear" });
  Object.assign(words.fr, { scen_sel_count: "{n} sélectionnés", scen_sel_ground: "véhicules", scen_sel_infantry: "infanterie", scen_sel_air: "avions", scen_sel_buildings: "bâtiments", scen_sel_other: "autres", scen_sel_only: "Cliquez pour ne garder que ceux-ci.", scen_sel_hint: "Tracez un cadre sur le sol pour en sélectionner plusieurs · Maj+clic en ajoute ou en retire un · Échap efface", scen_sel_clear: "Effacer" });
  // a test the build stopped (words.toml test_problems_title, test_fix_*, tip_copy_log, tip_status_close)
  Object.assign(words.us, {"test_problems_title": "The test stopped on {n} mistake(s) in your mods. Nothing in the game was changed. Fix each one here, then press Test in game again.", "test_in_mod": "(in {mod})", "test_no_fix": "No one-click fix: change it in the mod as the message says.", "test_fix_neutral": "Make it neutral", "tip_test_fix_neutral": "BATTLES maps place only neutral spawns: this keeps the unit and makes it neutral (camp -1).", "test_fix_remove_spawn": "Remove this spawn", "tip_test_fix_remove_spawn": "Takes this unit out of the map's scenario.toml in your mod.", "test_fix_remove_road": "Remove road {n}", "tip_test_fix_remove_road": "Takes this new road out of the map's roads.toml in your mod. Draw it again with both ends on a road if you want it back.", "test_fixed": "Fixed ({done}). Press Test in game again.", "tip_copy_log": "Copy the whole log and the message, to paste into a bug report or on Discord.", "test_copy_failed": "The log couldn't be copied: select it with the mouse and press Ctrl+C.", "tip_status_close": "Hide this message."});
  Object.assign(words.fr, {"test_problems_title": "Le test s'est arrêté sur {n} erreur(s) dans vos mods. Rien n'a été changé dans le jeu. Corrigez-les ici, puis relancez Tester en jeu.", "test_in_mod": "(dans {mod})", "test_no_fix": "Pas de correction en un clic : modifiez le mod comme le message l'indique.", "test_fix_neutral": "La rendre neutre", "tip_test_fix_neutral": "Les cartes BATAILLES ne placent que les apparitions neutres : l'unité reste, mais neutre (camp -1).", "test_fix_remove_spawn": "Retirer cette apparition", "tip_test_fix_remove_spawn": "Retire cette unité du scenario.toml de la carte dans votre mod.", "test_fix_remove_road": "Retirer la route {n}", "tip_test_fix_remove_road": "Retire cette nouvelle route du roads.toml de la carte dans votre mod. Redessinez-la avec les deux bouts sur une route pour la remettre.", "test_fixed": "Corrigé ({done}). Relancez Tester en jeu.", "tip_copy_log": "Copie tout le journal et le message, à coller dans un rapport de bug ou sur Discord.", "test_copy_failed": "Le journal n'a pas pu être copié : sélectionnez-le à la souris et appuyez sur Ctrl+C.", "tip_status_close": "Masquer ce message."});
  Object.assign(words.sc, {"test_problems_title": "测试因模组中的 {n} 个错误而停止。游戏没有任何改动。请在这里逐个修正，然后再次点击“在游戏中测试”。", "test_in_mod": "（在 {mod} 中）", "test_no_fix": "没有一键修正：请按消息所说修改模组。", "test_fix_neutral": "设为中立", "tip_test_fix_neutral": "“战役”地图只放置中立的出生单位：保留该单位并设为中立（阵营 -1）。", "test_fix_remove_spawn": "删除这个出生单位", "tip_test_fix_remove_spawn": "从你的模组中该地图的 scenario.toml 里删除这个单位。", "test_fix_remove_road": "删除道路 {n}", "tip_test_fix_remove_road": "从你的模组中该地图的 roads.toml 里删除这条新道路。如需恢复，请重新绘制并让两端都连到道路上。", "test_fixed": "已修正（{done}）。请再次点击“在游戏中测试”。", "tip_copy_log": "复制完整日志和消息，可粘贴到错误报告或 Discord。", "test_copy_failed": "无法复制日志：请用鼠标选中后按 Ctrl+C。", "tip_status_close": "隐藏这条消息。"});
  Object.assign(words.us, {"test_fix_neutral_all": "Make all {n} team spawns here neutral", "tip_test_fix_neutral_all": "The test stops at the first team spawn, so this fixes every one in this map setup at once: each unit stays, made neutral (camp -1).", "test_fix_remove_all": "Remove all {n} team spawns here", "tip_test_fix_remove_all": "Takes every team spawn of this map setup out of the map's scenario.toml in your mod; neutral spawns stay."});
  Object.assign(words.fr, {"test_fix_neutral_all": "Rendre neutres les {n} apparitions d'équipe ici", "tip_test_fix_neutral_all": "Le test s'arrête à la première apparition d'équipe : ceci les corrige toutes dans cette configuration de carte, chaque unité reste, mais neutre (camp -1).", "test_fix_remove_all": "Retirer les {n} apparitions d'équipe ici", "tip_test_fix_remove_all": "Retire toutes les apparitions d'équipe de cette configuration du scenario.toml de la carte dans votre mod ; les neutres restent."});
  Object.assign(words.sc, {"test_fix_neutral_all": "将这里全部 {n} 个队伍出生单位设为中立", "tip_test_fix_neutral_all": "测试会在第一个队伍出生单位处停止，所以这会一次修正此地图设置中的全部：每个单位保留并设为中立（阵营 -1）。", "test_fix_remove_all": "删除这里全部 {n} 个队伍出生单位", "tip_test_fix_remove_all": "从你的模组中该地图的 scenario.toml 里删除此设置的全部队伍出生单位；中立的保留。"});
  // the zones' fill on the ground (words.toml zone_fill, tip_zone_fill)
  Object.assign(words.us, {"zone_fill": "Zones' fill", "tip_zone_fill": "The scenario's zones (sectors: a ruse covers one) are drawn on the ground: a clear line along each border, and a see-through colour inside. This sets the inside: 0 % shows the borders alone."});
  Object.assign(words.fr, {"zone_fill": "Remplissage des zones", "tip_zone_fill": "Les zones du scénario (secteurs : une ruse en couvre un) sont dessinées au sol : une ligne nette le long de chaque bord, et une couleur transparente à l'intérieur. Ceci règle l'intérieur : 0 % ne montre que les bords."});
  Object.assign(words.sc, {"zone_fill": "区域填充", "tip_zone_fill": "剧本的区域（扇区：一个计谋作用于一个扇区）画在地面上：每条边界一条清晰的线，内部为半透明颜色。此项设置内部：0 % 只显示边界。"});
  // the Spawn tool: Stick to roads, the depot spot, the icons legend
  Object.assign(words.us, {"scen_snap_roads": "Stick to roads", "tip_scen_snap_roads": "A supply depot spot or a starting point (its HQ) goes beside the nearest road, as far from it as the game's own maps keep theirs. Untick it to put one exactly where you click, in the middle of a field say.", "scen_depot_slab": "Supply depot spot", "scen_depot_any": "Any side", "legend_spawn_icons": "Icons: what a scenario puts there at the start, by what it's for: HQ (star), supply depot (crate), factory, fort (shield), decoy (?), and units by what builds them (soldier, tank, anti-tank gun, artillery, plane); the roundel in the corner is its country, the colour its side", "scen_camp_label": "Who gets it?", "scen_owner_player": "Player", "scen_owner_ai": "Computer", "scen_owner_camp": "side {camp}", "scen_owner_unknown": "Side {camp}", "scen_owner_team": "Team {team}."});
  Object.assign(words.fr, {"scen_snap_roads": "Coller aux routes", "tip_scen_snap_roads": "Un emplacement de dépôt ou un point de départ (son QG) se place à côté de la route la plus proche, à la distance que gardent les cartes du jeu. Décochez pour le poser exactement où vous cliquez, au milieu d'un champ par exemple.", "scen_depot_slab": "Emplacement de dépôt de ravitaillement", "scen_depot_any": "Tous camps", "legend_spawn_icons": "Icônes : ce que le scénario place au départ, selon son rôle : QG (étoile), dépôt (caisse), usine, fort (bouclier), leurre (?), et les unités selon ce qui les produit (soldat, char, antichar, artillerie, avion) ; la cocarde dans le coin est son pays, la couleur son camp"});
  Object.assign(words.sc, {"scen_snap_roads": "吸附道路", "tip_scen_snap_roads": "补给站位置或起始点（其指挥部）会放在最近道路旁，与游戏自带地图的距离相同。取消勾选则放在你点击的位置，比如田野中央。", "scen_depot_slab": "补给站位置", "scen_depot_any": "任意阵营", "legend_spawn_icons": "图标：场景开始时放在此处的东西，按用途区分：指挥部（星）、补给站（箱子）、工厂、要塞（盾牌）、诱饵（？），单位按生产来源（士兵、坦克、反坦克炮、火炮、飞机）；角上的徽章表示国家，颜色表示阵营"});
  // the opening camera (words.toml scen_cam_*)
  Object.assign(words.us, {"scen_cam_what": "Opening camera · team {n}, place {p}", "scen_cam_rest": "the match opens looking from here, after its warm-up flight (the dotted line)", "scen_cam_view": "what the screen shows when the match opens"});
  Object.assign(words.fr, {"scen_cam_what": "Caméra d'ouverture · équipe {n}, place {p}", "scen_cam_rest": "la partie s'ouvre en regardant d'ici, après le vol d'introduction (la ligne pointillée)", "scen_cam_view": "ce que montre l'écran à l'ouverture de la partie"});
  Object.assign(words.sc, {"scen_cam_what": "开局镜头 · 队伍 {n}，位置 {p}", "scen_cam_rest": "对局在预热飞行（虚线）之后，从这里的视角开始", "scen_cam_view": "对局开始时屏幕显示的范围"});
  Object.assign(words.us, {"scen_cam_drag": "Or drag a start's camera round its HQ to open the match from another side.", "scen_cam_drag_tip": "drag it round the HQ to open the match from another side", "scen_drag_tip": "drag to move it", "scen_drag_help": "Drag any starting point, spawn, supply depot, camera, name, named point or zone on the map to move it: it's saved in the mod when you let go.", "scen_cam_turned": "Camera turned {deg}°.", "scen_cam_back": "Camera back"});
  Object.assign(words.us, {"scen_layers_show": "Show", "scen_layer_starts": "Starts", "scen_layer_cams": "Cameras", "scen_layer_depots": "Depots", "scen_layer_buildings": "Buildings", "scen_layer_units": "Units", "scen_layer_zones": "Zones", "scen_layer_towns": "Towns", "tip_scen_layers": "Show or hide this kind on the map. Only the view changes, never the mod.", "scen_icon_size": "Icon size {pct} %", "tip_scen_icon_size": "How big the icons are on the map. They also get smaller as you zoom out."});
  const nations = {
    base: ["EU", "Allemagne", "RU", "France", "Italie", "URSS", "Japon"],
    us: ["USA", "Germany", "UK", "France", "Italy", "USSR", "Japan"],
    fr: ["États-Unis", "Allemagne", "Royaume-Uni", "France", "Italie", "URSS", "Japon"],
    sc: ["美国", "德国", "英国", "法国", "意大利", "苏联", "日本"],
  };
  const labels = {
    us: { SeuilMort: "Health", VitesseLineaire: "Speed", ProductionPrice: "Price", ProductionTime: "Build time",
      DetectionBase: "Vision range", Factory: "Factory", PositionInMenu: "Menu slot", Nationalite: "Nation",
      DescriptorId: "Id", ClassNameForDebug: "Debug name", NameInMenuToken: "Name (text key)", Puissance: "Power",
      PorteeMaximale: "Maximum range", TempsEntreDeuxTirs: "Time between shots", TirEnMouvement: "Fires while moving", InitialFlagSet: "Flags" },
    fr: { SeuilMort: "Points de vie", VitesseLineaire: "Vitesse", ProductionPrice: "Prix", ProductionTime: "Temps de production",
      DetectionBase: "Portée de vision", Factory: "Usine", PositionInMenu: "Position dans le menu", Nationalite: "Nation",
      DescriptorId: "Identifiant", ClassNameForDebug: "Nom de débogage", NameInMenuToken: "Nom (clé de texte)",
      Puissance: "Puissance", PorteeMaximale: "Portée maximale", TempsEntreDeuxTirs: "Temps entre deux tirs",
      TirEnMouvement: "Tir en mouvement", InitialFlagSet: "Drapeaux" },
    sc: { SeuilMort: "生命值", VitesseLineaire: "速度", ProductionPrice: "价格", ProductionTime: "生产时间",
      DetectionBase: "视野范围", Factory: "工厂", PositionInMenu: "菜单位置", Nationalite: "国家", DescriptorId: "编号",
      ClassNameForDebug: "调试名称", NameInMenuToken: "名称(文本键)", Puissance: "威力", PorteeMaximale: "最大射程",
      TempsEntreDeuxTirs: "射击间隔", TirEnMouvement: "行进间射击", InitialFlagSet: "标志位" },
  };
  const groups = {
    us: { identity: "Identity", cost: "Cost", combat: "Combat", movement: "Movement", vision: "Vision", menu: "Build menu",
      weapon: "Weapon", other: "Other" },
    fr: { identity: "Identité", cost: "Coût", combat: "Combat", movement: "Déplacement", vision: "Vision",
      menu: "Menu de production", weapon: "Arme", other: "Autres" },
    sc: { identity: "标识", cost: "成本", combat: "战斗", movement: "移动", vision: "视野", menu: "生产菜单",
      weapon: "武器", other: "其他" },
  };
  const E = "$/GFX/Everything/Descriptor_Unit_";
  const AMMO = "$/GFX/Everything/Ammo_75mm_M3";
  const units = [
    { id: "M4_Sherman", kind: "ground", nation: 0, factory: 10, slot: 302, key: "U_M4",
      names: { us: "M4 Sherman", fr: "M4 Sherman", sc: "M4 谢尔曼" }, price: 40, hp: 12, speed: 38 },
    { id: "M3A1_Stuart", kind: "ground", nation: 0, factory: 10, slot: 301, key: "U_M3A1",
      names: { us: "M3A1 Stuart", fr: "M3A1 Stuart", sc: "M3A1 斯图亚特" }, price: 25, hp: 7, speed: 45 },
    { id: "Panzer_IV_G", kind: "ground", nation: 1, factory: 10, slot: 302, key: "U_PZIV",
      names: { us: "Panzer IV", fr: "Panzer IV", sc: "四号坦克" }, price: 45, hp: 13, speed: 34 },
    { id: "Soldat_US_Leger", kind: "infantry", nation: 0, factory: 8, slot: 101, key: "U_GI",
      names: { us: "Infantry", fr: "Infanterie", sc: "步兵" }, price: 10, hp: 4, speed: 12 },
    { id: "Type97_ChiHa", kind: "ground", nation: 6, factory: 10, slot: 302, key: "U_CHIHA",
      names: { us: "Type 97 Chi-Ha", fr: "Type 97 Chi-Ha", sc: "九七式中战车" }, price: 30, hp: 9, speed: 36 },
    { id: "P40Warhawk", kind: "air", nation: 0, factory: 9, slot: 201, key: "U_P40",
      names: { us: "P-40 Warhawk", fr: "P-40 Warhawk", sc: "P-40 战鹰" }, price: 35, hp: 5, speed: 330 },
    { id: "Building_Headquarter", kind: "buildings", nation: 0, factory: 3, slot: null, key: "B_HQ",
      names: { us: "Headquarters", fr: "Quartier général", sc: "司令部" }, price: 0, hp: 60, speed: 0 },
    { id: "Building_BatimentDepot", kind: "buildings", nation: 0, factory: 3, slot: null, key: "B_DEPOT",
      names: { us: "Supply depot", fr: "Dépôt de ravitaillement", sc: "补给站" }, price: 0, hp: 30, speed: 0 },
    { id: "Building_CaserneLeurre", kind: "buildings", nation: 0, factory: 3, slot: null, key: "B_DECOY",
      names: { us: "Decoy barracks", fr: "Caserne factice", sc: "假兵营" }, price: 5, hp: 5, speed: 0 },
    { id: "Building_DefenseMaginotFR", kind: "buildings", nation: 2, factory: 3, slot: null, key: "B_MAGINOT",
      names: { us: "Maginot line", fr: "Ligne Maginot", sc: "马奇诺防线" }, price: 30, hp: 80, speed: 0 },
  ];
  const FAKE_TYPES = {  // the game's type of each, on its card (TypeUnitHintToken)
    M4_Sherman: { us: "Advanced Medium Tank", fr: "Char moyen avancé" }, M3A1_Stuart: { us: "Light Tank", fr: "Char léger" },
    Panzer_IV_G: { us: "Medium Tank", fr: "Char moyen" }, Type97_ChiHa: { us: "Medium Tank", fr: "Char moyen" },
    Soldat_US_Leger: { us: "Light Infantry", fr: "Infanterie légère" }, P40Warhawk: { us: "Fighter", fr: "Chasseur" } };
  const FAKE_DESC = {  // the game's own line for each, on its card (DescriptionUnitHintToken)
    M4_Sherman: "Enjoys greater firepower than common medium tanks. Can fire while moving. Can't go in woods.",
    Building_CaserneLeurre: "Decoy building: The building is booby-trapped to kill any unit trying to capture it!",
    Building_Headquarter: "May field engineers and receive supply convoys. Generates $1 every 4s." };
  const aboutOf = (address) => {  // the name a player knows (the game's, in capitals) and that line
    const u = units.find((x) => E + x.id === address);
    return u ? { game_name: u.names.us.toUpperCase(), desc: FAKE_DESC[u.id] || "" } : { game_name: "", desc: "" };
  };
  // units made in the Studio: copies of one of the above, kept per mod like src/studio.rndf holds them
  const newUnits = [];  // { mod, id, source, name, price, nation, factory }
  const fakeLooks = new Set(), fakePainted = new Set();  // units opened in Blender, units whose paint came back
  function fakeLook(address) {
    const pic = "gen\\ww2\\fake\\tsccombcs_combineddsctexture01.tgv";
    return { models: ["ww2\\res3d\\units\\fake\\" + address.split("/").pop().toLowerCase() + "lod0.ase2ndfbin"],
             textures: [pic], painted: fakePainted.has(address) ? [pic] : [], download: "https://www.blender.org/download/",
             blender: mode === "noblender" ? "" : "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe",
             opened: fakeLooks.has(address), new_unit: mine().some((n) => address === newAddress(n.id)),
             own_model: fakeModels.get(address) || null };
  }
  const fakeModels = new Map();  // a new unit's own model (model_import): what the report says
  const FAKE_IMPORT = { file: "Tank Abrams.3ds", vertices: 17122, triangles: 13828, draws: 5, missing: [],
                        parts: { Main_Body: "hull", Main_Turre: "turret", Main_Barre: "gun", Minigun: "turret",
                                 Main_Wheel: "hull", Track: "hull" } };
  // a made-up tank for the 3D preview (three boxes with a striped picture), as a .gltf in a data: address; its paint
  // (after Bring back) is the same picture in red. ?preview=<url of a .glb> shows that model instead.
  const fakeShot = (base, stripe) => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const ctx = c.getContext("2d");
    ctx.fillStyle = base; ctx.fillRect(0, 0, 64, 64);
    ctx.fillStyle = stripe; for (let x = 0; x < 64; x += 16) ctx.fillRect(x, 0, 6, 64);
    return c.toDataURL("image/png");
  };
  function fakeModelUrl() {
    const boxes = [[-1.6, 0, -0.9, 1.6, 0.7, 0.9], [-0.7, 0.7, -0.6, 0.6, 1.15, 0.6], [0.6, 0.85, -0.08, 2.2, 1.0, 0.08]];
    const pos = [], uv = [], idx = [];
    for (const [x0, y0, z0, x1, y1, z1] of boxes) {
      for (const f of [[[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]], [[x1, y0, z0], [x0, y0, z0], [x0, y1, z0], [x1, y1, z0]],
        [[x0, y1, z1], [x1, y1, z1], [x1, y1, z0], [x0, y1, z0]], [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]],
        [[x1, y0, z1], [x1, y0, z0], [x1, y1, z0], [x1, y1, z1]], [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]]]) {
        const b = pos.length / 3;
        for (const p of f) pos.push(...p);
        uv.push(0, 1, 1, 1, 1, 0, 0, 0);
        idx.push(b, b + 1, b + 2, b, b + 2, b + 3);
      }
    }
    const f32 = new Float32Array([...pos, ...uv]), u16 = new Uint16Array(idx);
    const bytes = new Uint8Array(f32.byteLength + u16.byteLength);
    bytes.set(new Uint8Array(f32.buffer), 0);
    bytes.set(new Uint8Array(u16.buffer), f32.byteLength);
    const doc = { asset: { version: "2.0" },
      buffers: [{ byteLength: bytes.length, uri: "data:application/octet-stream;base64," + btoa(String.fromCharCode(...bytes)) }],
      bufferViews: [{ buffer: 0, byteOffset: 0, byteLength: pos.length * 4 }, { buffer: 0, byteOffset: pos.length * 4, byteLength: uv.length * 4 },
        { buffer: 0, byteOffset: f32.byteLength, byteLength: u16.byteLength }],
      accessors: [{ bufferView: 0, componentType: 5126, count: pos.length / 3, type: "VEC3", min: [-1.6, 0, -0.9], max: [2.2, 1.15, 0.9] },
        { bufferView: 1, componentType: 5126, count: uv.length / 2, type: "VEC2" },
        { bufferView: 2, componentType: 5123, count: idx.length, type: "SCALAR" }],
      images: [{ uri: fakeShot("#6b6a3c", "#55542e") }], textures: [{ source: 0 }],
      materials: [{ name: "Fake", pbrMetallicRoughness: { baseColorTexture: { index: 0 }, metallicFactor: 0, roughnessFactor: 0.8 },
        doubleSided: true, extras: { rusemod_texture: "gen\\ww2\\fake\\tsccombcs_combineddsctexture01.tgv" } }],
      meshes: [{ name: "fake", primitives: [{ attributes: { POSITION: 0, TEXCOORD_0: 1 }, indices: 2, material: 0 }] }],
      nodes: [{ name: "fake", mesh: 0 }], scenes: [{ nodes: [0] }], scene: 0 };
    return "data:model/gltf+json;base64," + btoa(JSON.stringify(doc));
  }
  // each unit's build-menu card: the game's (a grey stand-in) or the one "Use this view as the card" saved
  const fakeCards = new Map();
  const fakeCard = (address) => {
    const own = fakeCards.get(address);
    if (own) return { texture: "gen\\ww2\\res2d\\texanimationuniticone\\eu\\fake.tgv", width: 360, height: 184, url: own, own: true };
    const c = document.createElement("canvas");
    c.width = 360; c.height = 184;
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#8a96a0"; ctx.fillRect(0, 0, 360, 184);
    ctx.fillStyle = "#3d4650"; ctx.fillRect(110, 90, 140, 50);
    return { texture: "gen\\ww2\\res2d\\texanimationuniticone\\eu\\fake.tgv", width: 360, height: 184, url: c.toDataURL(), own: false };
  };
  const newAddress = (id) => E + id;
  const safeName = (name) => name.normalize("NFKD").replace(/[^\x00-\x7f]/g, "").replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  const home = "C:/Users/You/AppData/Local/RUSE Mod Platform/mods/";
  const mods = [{ path: home + "sherman-test", name: "sherman-test" }];  // sample data for the preview only
  let checkProblems = [{ file: "maps/SuperCrossRoads4/terrain.toml", set_aside: true,
    problem: "maps/SuperCrossRoads4/terrain.toml: stroke 1: the water brush needs level" }];
  const fakeRoads = {};  // the made-up mod's new roads, per map
  const fakeTakeOut = {};  // the made-up mod's roads.toml take_out, per mod and map
  // the made-up maps' own bridge kinds (rusemod.bridges.kinds): the Tunisian one has none, so the dock says so
  const bridgeKind = (name, placed, metres, roads) => ({ type: `TypeWarrior/${name}`, name, placed, length: Math.round(metres * 260),
    turn: 90, least: Math.ceil(metres * 260 * 0.9), most: Math.floor(metres * 260 * 2), lift: -640, roads });
  const fakeBridges = {
    TwoIslands: [bridgeKind("Pont_Italie_01_TangeantFloor", 6, 42, true), bridgeKind("Pont_Italie_02_TangeantFloor", 4, 39, false),
      bridgeKind("Pont_Italie_03", 0, 30, false)],
    SuperCrossRoads4: [bridgeKind("Pont_Metallique_02_TangeantFloor", 5, 41, true)],
    M02_Tunisie: [],
  };
  // where a made-up road crosses the sea round the island (fakeGround's heights): runs of water, a bank each end
  const fakeHeight = (pack, x, y) => {
    const u = x / 1310720, v = y / 1310720, r = Math.hypot(u - 0.5, v - 0.5) * 2.1, seed = pack.length;
    return Math.max(0, 48000 * (1 - r * r) + 7000 * Math.sin(u * (11 + seed)) * Math.cos(v * 9) + 3000 * Math.sin((u + v) * 31));
  };
  function fakeCrossings(pack, points) {
    const out = [], step = 800, bank = 2000, wet = [];
    for (let i = 0; i + 1 < points.length; i++) {
      const [ax, ay] = points[i], [bx, by] = points[i + 1], n = Math.max(1, Math.round(Math.hypot(bx - ax, by - ay) / step));
      for (let k = 0; k < n; k++) { const x = ax + (bx - ax) * k / n, y = ay + (by - ay) * k / n; wet.push([x, y, fakeHeight(pack, x, y) < 11000]); }
    }
    for (let i = 0; i < wet.length;) {
      if (!wet[i][2]) { i++; continue; }
      const s = i;
      while (i < wet.length && wet[i][2]) i++;
      const a = wet[Math.max(0, s - Math.round(bank / step))], b = wet[Math.min(wet.length - 1, i - 1 + Math.round(bank / step))];
      if (i - s >= 2) out.push([a[0], a[1], b[0], b[1]].map(Math.round));
    }
    return out;
  }
  // "Check this map": made-up findings from the made-up mod's roads (rusemod.mapcheck's kinds), or nothing found
  let checkPack = null;
  function fakeFindings(pack) {
    const f = (key, level, say, data) => ({ key, level, say, data, fix: null });
    const roads = fakeRoads[pack] || [];
    if (!roads.length) return [f("map", "ok", "mc_ok", {})];
    const [x, y] = roads[0][roads[0].length - 1].map(Math.round), [sx, sy] = roads[0][0].map(Math.round);
    const out = [f("pieces", "fail", "mc_cut_off", { units: "vehicles", sub: 0, circles: 3, metres: 41, x: 640000, y: 905000 }),
      f("join", "info", "mc_road_unjoined", { road: 1, x, y }),
      f("object", "info", "mc_object_on_road", { type: "TypeWarrior/MairieNormande", name: "MairieNormande", group: "building", road: 1, x: sx, y: sy })];
    for (const [n, line] of roads.entries()) {
      for (const [x0, y0, x1, y1] of fakeCrossings(pack, line)) {
        out.splice(1, 0, f("bridge", "fail", "mc_bridge_closed", { units: "infantry", road: n + 1, x: Math.round((x0 + x1) / 2), y: Math.round((y0 + y1) / 2) }));
      }
    }
    return out;
  }
  let current = mode === "nomod" ? null : mods[0].path;
const maps = [{ path: home + "maps/d-day-big", name: "d-day-big" }];  // the Maps tab's own list (preview only)
let currentMap = mode === "nomod" ? null : maps[0].path;
const mapsView = () => ({ mods: maps.slice(), kind: "map", current: currentMap });
  const edits = new Map();  // `${mod}|${address}|${prop}|${how}|${via}` -> value, like the mod's src/studio.rndf
  const terrains = new Map();  // `${mod}|${map pack}` -> strokes, like the mod's maps/<pack>/terrain.toml
  const placed = new Map();    // `${mod}|${map pack}` -> placed objects, like the mod's maps/<pack>/scenery.toml
  const erased = new Map();    // `${mod}|${map pack}` -> its circles to erase, the same file's [[erase]] tables
  const editKey = (address, prop, how, via) => `${current}|${address}|${prop}|${how || ""}|${how === "own" ? via : ""}`;
  if (current) edits.set(editKey(E + "M4_Sherman", "ProductionTime"), 1);  // a cheap, fast Sherman, as in the owner's test
  const mine = () => newUnits.filter((n) => n.mod === current);
  const BLAST = E + "M4_Sherman:Weapon.Blast";  // a part three units share
  const BLAST_OWNERS = ["M4_Sherman", "M3A1_Stuart", "Type97_ChiHa"];

  // ammunition: what a weapon fires; each unit has one mounted weapon here, and every ground unit its flags
  const A = "$/GFX/Everything/Ammo_";
  const ammo = [
    { id: "75mm_M3", ammoId: 1001, names: { us: "AP shell · Medium cal.", fr: "Obus AP · Moyen cal.", sc: "穿甲弹 · 中口径" },
      power: 40, range: 104000, users: ["M4_Sherman", "M3A1_Stuart"], group: "ap" },
    { id: "75mm_KwK40", ammoId: 1002, names: { us: "AP shell · Long 75", fr: "Obus AP · 75 long", sc: "穿甲弹 · 长身管75" },
      power: 55, range: 117000, users: ["Panzer_IV_G"], group: "ap" },
    { id: "MG_Cal30", ammoId: 1048, names: { us: "Machine-gun · .30 cal.", fr: "Mitrailleuse · cal. 30", sc: "机枪 · .30口径" },
      power: 2, range: 52000, users: ["Soldat_US_Leger", "P40Warhawk", "Type97_ChiHa"], group: "mg" },
  ];
  const newAmmo = [];  // { mod, id, source, name }: copies made here, like the new units
  const ammoAddress = (id) => A + id;
  const myAmmo = () => newAmmo.filter((n) => n.mod === current);
  const ammoName = (a, lang) => lang === "base" ? "Ammo_" + a.id : (a.names[lang] || a.names.us);
  const nationsOf = (a, lang) => [...new Set(a.users.map((id) => units.find((x) => x.id === id).nation))].sort()
    .map((n) => (nations[lang] || nations.us)[n]);
  const flags = { M4_Sherman: [10, 11, 21, 22, 55], M3A1_Stuart: [10, 11, 21, 22, 55], Panzer_IV_G: [10, 11, 21, 22, 55],
    Type97_ChiHa: [10, 11, 21, 22, 55] };
  // a few of the 105 (StudioApi.flags gives them all, rusemod/labels.toml [flags]): 91, which no unit carries, says it
  // does nothing in a unit's flags, and 62 warns of the crash
  const knownFlags = [
    { flag: 1, count: 54, examples: ["M7 Priest", "Wespe", "Type 4 Ha-To"], meaning: {
      us: "Artillery: fires indirectly at what others spot; works on any unit, tested (artillerie)",
      fr: "Artillerie : tir indirect sur ce que d'autres repèrent ; marche sur toute unité, testé (artillerie)",
      sc: "炮兵：对友军发现的目标进行间接射击；对任何单位都有效，已实测 (artillerie)" } },
    { flag: 10, count: 454, examples: ["M4 Sherman", "Infantry", "P-40 Warhawk"], meaning: {
      us: "Can take damage, so it can be picked as something to shoot (blessable)",
      fr: "Peut subir des dégâts, donc être choisi comme cible (blessable)", sc: "可受伤害，因此可被选为射击目标 (blessable)" } },
    { flag: 11, count: 155, examples: ["M4 Sherman", "M3A1 Stuart", "Panzer IV"], meaning: {
      us: "Can't enter woods; take 11, 21 and 55 off together to let a vehicle in, tested (blocage_foret)",
      fr: "N'entre pas en forêt ; retirer 11, 21 et 55 ensemble pour y faire entrer un véhicule, testé (blocage_foret)",
      sc: "不能进入树林；同时去掉 11、21 和 55 可让车辆进入，已实测 (blocage_foret)" } },
    { flag: 21, count: 262, examples: ["M4 Sherman", "Infantry", "Panzer IV"], meaning: {
      us: "Fighting unit: counted in end-of-game statistics; see 11 for woods (combattant)",
      fr: "Unité de combat : comptée dans les statistiques de fin de partie ; voir 11 pour les forêts (combattant)",
      sc: "作战单位：计入战后统计；树林相关见 11 (combattant)" } },
    { flag: 22, count: 407, examples: ["M4 Sherman", "Infantry", "P-40 Warhawk"], meaning: {
      us: "Takes the player's orders; scripts take it off to lock a unit (controlable)",
      fr: "Obéit aux ordres du joueur ; les scripts le retirent pour bloquer une unité (controlable)",
      sc: "接受玩家命令；脚本去掉它来锁定单位 (controlable)" } },
    { flag: 55, count: 55, examples: ["M4 Sherman", "M3A1 Stuart", "Panzer IV"], meaning: {
      us: "Tank; see 11 for letting a vehicle into woods (tank)", fr: "Char ; voir 11 pour faire entrer un véhicule en forêt (tank)",
      sc: "坦克；让车辆进入树林见 11 (tank)" } },
    { flag: 62, count: 18, examples: ["GMC truck", "GMC construction truck"], meaning: {
      us: "Truck; WARNING: crashes the game at match start on anything but a truck (truck)",
      fr: "Camion ; ATTENTION : fait planter le jeu en début de partie sur tout ce qui n'est pas un camion (truck)",
      sc: "卡车；警告：加在卡车以外的单位上，游戏会在对局开始时崩溃 (truck)" } },
    { flag: 72, count: 63, examples: ["P-40 Warhawk", "Spitfire"], meaning: {
      us: "Sees through obstacles: terrain and scenery; aircraft have it, untried on ground units (vision_no_obstacle)",
      fr: "Voit à travers les obstacles : relief et décor ; les avions l'ont, jamais essayé sur les unités au sol (vision_no_obstacle)",
      sc: "无视障碍物：地形和场景物体不挡视线；飞机具有，地面单位尚未测试 (vision_no_obstacle)" } },
    { flag: 91, count: 0, examples: [], meaning: {
      us: "Camouflaged, by the ruse card: the game sets it while playing; in a unit's flags it does nothing, tested (is_camoufle)",
      fr: "Camouflé, par la carte de ruse : le jeu le pose en cours de partie ; dans les drapeaux d'une unité, sans effet, testé (is_camoufle)",
      sc: "伪装，来自计谋卡：游戏在对局中设置；放在单位的标志位里无效，已实测 (is_camoufle)" } },
  ];
  // what a unit or building is for, as StudioApi.group_of says
  const GROUPS = ["hq", "money", "factory", "fort", "fake", "barracks", "armor", "antitank", "artillery", "prototype",
    "airfield", "turret", "other"];
  const groupOf = (u) => u.kind === "buildings"
    ? (/Leurre|Fake/.test(u.id) ? "fake" : /Headquarter/.test(u.id) ? "hq" : /BatimentAdministratif|Depot/.test(u.id)
      ? "money" : /Defense|Def_|ArtillerieField|PosteAlerte/.test(u.id) ? "fort" : "factory")
    : ({ 8: "barracks", 10: "armor", 11: "antitank", 13: "artillery", 12: "prototype", 9: "airfield", 3: "turret" })[u.factory] || "other";
  const nameOf = (u, lang) => lang === "base" ? E.slice(17) + u.id : (u.names[lang] || u.names.us);
  const label = (prop, lang) => lang === "base" ? prop : ((labels[lang] || labels.us)[prop] || prop);
  // the preview island's scenario: two zones, two starting points, a spawn and a town name (rusemod.scenario.view)
  const baseScenarios = () => ({ scenarios: [
        { file: "leveldesign.scenario", kind: "skirmish", entries: [{ name: "(2) Island", kind: "skirmish", titles: { us: "Island", fr: "Île" } }], zones: [
          { name: "zone_west", number: 0, points: [300000, 450000, 560000, 450000, 560000, 800000, 300000, 800000], triangles: [0, 1, 2, 0, 2, 3] },
          { name: "zone_port", number: 2, points: [560000, 450000, 760000, 450000, 760000, 800000, 660000, 860000, 560000, 800000], triangles: [0, 1, 2, 0, 2, 4, 2, 3, 4] },
          { name: "zone_east", number: 1, points: [760000, 450000, 1020000, 450000, 1020000, 800000, 760000, 800000], triangles: [0, 1, 2, 0, 2, 3] }],
          items: [{ kind: "StartingPoint", x: 430000, y: 620000, turn: 0, name: "", alliance: 1,
              cam: { path: [[730000, 420000, 200000], [580000, 620000, 90000]], look: [-0.857, 0, -0.514] } },
            { kind: "StartingPoint", x: 890000, y: 620000, turn: 0, name: "", alliance: 2,
              cam: { path: [[590000, 820000, 200000], [740000, 620000, 90000]], look: [0.857, 0, -0.514] } },
            { kind: "Spawn", x: 655000, y: 560000, turn: 0, name: "", camp: -1, what: "DalleBatimentDepot", trucks: 25, unit_kind: "buildings", group: "depot", icon: "depot" },
            { kind: "Spawn", x: 655000, y: 420000, turn: 0, name: "depot", camp: -1, what: "Unit_M4_Sherman", unit_kind: "ground", nation: 0, group: "armor", icon: "tank" },
    { kind: "Spawn", x: 640000, y: 400000, turn: 0, name: "", camp: 2, what: "Batiment_QG_GER", unit_kind: "buildings", nation: 1, group: "hq", icon: "hq" },
    { kind: "Spawn", x: 670000, y: 400000, turn: 0, name: "", camp: 1, what: "Avion_P47", unit_kind: "air", nation: 0, icon: "plane" },
    // one of each kind of icon, in a row south of the island's middle (the preview's check of every picture)
    ...["soldier", "truck", "at_gun", "howitzer", "aa_gun", "armor_base", "airfield", "barracks", "at_base", "art_base",
        "proto_base", "atomic", "hq2", "admin", "bunker_at", "bunker_mg", "bunker_aa", "bunker_art", "bunker_fort", "bunker_op"]
      .map((icon, k) => ({ kind: "Spawn", x: 520000 + (k % 10) * 30000, y: 760000 + Math.floor(k / 10) * 40000, turn: 0,
        name: icon, camp: 1 + (k % 2), what: "X_" + icon, nation: k % 7, icon, decoy: icon === "airfield",
        unit_kind: ["soldier", "truck", "at_gun", "howitzer", "aa_gun"].includes(icon) ? "ground" : "buildings" })),
            { kind: "LabelVille", x: 655000, y: 700000, turn: 0, name: "", text: "PortIsland", key: "PortIsland" }] },
        { file: "leveldesign_challenge.scenario", kind: "operation", entries: [{ name: "Challenge - Island", kind: "operation", titles: { us: "Harbour raid", fr: "Raid sur le port" } }], zones: [], items: [{ kind: "StartingPoint", x: 655000, y: 620000, turn: 0, name: "", alliance: 1 },
          // a depot a side holds and a zone its mission uses (the item details box: StudioApi.scenario_change)
          { kind: "Spawn", x: 720000, y: 600000, turn: 0, name: "depot_port", camp: 1, what: "DalleBatimentDepot", trucks: 30, unit_kind: "buildings", group: "depot", icon: "depot" },
          { kind: "CircularZone", x: 655000, y: 500000, turn: 0, name: "zone_harbour", radius: 52000 },
          // a named point and a square zone its mission script uses (Add a name or zone, the Named spots layer)
          { kind: "Name", x: 600000, y: 560000, turn: 0.5, turns: true, name: "WP_Landing_01" },
          { kind: "RectangleZone", x: 700000, y: 470000, turn: 0.3, turns: true, name: "zone_beach", width: 90000, height: 40000 }],
          // its mission's camps (StudioApi._scenario_owners_of, rusemod.missions), as M03_Italie's first chapter has them
          owners: [{ camp: -1, kind: "neutral" }, { camp: 0, kind: "player", nation: 0, team: 1 },
            { camp: 1, kind: "ai", nation: 1, team: 2 }, { camp: 2, kind: "ai", nation: 3, team: 1 },
            { camp: 3, kind: "ai", nation: 4, team: 2 }, { camp: 4, kind: "ai", nation: 2, team: 1 }] }] });
  // a scenario edited in a mod: moves and spawns per mod and map
  const scenarioEdits = new Map();
  const playerCounts = new Map();
  function fakePlayers(pack) {
    const entry = { name: "(2) Island", players: 2, layouts: [2], file: "leveldesign.scenario" };
    const mod = current ? playerCounts.get(`${current}|${pack}`) || null : null;
    const places = {};
    const s = withScenarioEdits(pack).scenarios.find((x) => x.file === entry.file);
    for (const it of s.items) if (it.kind === "StartingPoint") (places[it.alliance] = places[it.alliance] || new Set()).add(it.place || 1);
    const missing = [];
    if (mod) for (const t of [1, 2]) for (let q = 1; q <= mod / 2; q++) if (!(places[t] && places[t].has(q))) missing.push([t, q]);
    return { entries: [entry], mod, entry: null, missing, most: 8 };
  }
  function scenEdits(pack) {
    if (!current) throw new Error("Pick or make a mod first: scenario changes are saved in it.");
    const key = `${current}|${pack}`;
    if (!scenarioEdits.has(key)) scenarioEdits.set(key, { moves: [], spawns: [], starts: [], removes: [] });
    const e = scenarioEdits.get(key);
    e.removes = e.removes || [];
    return e;
  }
  // a start's warm-up camera turned `a` radians about (x, y), as StudioApi._turned_cam
  function turnCam(cam, x, y, a) {
    if (!a) return cam;
    const c = Math.cos(a), sn = Math.sin(a);
    return { ...cam, path: cam.path.map(([px, py, pz]) => [x + (px - x) * c - (py - y) * sn, y + (px - x) * sn + (py - y) * c, pz]),
      look: cam.look && [cam.look[0] * c - cam.look[1] * sn, cam.look[0] * sn + cam.look[1] * c, cam.look[2]] };
  }
  // the sample BATTLES menu for a mission's place (mission_steps): two groups under the game's headings, the first in
  // the mod's order and followed by a map from another of the game's lists
  const missionOrder = ["MP01", "MP02", "MP06"];
  function missionMenuOrder() {
    const titles = { MP01: "Blitz", MP02: "Tank Graveyard", MP06: "Frontline", MP25: "Pegasus Bridge",
      MP10: "Ardennes", MP12: "Bastogne" };
    const order = [...missionOrder.map((t) => ({ tracking: t, group: 0, pack: 97 })), { tracking: "MP25", group: 0, pack: 242 },
      { tracking: "MP10", group: 1, pack: 97 }, { tracking: "MP12", group: 1, pack: 97 }]
      .map((o) => ({ ...o, title: titles[o.tracking], this: o.tracking === "MP01" }));
    const at = missionOrder.indexOf("MP01");
    return { order, headings: { 0: "2 players", 1: "3-4 players" }, up: at === 0 ? "top" : null,
      down: at === 2 ? "pack" : null, mine: missionOrder.join() !== "MP01,MP02,MP06" };
  }
  function withScenarioEdits(pack) {
    const out = baseScenarios();
    const e = current && scenarioEdits.get(`${current}|${pack}`) || { moves: [], spawns: [], starts: [] };
    out.sectors_whole = Boolean(e.wholeMap);
    for (const s of out.scenarios) {
      if (e.wholeMap && s.zones.length) {  // sectors over the whole map (StudioApi.scenario_sectors): bands to the edges
        const band = (name, number, x0, x1) => ({ name, number, points: [x0, 0, x1, 0, x1, 1310720, x0, 1310720],
          triangles: [0, 1, 2, 0, 2, 3] });
        s.zones = [band("zone_west", 0, 0, 560000), band("zone_port", 2, 560000, 760000), band("zone_east", 1, 760000, 1310720)];
        s.sectors_whole = true;
      }
      s.items.forEach((it, i) => { it.item = i; if (it.kind === "StartingPoint") it.place = it.place || 1; });
      for (const r of e.removes || []) {
        if (r.file === s.file && s.items[r.item]) s.items[r.item].gone = true;
      }
      for (const c of e.changes || []) {  // the map's own items with a value changed (StudioApi.scenario_change)
        const it = c.file === s.file && s.items[c.item];
        if (!it) continue;
        it.game = Object.fromEntries(Object.keys(c.values).map((k) => [k, it[k]]));
        Object.assign(it, c.values);
      }
      for (const m of e.moves) {
        const it = m.file === s.file && s.items[m.item];
        if (!it) continue;
        if (it.cam) it.cam = turnCam({ ...it.cam, path: it.cam.path.map(([x, y, z]) => [x + m.x - it.x, y + m.y - it.y, z]) }, m.x, m.y, m.camera || 0);
        Object.assign(it, { x: m.x, y: m.y, moved: m.x !== it.x || m.y !== it.y || it.moved, camera: m.camera || 0 });
        if (m.rotation !== undefined && m.rotation !== null) Object.assign(it, { game_turn: it.turn, turn: m.rotation });
      }
      (e.places || []).forEach((p, n) => {  // new names, points and zones (StudioApi.scenario_place)
        if (p.file !== s.file) return;
        s.items.push({ ...p, turn: p.rotation || 0, mine: true, place: n, item: s.items.length,
          words: p.key ? newWords.get(p.key) : undefined });
      });
      (e.starts || []).forEach((st, n) => {
        if (st.file !== s.file) return;
        const place = 1 + Math.max(0, ...s.items.filter((it) => it.kind === "StartingPoint" && it.alliance === st.team).map((it) => it.place || 1));
        const model = s.items.find((it) => it.kind === "StartingPoint" && it.cam);
        const cam = model && turnCam({ ...model.cam, path: model.cam.path.map(([x, y, z]) => [x + st.x - model.x, y + st.y - model.y, z]) },
          st.x, st.y, st.camera || 0);
        s.items.push({ kind: "StartingPoint", x: st.x, y: st.y, turn: 0, name: "", alliance: st.team, place, mine: true,
          start: n, item: s.items.length, cam, camera: st.camera || 0 });
      });
      e.spawns.forEach((sp, n) => {
        if (sp.file === s.file) s.items.push({ kind: "Spawn", x: sp.x, y: sp.y, turn: 0, name: "", camp: sp.camp, what: sp.what,
          mine: true, spawn: n, item: s.items.length });
      });
    }
    return out;
  }
  // "Choose your language" (?fake=lang: the game set to French in Steam; it also opens on ?fake=noindex, a first start)
  Object.assign(words.us, { lang_pick_title: "Choose your language", lang_from_steam: "Your game's language in Steam",
    lang_from_pc: "Your PC's language", lang_pick_close: "Close", tip_lang_open: "Change the language.",
    lang_code_names: "Code names, for modding (screens in English)",
    tip_unit_type: "Show one type of unit, as the game names it: light, medium or heavy tank, fighter, bomber, recon…",
    lang_pick_help: "The Studio, its help and the game's unit names in your language. You can change it any time with the language button at the top." });
  Object.assign(words.fr, { lang_pick_title: "Choisissez votre langue", lang_from_steam: "La langue de votre jeu sur Steam",
    lang_from_pc: "La langue de votre PC", lang_pick_close: "Fermer", tip_lang_open: "Changer la langue.",
    lang_code_names: "Noms internes, pour le modding (écrans en anglais)",
    tip_unit_type: "Afficher un seul type d'unité, tel que le jeu le nomme : char léger, moyen ou lourd, chasseur, bombardier, reconnaissance…",
    lang_pick_help: "Le Studio, son aide et les noms des unités du jeu dans votre langue. Vous pouvez la changer à tout moment avec le bouton de langue en haut." });
  Object.assign(words.sc, { lang_pick_title: "选择你的语言", lang_from_steam: "你在 Steam 中的游戏语言",
    lang_from_pc: "你的电脑语言", lang_pick_close: "关闭", tip_lang_open: "更改语言。",
    lang_code_names: "内部名称（用于制作模组，界面为英语）",
    lang_pick_help: "用你的语言显示 Studio、帮助和游戏中的单位名称。随时可以用顶部的语言按钮更改。" });
  const words_ = (lang) => words[lang] || words.us;
  const modsView = () => ({ mods: mods.slice(), current });

  // one object's values, as StudioApi.unit() gives them
  function view(address, lang, cls, name, editable, whyNot, users, rowsByGroup, parts, uses, usedBy, share, via) {
    const g = groups[lang] || groups.us;
    const out = [];
    for (const [key, rows] of rowsByGroup) {
      out.push({ key, name: g[key], rows: rows.map(([prop, numbers, opts]) => {
        const o = opts || {};
        const list = Array.isArray(numbers);
        const nums = list ? numbers : [numbers];
        const values = o.text ? [o.text] : nums.map(String);
        const locked = ["DescriptorId", "Nationalite"].includes(prop);
        return { prop, label: label(prop, lang), group: key, values, numbers: o.text ? [null] : nums, list,
          type: o.type || "int32", editable: editable && !o.text && !locked, locked,
          edited: edits.get(editKey(address, prop, share ? "shared" : "")) ?? null,
          edited_own: share && share.via ? edits.get(editKey(address, prop, "own", via)) ?? null : null };
      }) });
    }
    return { address, class: cls, name, ...aboutOf(address), stable: true, shared: Boolean(share), owners: [], groups: out, parts, uses,
      used_by: usedBy, editable, why_not: whyNot, users, share: share || null, named: !address.includes(":"),
      can_copy: editable && !address.includes(":") && units.some((u) => E + u.id === address), new: null,
      can_copy_ammo: false, has_weapons: !address.includes(":") && cls !== "TAmmunition",
      can_upgrade: !address.includes(":") && cls !== "TAmmunition", in_game: true };
  }
  // the Upgrade box (StudioApi.upgrade): every made-up unit may be an upgrade of the first one, which has none
  const upgradeEdits = new Map();  // address -> the mod's parent (null: a unit of its own)
  const researchEdits = new Map();  // `${address}|${prop}` -> the mod's research price or time
  function upgradeOf(address, lang) {
    const all = units.map((u) => ({ address: E + u.id, name: lang === "base" ? u.id : u.names[lang] || u.names.us }));
    const gameParent = address === all[0].address ? null : all[0];
    const parent = upgradeEdits.has(address) ? all.find((x) => x.address === upgradeEdits.get(address)) || null : gameParent;
    const research = {};
    for (const [prop, labelText, game] of [["UpgradePrice", "Upgrade price", 25], ["UpgradeTime", "Upgrade time", 50]]) {
      const key = `${address}|${prop}`;
      research[prop] = { label: lang === "base" ? prop : labelText, game: gameParent ? game : null,
        value: researchEdits.has(key) ? researchEdits.get(key) : null };
    }
    return { address, parent, game_parent: gameParent, choices: all.filter((x) => x.address !== address),
      children: address === all[0].address ? all.slice(1, 3) : [], research };
  }

  function unit(address, lang, via) {
    const made = mine().find((n) => address === newAddress(n.id) || address.startsWith(newAddress(n.id) + ":"));
    if (made) {
      const inside = address.includes(":") ? address.slice(address.indexOf(":")) : "";
      const page = unit(made.source + inside, lang, via);
      const swap = (a) => a.startsWith(made.source + ":") ? newAddress(made.id) + a.slice(made.source.length) : a;
      page.address = address;
      page.parts = page.parts.map((p) => ({ ...p, address: p.shared ? p.address : swap(p.address) }));
      page.used_by = [];
      page.can_copy = false;
      if (!inside) {
        const src = units.find((x) => E + x.id === made.source);
        page.name = made.name;
        page.new = { source: made.source, source_name: nameOf(src, lang) };
        for (const g of page.groups) {
          for (const r of g.rows) {
            if (r.prop === "ProductionPrice") r.edited = edits.get(editKey(address, r.prop, "")) ?? Array(5).fill(made.price);
            if (r.prop === "NameInMenuToken") r.values = [made.name];
            if (r.prop === "Nationalite") r.values = [`${made.nation} (${(nations[lang] || nations.us)[made.nation]})`];
            if (r.prop === "Factory" && made.factory !== src.factory) r.edited = made.factory;
          }
        }
      }
      return page;
    }
    const copy = myAmmo().find((n) => ammoAddress(n.id) === address);
    const a = ammo.find((x) => ammoAddress(x.id) === (copy ? copy.source : address));
    if (a) {
      const page = view(address, lang, "TAmmunition", copy ? copy.name : ammoName(a, lang), true, "", copy ? 0 : a.users.length,
        [["identity", [["AmmunitionId", a.ammoId]]],
         ["weapon", [["Puissance", a.power], ["PorteeMaximale", a.range], ["TempsEntreDeuxTirs", 3.5, { type: "float32" }]]]],
        [], [], copy ? [] : a.users.map((id) => ({ address: E + id + ":MountedWeapon", path: "Ammunition" })));
      for (const r of page.groups.flatMap((g) => g.rows)) if (r.prop === "AmmunitionId") { r.editable = false; r.locked = true; }
      page.can_copy = false;
      page.can_copy_ammo = Boolean(current) && !copy;
      if (copy) page.new = { source: copy.source, source_name: ammoName(a, lang) };
      return page;
    }
    if (address === AMMO) {
      return view(AMMO, lang, "TAmmunition", "Ammo_75mm_M3", true, "", 3,
        [["weapon", [["Puissance", 40], ["PorteeMaximale", 104000], ["TempsEntreDeuxTirs", 3.5, { type: "float32" }]]]],
        [], [], [{ address: E + "M4_Sherman:WeaponManager.Turrets[class=TTurretTwoAxisDescriptor]", path: "Ammo" }]);
    }
    if (address === BLAST) {
      const owners = BLAST_OWNERS.map((id) => ({ address: E + id, name: nameOf(units.find((x) => x.id === id), lang) }));
      const from = owners.find((o) => o.address === via);
      const share = { owners, via: from ? { ...from, path: "Weapon.Blast" } : null };
      return view(address, lang, "TDamageDescriptor", "Weapon.Blast", true, "", 0,
        [["weapon", [["Puissance", 6], ["RayonDegats", 120]]]], [], [], [], share, via);
    }
    const base = address.split(":")[0];
    const u = units.find((x) => E + x.id === base) || units[0];
    if (address.includes(":")) {
      return view(address, lang, "TTurretTwoAxisDescriptor", address.split(":").pop(), true, "", 0,
        [["weapon", [["VitesseRotation", 45.5, { type: "float32" }], ["TirEnMouvement", 1, { type: "bool" }]]]],
        [], [{ address: AMMO, class: "TAmmunition" }], []);
    }
    const nationName = (nations[lang] || nations.base)[u.nation];
    return view(E + u.id, lang, u.kind === "air" ? "TAvionDescriptor" : u.kind === "infantry" ? "TInfanterieDescriptor" :
      "TUniteAuSolDescriptor", nameOf(u, lang), true, "", 0, [
      ["identity", [["Nationalite", u.nation, { text: `${u.nation} (${nationName})` }], ["DescriptorId", 187],
        ["ClassNameForDebug", 0, { text: "Unit_" + u.id }],
        ["NameInMenuToken", 0, { text: lang === "base" ? u.key : `${u.key} (${nameOf(u, lang)})` }],
        ...(flags[u.id] ? [["InitialFlagSet", flags[u.id], { type: "uint32" }]] : [])]],
      ["cost", [["ProductionPrice", Array(5).fill(u.price)], ["ProductionTime", 20]]],
      ["combat", [["SeuilMort", u.hp]]],
      ["movement", [["VitesseLineaire", u.speed, { type: "float32" }]]],
      ["vision", [["DetectionBase", 2500]]],
      ["menu", [["Factory", u.factory], ["PositionInMenu", u.slot]]],
    ], [{ address: E + u.id + ":WeaponManager.Turrets[class=TTurretTwoAxisDescriptor]", class: "TTurretTwoAxisDescriptor",
      shared: false }, { address: BLAST, class: "TDamageDescriptor", shared: true }],
    [{ address: AMMO, class: "TAmmunition" }], [{ address: "$/GFX/Everything/Menu_Armour_US", path: "Units[3]" }]);
  }

  // a unit's mounted weapon and what it fires (one per unit here), with the mod's ammo choice on top
  function weaponsOf(address, lang) {
    const made = mine().find((n) => address === newAddress(n.id));
    const u = units.find((x) => E + x.id === (made ? made.source : address));
    if (!u) return { weapons: [], choices: [] };
    const game = ammo.find((a) => a.users.includes(u.id)) || ammo[0];
    const weapon = address + ":MountedWeapon";
    const chosen = edits.get(editKey(weapon, "Ammunition", ""));
    const names = new Map(ammo.map((a) => [ammoAddress(a.id), ammoName(a, lang)]));
    for (const n of myAmmo()) names.set(ammoAddress(n.id), n.name);
    const current_ = chosen || ammoAddress(game.id);
    const whose = (addr) => { const c = myAmmo().find((n) => ammoAddress(n.id) === addr);
      const a = ammo.find((x) => ammoAddress(x.id) === (c ? c.source : addr)); return a ? nationsOf(a, lang) : []; };
    const choices = [...names].map(([addr, name]) => ({ address: addr, name, new: myAmmo().some((n) => ammoAddress(n.id) === addr),
      nations: whose(addr) }))
      .sort((x, y) => x.name.localeCompare(y.name));
    // the shot (muzzle flash and sound) follows the ammo, as in api.set_ammo: made-up names like the game's FX_Tir_*
    const shotOf = (addr) => { const c = myAmmo().find((n) => ammoAddress(n.id) === addr);
      const id = c ? c.source.split("/").pop() : addr.split("/").pop(); return /88|75|76/.test(id) ? "ObusAP Moyen" : "infanterie Moyen"; };
    const firing = firingOf(current_).map((id) => ({ address: E + id,
      name: nameOf(units.find((x) => x.id === id), lang) }));
    if (made) firing.push({ address, name: made.name });
    return { weapons: [{ address: weapon, name: "weapon_effet_tag1", ammo: { address: current_, name: names.get(current_) || current_ },
      game_ammo: ammoAddress(game.id), edited: Boolean(chosen), shot: shotOf(current_),
      range: rangeOf(current_), game_range: rangeOf(current_, true), firing,
      own_copy: myAmmo().some((n) => ammoAddress(n.id) === current_) && firing.length === 1 }], choices };
  }

  // an ammo's range (PorteeMaximale) with the mod's change (`game`: the game's; a copy: its source's), as api._range
  function rangeOf(addr, game) {
    const mine_ = game ? undefined : edits.get(editKey(addr, "PorteeMaximale", ""));
    if (mine_ !== undefined) return mine_;
    const c = myAmmo().find((n) => ammoAddress(n.id) === addr);
    const a = ammo.find((x) => ammoAddress(x.id) === (c ? c.source : addr));
    return a ? a.range : null;
  }

  // the game's units whose weapon fires `addr` now, with the mod's picks (api._firing)
  function firingOf(addr) {
    return units.filter((u) => {
      const game = ammo.find((a) => a.users.includes(u.id));
      const chosen = edits.get(editKey(E + u.id + ":MountedWeapon", "Ammunition", ""));
      return (chosen || (game ? ammoAddress(game.id) : null)) === addr;
    }).map((u) => u.id);
  }

  // The Maps view: a made-up island, packed like rusemod.terrain (uint16 positions over the bounds, zlib, base64)
  // (titles: what the game's menus call each map, as the game has them)
  const fakeMaps = [
    { pack: "TwoIslands", names: ["(6) Centre de gravite", "Challenge - 1v3 Centre de Gravite (Maginot)"],
      paths: ["TwoIslands"], file: "DataMapTwoIslands_v09.dat", kinds: ["skirmish", "operation"],
      titles: { us: ["Centre of Gravity", "The Maginot Line"], fr: ["Centre de gravité", "Ligne Maginot"],
                sc: ["引力中心", "马奇诺防线"] } },
    { pack: "SuperCrossRoads4", names: ["(2) Blitz", "Challenge - 1v1 39 Blitz_2 (Anzio)"], paths: ["SuperCrossRoads4"],
      file: "DataMapSuperCrossRoads4_v09.dat", kinds: ["skirmish", "operation", "test"],
      titles: { us: ["Blitz", "Anzio"], fr: ["Blitz", "Anzio"], sc: ["闪电战", "安齐奥"] } },
    { pack: "M02_Tunisie", names: ["M02_Tunisie_chapter1", "M02_Tunisie_chapter2"], paths: ["M02_Tunisie"],
      file: "DataMapM02_Tunisie_v09.dat", kinds: ["campaign"],
      titles: { us: ["2. TAKING COMMAND!", "3. KASSERINE PASS"], fr: ["2. AUX COMMANDES !", "3. PASSE DE KASSERINE"],
                sc: ["2. 接管指挥权！", "3. 卡塞林山口"] } },
  ].map((m) => ({ ...m, found: true }));

  async function packed(typed) {
    const stream = new Blob([typed]).stream().pipeThrough(new CompressionStream("deflate"));
    const bytes = new Uint8Array(await new Response(stream).arrayBuffer());
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }

  // A made-up village in the island's middle, a wood to its north and a few carts about.
  function fakeScenery(pack) {
    const types = [["MairieNormande", "building", "COC/Normandie/Batiments_Villes_Villages", ""],
      ["TownHouseB2_Haut", "building", "COC/Normandie/BatimentsMorceaux/TownHouseB/B2", ""],
      ["Charette_1", "prop", "Props/Ferme", ""], ["Chene_02", "vegetation", "Vegetation/Arbres", ""]];
    const items = { building: [], prop: [], vegetation: [] }, c = 655360, seed = pack.length;
    for (let k = 0; k < 40; k++) {
      const a = k * 2.4, r = 9000 + 1500 * k;
      items.building.push(k ? 1 : 0, Math.round(c + r * Math.cos(a)), Math.round(c + r * Math.sin(a)), a, k ? 1 : 1.5);
    }
    for (let k = 0; k < 30; k++) items.prop.push(2, c + 20000 + 700 * k, c + 30000 + (k % 5) * 900, k * 0.7, 1);
    for (let k = 0; k < 900; k++) {
      const u = (k * 7919 + seed) % 97 / 97, v = (k * 104729) % 89 / 89;
      items.vegetation.push(3, Math.round(c - 90000 + u * 180000), Math.round(c - 200000 + v * 90000), k, 0.8 + (k % 5) / 10);
    }
    // with their names and what they are in each language (rusemod.scenerynames; English, French and German here,
    // the others fall back to English)
    const palette = [["TypeWarrior/MairieNormande", "MairieNormande", "building", "COC/Normandie/Batiments_Villes_Villages", 1,
        { us: "Town hall (Normandy)", fr: "Mairie (Normandie)", ger: "Rathaus (Normandie)" },
        { us: "town building", fr: "bâtiment de ville", ger: "Stadtgebäude" }],
      ["TypeWarrior/TownHouseB2_Haut", "TownHouseB2_Haut", "building", "COC/Normandie/BatimentsMorceaux/TownHouseB/B2", 39,
        { us: "Town house B 2 high", fr: "Maison de ville B 2 haut", ger: "Stadthaus B 2 hoch" },
        { us: "building piece", fr: "élément de bâtiment", ger: "Gebäudeteil" }],
      ["TypeWarrior/Charette_1", "Charette_1", "prop", "Props/Ferme", 30, { us: "Cart 1", fr: "Charrette 1", ger: "Karren 1" },
        { us: "farm prop", fr: "objet de ferme", ger: "Hofgegenstand" }],
      ["TypeWarrior/Cotentin_PanierOsier1", "Cotentin_PanierOsier1", "prop", "Props/Ville", 4,
        { us: "Wicker basket 1 (Cotentin)", fr: "Panier en osier 1 (Cotentin)", ger: "Weidenkorb 1 (Cotentin)" },
        { us: "town prop", fr: "objet de ville", ger: "Stadtgegenstand" }],
      ["TypeWarrior/Chene_02", "Chene_02", "vegetation", "Vegetation/Arbres", 12000, { us: "Oak 2", fr: "Chêne 2", ger: "Eiche 2" },
        { us: "tree", fr: "arbre", ger: "Baum" }]];
    return { types, items, palette, groups: { building: { shown: 40, total: 40 }, prop: { shown: 30, total: 30 },
      vegetation: { shown: 900, total: 12000 } } };
  }

  async function fakeGround(pack, lod) {
    const n = lod === "highdef" ? 257 : 129, Q = 32767, size = 1310720, top = 60000, sea = 11000;
    const seed = pack.length;
    const h = (u, v) => {
      const r = Math.hypot(u - 0.5, v - 0.5) * 2.1;
      return Math.max(0, 48000 * (1 - r * r) + 7000 * Math.sin(u * (11 + seed)) * Math.cos(v * 9)
        + 3000 * Math.sin((u + v) * 31));
    };
    const pos = new Uint16Array(n * n * 3), nrm = new Uint8Array(n * n * 3), wat = new Uint16Array(n * n);
    const step = size / (n - 1);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const k = j * n + i, u = i / (n - 1), v = j / (n - 1), z = Math.min(top, h(u, v));
        pos.set([Math.round(u * Q), Math.round(v * Q), Math.round(z / top * Q)], 3 * k);
        wat[k] = Math.round(sea / top * Q);
        const dx = (h(u + 1 / (n - 1), v) - h(u - 1 / (n - 1), v)) / (2 * step);
        const dy = (h(u, v + 1 / (n - 1)) - h(u, v - 1 / (n - 1))) / (2 * step);
        const len = Math.hypot(dx, dy, 1);
        nrm.set([(-dx / len + 1) * 127.5, (-dy / len + 1) * 127.5, (1 / len + 1) * 127.5].map(Math.round), 3 * k);
      }
    }
    const tri = [], wtri = [];
    for (let j = 0; j < n - 1; j++) {
      for (let i = 0; i < n - 1; i++) {
        const a = j * n + i, b = a + 1, c = a + n, d = c + 1;
        for (const t of [[a, b, c], [b, d, c]]) {  // wound like the game's meshes, so the top is the lit side
          tri.push(...t);
          if (t.some((x) => pos[3 * x + 2] < wat[x])) wtri.push(...t);
        }
      }
    }
    return { pack, lod, bounds: [0, 0, 0, size, size, top], q_max: Q, vertices: n * n, triangle_count: tri.length / 3,
      positions: await packed(pos), normals: await packed(nrm), water_heights: await packed(wat),
      triangles: await packed(new Uint32Array(tri)), water: await packed(new Uint32Array(wtri)), picture: islandPicture(h, sea) };
  }

  // A made-up ground picture for the island (north up, as the game's overview): sand by the sea, grass, a few fields
  // and a road, so Map Paint has something to paint on and to copy from in the preview
  function islandPicture(h, sea) {
    const N = 512, c = document.createElement("canvas");
    c.width = c.height = N;
    const ctx = c.getContext("2d"), img = ctx.createImageData(N, N);
    for (let j = 0; j < N; j++) {
      for (let i = 0; i < N; i++) {
        const u = i / N, v = j / N, z = h(u, v), k = 4 * (j * N + i);
        let rgb = z < sea ? [52, 92, 118] : z < sea + 2500 ? [196, 178, 128] : [92, 118, 62];
        if (z >= sea + 2500 && ((Math.floor(u * 14) + Math.floor(v * 11)) % 5 === 0)) rgb = [150, 128, 74];  // fields
        if (z >= sea && Math.abs(v - 0.5 - 0.08 * Math.sin(u * 7)) < 0.006) rgb = [150, 140, 120];  // a road
        const n = (Math.sin(i * 12.9898 + j * 78.233) * 43758.5453) % 1 * 14;  // a little grain
        img.data.set([rgb[0] + n, rgb[1] + n, rgb[2] + n, 255], k);
      }
    }
    ctx.putImageData(img, 0, 0);
    return c.toDataURL("image/png");
  }

  // Share your mod (words.toml share_*): the steps onto the supported-mods list, and an export's file
  Object.assign(words.us, {"share_mod": "Share your mod…", "share_title": "Share your mod", "share_lead": "Made a mod? Add it to the list and become a contributor.", "share_step_export": "Export it (Export mod… in the mod menu). The file says it was made with RUSE Studio.", "share_step_pr": "Press “Publish to the mod list”: the list's “Add my mod” form opens on GitHub, filled in from your file, and a .zip of your mod is in the folder that opens. Drag the .zip into the form.", "share_step_post": "Say what the mod does, what it changes and what its code does, then submit. An automatic check reads the file, and once we've tried the mod it's on the list in every player's Launcher.", "share_file": "File: {file} ({size} bytes)", "share_sha": "SHA-256: {sha}", "share_entry": "Its entry for index.toml (put the file's link in download):", "share_copy": "Copy the entry", "share_copied": "Copied: paste it into index.toml.", "share_open": "Open the mod list on GitHub", "share_discussions": "Open the Discussions", "share_publish": "Publish to the mod list", "share_published": "The form is open in your browser. Drag the .zip from the folder that opened into its “The mod file” box.", "share_credit": "Credit line: paste it wherever you share your mod.", "share_guidelines": "What the list accepts", "share_credit_copy": "Copy the line", "share_credit_copied": "Copied: paste it where you share your mod."});
  Object.assign(words.fr, {"share_mod": "Partager votre mod…", "share_title": "Partagez votre mod", "share_lead": "Vous avez fait un mod ? Ajoutez-le à la liste et devenez contributeur.", "share_step_export": "Exportez-le (Exporter le mod… dans le menu du mod). Le fichier indique qu'il a été fait avec RUSE Studio.", "share_step_pr": "Appuyez sur « Publier sur la liste des mods » : le formulaire « Add my mod » de la liste s'ouvre sur GitHub, rempli à partir de votre fichier, et un .zip de votre mod se trouve dans le dossier qui s'ouvre. Glissez le .zip dans le formulaire.", "share_step_post": "Dites ce que fait le mod, ce qu'il change et ce que fait son code, puis envoyez. Une vérification automatique lit le fichier, et une fois le mod essayé, il est dans la liste du Launcher de chaque joueur.", "share_file": "Fichier : {file} ({size} octets)", "share_sha": "SHA-256 : {sha}", "share_entry": "Son entrée pour index.toml (mettez le lien du fichier dans download) :", "share_copy": "Copier l'entrée", "share_copied": "Copié : collez-la dans index.toml.", "share_open": "Ouvrir la liste des mods sur GitHub", "share_discussions": "Ouvrir les Discussions", "share_publish": "Publier sur la liste des mods", "share_published": "Le formulaire est ouvert dans votre navigateur. Glissez le .zip du dossier ouvert dans sa case « The mod file ».", "share_credit": "Ligne de crédit : collez-la partout où vous partagez votre mod.", "share_guidelines": "Ce que la liste accepte", "share_credit_copy": "Copier la ligne", "share_credit_copied": "Copiée : collez-la là où vous partagez votre mod."});
  Object.assign(words.sc, {"share_mod": "分享你的模组…", "share_title": "分享你的模组", "share_lead": "做了模组？把它加入列表，成为贡献者。", "share_step_export": "将其导出（模组菜单中的“导出模组…”）。文件会注明它是用 RUSE Studio 制作的。", "share_step_pr": "点击“发布到模组列表”：列表的“Add my mod”表单会在 GitHub 上打开，并按你的文件填好；打开的文件夹里有你模组的 .zip。把 .zip 拖进表单。", "share_step_post": "写明模组做什么、改了什么、它的代码做什么，然后提交。自动检查会读取文件；我们试过之后，它就会出现在每位玩家 Launcher 的列表中。", "share_file": "文件：{file}（{size} 字节）", "share_sha": "SHA-256：{sha}", "share_entry": "它在 index.toml 中的条目（在 download 中填入文件链接）：", "share_copy": "复制条目", "share_copied": "已复制：请粘贴到 index.toml 中。", "share_open": "在 GitHub 上打开模组列表", "share_discussions": "打开 Discussions", "share_publish": "发布到模组列表", "share_published": "表单已在浏览器中打开。把打开的文件夹里的 .zip 拖到其“The mod file”栏中。", "share_credit": "署名行：在你分享模组的地方粘贴它。", "share_guidelines": "列表接受哪些内容", "share_credit_copy": "复制这一行", "share_credit_copied": "已复制：粘贴到你分享模组的地方。"});
  // the Bridges dock and "Check this map" (words.toml dock_bridges, bridges_*, check_*, mc_*)
  Object.assign(words.us, {"dock_bridges": "Bridges", "tip_dock_bridges": "The map's own bridge kinds: place one by hand, and see where new roads cross water (in gold).", "bridges_help": "Pick a kind, set its length and turn, then click the ground where the bridge's middle goes. Both ends should rest on dry bank.", "bridges_kind_info": "{n} on the map · {least} to {most} m", "bridges_roads_kind": "new roads' bridges", "bridges_no_floor": "not placed on this map: no floor to copy, so the build refuses it", "bridges_length": "Length {m} m", "tip_bridges_length": "How long the deck is, bank to bank: the map's own bridges are stretched from 0.9 to 2 times their model's length.", "tip_bridges_turn": "Which way the bridge runs, in degrees (- and = keys too).", "tip_bridges_undo": "Take the last bridge placed by hand off the map.", "bridges_count": "{n} placed by hand", "bridges_crossings": "{n} water crossing(s) on the new roads, in gold: the build puts a bridge of the new roads' kind on each.", "bridges_none": "{n} water crossing(s), but this map has no bridge kind of its own: no bridge can go there, and units can't cross", "bridges_none_map": "This map has no bridge kind of its own: no bridge can go on it, and units can't cross water on a new road.", "bridges_loading": "Reading the map's bridges…", "dock_check": "Check", "tip_dock_check": "Find what would go wrong on this map with your mod, before the game starts.", "check_run": "Check this map", "tip_check_run": "Builds your mod's changes to this map as Test in game would, in a folder removed afterwards, and lists what would go wrong: ground cut off, roads or bridges units can't use, road ends not joined, buildings on roads.", "check_running": "Checking: building your mod on this map (a minute or so)…", "check_found": "{n} thing(s) to look at. Click one with a place to see it on the map.", "check_stale": "Checked before your last change: check again to be sure.", "mc_ok": "Nothing found that would go wrong on this map.", "mc_build_failed": "The map couldn't be built, so it wasn't checked: {why}", "mc_cut_off": "Ground around ({x}, {y}), {metres} m across, is cut off for {units}: they can't reach it from the rest of the map, and an order onto it crashes the game.", "mc_road_closed": "Road {road}: {metres} m around ({x}, {y}) is ground {units} can't use.", "mc_bridge_closed": "The crossing at ({x}, {y}) is closed to {units}: they can't get from one bank to the other.", "mc_road_unjoined": "Road {road} ends at ({x}, {y}) without joining the road network. Supply trucks use the road network.", "mc_object_on_road": "{name} stands on road {road} at ({x}, {y}).", "mc_objects_more": "{n} more objects stand on the new roads.", "mc_units_infantry": "infantry", "mc_units_vehicles": "vehicles"});
  // the Erase brush (words.toml brush_erase, erase_*)
  Object.assign(words.us, {"dock_group_ground": "Ground & water", "tip_dock_group_ground": "Shape the ground, and put water on it or drain it.", "dock_group_zones": "Cover & movement", "tip_dock_group_zones": "Where units are hidden, and where they can go.", "dock_group_ways": "Roads & bridges", "tip_dock_group_ways": "Draw new roads, and place the map's own bridges.", "dock_group_nature": "Props & trees", "tip_dock_group_nature": "Place the map's own props and trees."});
  Object.assign(words.fr, {"dock_group_ground": "Terrain et eau", "tip_dock_group_ground": "Modelez le terrain, ajoutez de l'eau ou asséchez-la.", "dock_group_zones": "Couvert et mouvement", "tip_dock_group_zones": "Où les unités sont cachées, et où elles peuvent aller.", "dock_group_ways": "Routes et ponts", "tip_dock_group_ways": "Tracez de nouvelles routes et placez les ponts de la carte.", "dock_group_nature": "Objets et arbres", "tip_dock_group_nature": "Placez les objets et arbres de la carte."});
  Object.assign(words.sc, {"dock_group_ground": "地形与水", "tip_dock_group_ground": "塑造地形，添加或排干水域。", "dock_group_zones": "掩护与通行", "tip_dock_group_zones": "单位在哪里隐蔽，又能去哪里。", "dock_group_ways": "道路与桥梁", "tip_dock_group_ways": "绘制新道路，放置地图自带的桥梁。", "dock_group_nature": "道具与树木", "tip_dock_group_nature": "放置地图自带的道具和树木。"});
  Object.assign(words.us, {"brush_erase": "Erase", "tip_dock_erase": "Take the map's own trees and props away (buildings too, if you pick them).", "tip_brush_erase": "Drag over the map's own trees and props: the red circles are saved in the mod, and what they cover (tinted red) goes when the mod is built. Undo takes back the last drag.", "tip_erase_what": "What the circles take away. Each circle keeps what was picked when it was painted.", "erase_trees_note": "Where trees go, the ground opens to every unit and loses its forest cover (proven in the game).", "erase_buildings_note": "Where buildings go, the ground opens to every unit, as with trees (seen in the game).", "erase_none": "Pick at least one of trees, props and buildings.", "erase_size": "Size {m} m", "erase_count": "Circles on this map: {n}", "erase_really_clear": "Remove all {n} circles on this map? The map then keeps everything they would take.", "tip_erase_undo": "Take back the last circles painted (Ctrl+Z).", "tip_erase_clear": "Remove every circle this mod has on this map: the map keeps all its own scenery.", "erase_counting": "Counting what the circles take…", "erase_takes": "When the mod is built, the circles take: {list}", "erase_takes_none": "The circles cover nothing they may take.", "erase_refused": "The build would refuse these circles: {why}", "scenery_decal": "Ground marks"});
  Object.assign(words.fr, {"brush_erase": "Effacer", "tip_dock_erase": "Retirer les arbres et objets de la carte (les bâtiments aussi, si vous les choisissez).", "tip_brush_erase": "Glissez sur les arbres et objets de la carte : les cercles rouges sont enregistrés dans le mod, et ce qu'ils couvrent (teinté de rouge) disparaît à la construction du mod. Annuler reprend le dernier glissement.", "tip_erase_what": "Ce que les cercles retirent. Chaque cercle garde ce qui était choisi quand il a été peint.", "erase_trees_note": "Là où les arbres disparaissent, le sol s'ouvre à toutes les unités et perd son couvert forestier (vérifié en jeu).", "erase_buildings_note": "Là où les bâtiments disparaissent, le sol s'ouvre à toutes les unités, comme pour les arbres (vérifié en jeu).", "erase_none": "Choisissez au moins arbres, objets ou bâtiments.", "erase_size": "Taille {m} m", "erase_count": "Cercles sur cette carte : {n}", "erase_really_clear": "Supprimer les {n} cercles de cette carte ? La carte garde alors tout ce qu'ils auraient retiré.", "tip_erase_undo": "Reprendre les derniers cercles peints (Ctrl+Z).", "tip_erase_clear": "Supprimer tous les cercles de ce mod sur cette carte : la carte garde tout son décor.", "erase_counting": "Calcul de ce que retirent les cercles…", "erase_takes": "À la construction du mod, les cercles retirent : {list}", "erase_takes_none": "Les cercles ne couvrent rien qu'ils puissent retirer.", "erase_refused": "La construction refuserait ces cercles : {why}", "scenery_decal": "Marques au sol"});
  Object.assign(words.sc, {"brush_erase": "移除", "tip_dock_erase": "移除地图自带的树木和道具（如果选中，也包括建筑）。", "tip_brush_erase": "在地图自带的树木和道具上拖动：红色圆圈保存在模组中，圆圈覆盖的内容（显示为红色）会在构建模组时消失。撤销可取消最后一次拖动。", "tip_erase_what": "圆圈要移除的内容。每个圆圈保留绘制时所选的内容。", "erase_trees_note": "树木消失的地方，地面对所有单位开放，并失去森林掩护（已在游戏中验证）。", "erase_buildings_note": "建筑消失的地方，地面像树木一样对所有单位开放（已在游戏中验证）。", "erase_none": "请至少选择树木、道具或建筑中的一项。", "erase_size": "大小 {m} 米", "erase_count": "此地图上的圆圈：{n}", "erase_really_clear": "删除此地图上的全部 {n} 个圆圈？它们原本要移除的内容都会保留在地图上。", "tip_erase_undo": "撤销最后绘制的圆圈（Ctrl+Z）。", "tip_erase_clear": "删除此模组在此地图上的所有圆圈：地图保留其全部景物。", "erase_counting": "正在统计圆圈移除的内容…", "erase_takes": "构建模组时，圆圈将移除：{list}", "erase_takes_none": "圆圈没有覆盖任何可移除的内容。", "erase_refused": "构建会拒绝这些圆圈：{why}", "scenery_decal": "地面痕迹"});
  // what each made-up map's menus offer to copy (StudioApi._menu_entries)
  const FAKE_ENTRIES = {
    TwoIslands: [{ name: "(6) Centre de gravite", kind: "battles", titles: { us: "Centre of Gravity", fr: "Centre de gravité" } },
      { name: "Challenge - 1v3 Centre de Gravite (Maginot)", kind: "operation", titles: { us: "The Maginot Line", fr: "Ligne Maginot" } }],
    SuperCrossRoads4: [{ name: "(2) Blitz", kind: "battles", titles: { us: "Blitz", fr: "Blitz" } },
      { name: "Challenge - 1v1 39 Blitz_2 (Anzio)", kind: "operation", titles: { us: "Anzio", fr: "Anzio" } }],
    M02_Tunisie: [{ name: "M02_Tunisie_chapter1", kind: "campaign", titles: { us: "2. TAKING COMMAND!", fr: "2. AUX COMMANDES !" } },
      { name: "M02_Tunisie_chapter2", kind: "campaign", titles: { us: "3. KASSERINE PASS", fr: "3. PASSE DE KASSERINE" } }],
  };
  Object.assign(words.us, {"dup_kind": "What kind of new map", "dup_kind_battles": "Battles map", "dup_kind_battles_what": "Played in BATTLES: skirmish against the computer, and online with players who have it. Listed next to the original. Seen in the game.", "dup_kind_operation": "Operation", "dup_kind_operation_what": "A new Operation, at the end of OPERATIONS: the original's mission, briefing and objectives, on your copy of the map. Seen in the game.", "dup_kind_campaign": "Campaign chapter", "dup_kind_campaign_what": "A new chapter, at the end of the campaign: the original chapter's mission, cutscenes and dialog, on your copy of the map. The game opens a chapter once the one before it is finished. Not yet tried in the game.", "dup_kind_none": "This map has none."});
  // A map's menu pictures (words.toml map_picture, tip_map_picture, menu_*)
  Object.assign(words.us, {"map_picture": "Menu pictures…", "tip_map_picture": "This map's two pictures in the game's menus: pick your own, make them in Blender, or keep the game's own.", "menu_pics_title": "Menu pictures", "menu_pics_lead": "What the game's menus show for {map}: a big picture, and a 3D map with a white dot where each player starts.", "menu_big": "Big picture", "menu_wide": "3D map", "menu_own_file": "This map's own: {file}", "menu_game_own": "The game's own picture", "menu_pick": "Pick a PNG…", "tip_menu_pick": "Any PNG: a screenshot, or a picture made anywhere. It's cut to shape from its middle and scaled.", "menu_back": "Back to the game's own", "tip_menu_back": "Takes this map's own picture away (to the Recycle Bin): the game's own shows again.", "menu_dots": "White dots on the start points", "tip_menu_dots": "The build draws a white dot where each player starts, wherever the start points are when you build, so a moved start moves its dot. Leave it off for a picture with dots of its own.", "menu_blender_title": "Make your own in Blender", "menu_blender_how": "Blender opens with this map's own 3D model, both pictures' cameras set like the game's. Change anything you like, click Save menu pictures at the top of Blender, then Bring back here.", "menu_blender": "Make in Blender…", "tip_menu_blender": "Opens this map's scene in Blender (the first time takes a little while: the map's ground picture is made first).", "menu_no_blender": "Blender isn't found on this PC: get it free from blender.org.", "menu_bring_back": "Bring back", "tip_menu_bring_back": "Takes the pictures saved in Blender into this map.", "menu_fresh": "New scene", "tip_menu_fresh": "Makes this map's Blender scene again from the start; the old one goes to the Recycle Bin.", "menu_shared": "The game also shows these pictures for: {entries}. They change there too."});
  // each map's menu pictures in the preview (StudioApi.menu_pictures): drawn shapes for the pictures
  const fakeMenus = {};
  const fakeMenuState = (pack) => (fakeMenus[pack] = fakeMenus[pack] || { picture: null, wide_picture: null, start_dots: false,
    scene: false, saved: false });
  const svgUrl = (svg) => "data:image/svg+xml;utf8," + encodeURIComponent(svg);
  const fakeMenu = (pack) => {
    const s = fakeMenuState(pack), m = fakeMaps.find((x) => x.pack === pack) || {};
    const sky = s.picture ? "#8fb3d9" : "#b9c4cc", land = s.picture ? "#2f6db0" : "#6f8a4a";
    const big = svgUrl(`<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><rect width="320" height="110" fill="${sky}"/>`
      + `<rect y="110" width="320" height="70" fill="${land}"/><rect x="1" y="1" width="318" height="178" fill="none" stroke="#848684" stroke-width="2"/></svg>`);
    const dots = s.start_dots ? [[157, 28], [184, 42], [214, 51], [231, 56], [189, 77]].map(([x, y]) => `<ellipse cx="${x}" cy="${y}" rx="2.5" ry="1.3" fill="#fff"/>`).join("") : "";
    const top = s.wide_picture ? "#0d3a52" : "#5f7a3c";
    const wide = svgUrl(`<svg xmlns="http://www.w3.org/2000/svg" width="340" height="100"><polygon points="82,5 257,5 315,85 25,85" fill="${top}"/>`
      + `<rect x="25" y="85" width="290" height="10" fill="#3a2b1c"/>${s.wide_picture ? dots : '<ellipse cx="170" cy="45" rx="2.5" ry="1.3" fill="#fff"/>'}</svg>`);
    return { pictures: [{ key: "picture", file: s.picture, own: Boolean(s.picture), url: big, width: 640, height: 360 },
      { key: "wide_picture", file: s.wide_picture, own: Boolean(s.wide_picture), url: wide, width: 680, height: 200 }],
    start_dots: s.start_dots, new: Boolean(m.copy_of), shared: m.copy_of ? [] : ["Challenge - 1v1 39 Blitz_2 (Anzio) (operation)"],
    blender: "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe", scene: s.scene, saved: s.saved };
  };
  // Duplicate map's start: as it is, or Blank Terrain (words.toml dup_start_*; Blank Ocean taken out 2026-10-08)
  Object.assign(words.us, {"dup_start": "Start from", "dup_start_copy": "As it is", "dup_start_copy_what": "A full copy, with the changes made to {map} so far.", "dup_start_blank_terrain": "Blank Terrain", "dup_start_blank_terrain_what": "Flat land with no water and nothing on it: only the starting points. Add roads, buildings and the rest yourself. Not tested in the game yet.", "dup_start_battles_only": "Blank Terrain starts from a Battles map."});
  // New map from scratch (words.toml new_map_scratch, tip_new_map_scratch, scratch_what, dup_scratch_*, dup_base*)
  Object.assign(words.us, {"new_map_scratch": "New map: start from scratch…", "tip_new_map_scratch": "Make a new map that starts blank: flat land with only the starting points. You pick which game map it's built on.", "scratch_what": "Blank Terrain: flat land with nothing on it but the starting points.", "dup_scratch_title": "New map from scratch", "dup_scratch_lead": "Want to start from scratch? Your new map starts as Blank Terrain. Every new map sits on one of the game's maps, because the game can't load a map made from nothing: that map gives yours its size, its player count and its starting points, and nothing else. Pick which one under Built on.", "dup_base": "Built on", "dup_base_what": "Only its size, its player count and its starting points are kept.", "dup_scratch_go": "Make the map", "dup_done_blank": "{name}: a new map, {start} built on {map}. Change it like any map; Test in game plays it."});
  // Duplicate map (words.toml duplicate_map, dup_*, map_copy_of)
  Object.assign(words.us, {"duplicate_map": "Duplicate map", "tip_duplicate_map": "Make a new map from this one: a full copy with a name of its own, as a Battles map, an Operation or a campaign chapter. You then change the copy like any map.", "dup_lead": "Makes a new map: a full copy of {map} with a name of its own, in the game's menus next to the original. Everything you change on the copy (ground, buildings, roads, starting points, players) is the copy's alone: {map} stays as it is.", "dup_how": "How it works", "dup_how_own": "The copy gets its own map file, its own place in the game's menus and its name in every language. Its ids come from its name, so every PC with your map changes gets the very same map, and players who have it can play it together online.", "dup_how_edits": "Your changes to {map} so far come along, so the copy starts as you see it now.", "dup_how_where": "It's saved in your map changes ({folder}); Test in game and Export… take it along like any other change. Ranked games don't offer it.", "dup_how_new": "No map changes is picked, so a new one is made for it, named after it; Test in game and Export… take it along like any other change. Ranked games don't offer it.", "dup_how_tested": "New in this version and still early: tried in the game with 101 new maps at once, each listed and playing its own ground.", "dup_name": "Name in the menus", "dup_file": "Its files and folder: {file}", "dup_long": "Names over 35 characters get cut off in the game's menus.", "dup_entry": "Which one to copy", "dup_go": "Duplicate", "dup_done": "{name}: a new map, a copy of {map}. Change it like any map; Test in game plays it.", "map_copy_of": "new map · copy of {map}"});
  // a new unit's own model (words.toml model_*, tip_model_*)
  Object.assign(words.us, {"model_title": "Its own model", "model_how": "It uses the model of the unit it copies. Import a 3D model (.3ds, or .glb from Blender and most 3D tools) to give it one of its own: it's fitted to that unit's length (times Size), its turret on that unit's turret, and turns and drives the same way.", "model_import": "Import model…", "model_import_again": "Import another…", "tip_model_import": "Pick a .3ds (with its pictures beside it, or in the folder above) or a .glb. It's fitted to the copied unit and saved in your mod; Test in game shows it.", "model_size": "Size", "tip_model_size": "Its length over the copied unit's: 1 is as long; an M1 Abrams over a Sherman is 1.36.", "model_importing": "Fitting the model to the unit…", "model_done": "{file} is now this unit's model. Click Test in game to see it.", "model_own": "From {file}: {points} points, {triangles} triangles.", "model_turret": "Turning with the turret: {parts}. The rest moves with the hull.", "model_missing": "Pictures not found: {names}. Those parts show one flat colour. Put the pictures beside the model (or the folder above it) and import it again.", "model_remove": "Use the copied unit's model", "tip_model_remove": "Take its own model out of the mod: it looks like the unit it copies again."});
  // the Units tab's two ways in (words.toml start_*, pick_unit_new, tip_start_from, new_unit_next, model_want*)
  Object.assign(words.us, {"start_change": "Change a unit", "tip_start_change": "Pick a unit to change its values, or open it in Blender to repaint it.", "start_new": "New unit (import a model)", "tip_start_new": "Start a new unit from a game unit: it copies its values and moves the same way. Then import your own 3D model and change the rest.", "start_new_help": "Pick the unit to start from: your new unit copies its values, and your model turns and drives the way its model does. Tested with tanks so far.", "pick_unit_new": "Pick the unit your new one starts from, on the left.", "tip_start_from": "Start a new unit from this one.", "new_unit_next": "Your new unit starts as a copy of {name}. Give it a name, a price and a build menu, then Create: its page opens at Import model.", "model_want": "A model of your own goes on a new unit: make one from this unit, then Import model on its page. This unit stays as it is.", "model_want_button": "New unit from this one…", "tip_model_want": "Opens New unit on this page: a name, a price and a build menu. The new unit's page has Import model."});
  // the Economy tab (words.toml economy_*, tip_tab_economy, tip_economy_reset)
  Object.assign(words.us, { economy_tab: "Economy", economy_title: "Economy",
    tip_tab_economy: "Money, income, supply trucks, production limits and ruse cards, for every battle with this mod.",
    economy_help: "A change here is saved in the current mod at once, for every game mode (the game keeps these values twice: for its usual modes and for the Nuclear mode). From LittleGroove's Economy editor in RUSE Mod Manager. Tried in the game: the starting money and the ruse cards at the start; the rest not yet.",
    economy_buildings: "Supply depots and administration buildings are buildings: change their price, build time and strength on the Units tab, under Buildings.",
    economy_none: "The game index has none of the economy's values. Build it again in Settings.",
    economy_atomic: "Nuclear mode: {v} as the game has it (a change sets both)",
    tip_economy_reset: "Put the value back as the game has it, in every game mode.",
    economy_group_money: "Money and income", economy_group_supply: "Supply depots", economy_group_production: "Production",
    economy_group_cards: "Ruse cards", economy_group_computer: "Computer players", economy_group_decoys: "Decoys" });
  Object.assign(words.fr, { economy_tab: "Économie", economy_title: "Économie", economy_group_money: "Argent et revenus",
    economy_group_supply: "Dépôts de ravitaillement", economy_group_cards: "Cartes de ruse",
    economy_atomic: "Mode Nucléaire : {v} dans le jeu (un changement règle les deux)" });
  Object.assign(words.sc, { economy_tab: "经济", economy_title: "经济", economy_group_money: "资金与收入",
    economy_group_supply: "补给站", economy_group_cards: "计谋卡", economy_atomic: "核战争模式：游戏中为 {v}（更改会同时设置两者）" });
  // the Nations tab (words.toml nations_*, tip_tab_nations, tip_nations_*)
  Object.assign(words.us, { nations_tab: "Nations", tip_tab_nations: "Give one of the game's seven nations a new name and flag: China in Italy's place, say.", nations_title: "Nations", nations_help: "Give one of the game's seven nations a new name and flag, to make it another nation: China in Italy's place, say. The game keeps seven nations: the one you change keeps its place in the lobby, its build menus, and its campaign chapters and Operations. Its units are changed on the Units tab, and what they say on each unit's page. Not tried in the game yet.", nations_lobby_note: "The lobby's own nation button draws its flags inside the game's menu file, so it shows the game's flag for now. The new flag goes everywhere the game's flag lists show it: the loading screen, the players' names in a match, replays.", nations_flag_of: "{nation}'s flag", nations_was: "(was {nation})", nations_units_count: "{n} units and buildings", nations_change: "Change…", nations_close: "Close", tip_nations_change: "Give {nation} a new name and flag.", nations_name_head: "Name in the lobby", tip_nations_name_head: "What the lobby's nation list calls it, in every language.", nations_name_help: "What the lobby's nation list calls it. A language left as it is keeps the game's name.", nations_army_head: "Army name", tip_nations_army_head: "Its army's name where an Operation asks which army to take.", nations_army_help: "Its army's name where an Operation asks which army to take.", nations_flag_head: "Flag", tip_nations_flag_head: "The small round flag the game shows for this nation.", nations_flag_help: "Choose any picture of the flag, or drop one here: it's fitted to the game's flag, and the round shape stays the game's.", nations_flag_game: "The game's", nations_flag_mine: "Yours", nations_shine: "Shine like the game's flags", tip_nations_shine: "Light the top half and shade the bottom half, as the game's own flags are.", nations_flag_pick: "Choose a picture…", tip_nations_flag_pick: "Pick a picture of the new flag: PNG, JPG or any picture.", nations_flag_back: "Game's flag", tip_nations_flag_back: "Take your flag out: the game's comes back.", nations_flag_backed: "{nation} has the game's flag again.", nations_flag_none: "The Studio can't read this nation's flag in the game's files.", nations_flag_unreadable: "That picture couldn't be read. Try a PNG or JPG.", nations_flag_saved: "{nation}'s new flag is in your mod. Click Test in game to see it.", nations_units_head: "Units and what they say", nations_units_help: "Its units are changed on the Units tab: New unit… puts a copy of any unit in its build menus. What a unit says is on its page, under Voice.", nations_units: "{nation}'s units", tip_nations_units: "Open the Units tab with this nation picked.", nations_reset: "Put it all back", tip_nations_reset: "Give this nation back the game's name, army name and flag.", nations_reset_done: "{nation} is the game's again." });
  // the Music tab (words.toml music_*, tip_tab_music, tip_music_*)
  Object.assign(words.us, {
    music_tab: "Music", tip_tab_music: "The game's songs: hear each one, and put your own in its place",
    music_title: "Music",
    music_help: "Every song the game plays, by where it plays. Replace one with your own: drop a sound file on it (WAV, MP3, OGG or FLAC), cut it, fade it, then Use this. It's saved in the current mod, and the next build puts it in the game. Tried in the game: the main menu song, the songs of battle lists 1 and 2, new songs added to those lists, and a unit's voice; the rest not yet.",
    music_none: "No songs found in the game index: build it again in Settings.", music_group_menu: "Main menu",
    music_group_credits: "Credits", music_group_playlist: "In battle: list {n}",
    music_help_playlist: "In every battle the game plays from three lists and switches between them as the fight goes.",
    music_group_end: "End of a match", music_group_goals: "Mission goals",
    music_group_missions: "Campaign chapters and Operations",
    music_help_missions: "Only the missions that name these play them.", music_group_other: "Other moments",
    music_group_unused: "Not played by the game", music_help_unused: "Nothing in the game plays these songs.",
    music_also_menu: "also the main menu", music_also_credits: "also the credits",
    music_also_playlist: "also in battle, list {n}", music_also_end: "also at the end of a match",
    music_also_goals: "also for mission goals", music_also_other: "also at other moments",
    music_in_missions: "played by the missions of {n} map(s)", music_which_missions: "Which?", music_play: "Play",
    music_stop: "Stop", music_reading: "Reading…", music_replace: "Replace…", music_change: "Change…",
    music_yours: "Yours", music_play_yours: "Play yours", music_reset: "Back to the game's",
    music_back_done: "{name}: the game's song again.", tip_music_play: "Hear the game's song",
    tip_music_replace: "Put your own song here: drop a file, cut it, fade it, then Use this",
    tip_music_reset: "Take your song out of the mod: the game's plays again",
    music_editor_title: "Your song for {name}",
    music_editor_lead: "The game's song is {len} long. Yours can be any length: the Studio makes it the game's format.",
    music_drop: "Drop a sound file here (WAV, MP3, OGG or FLAC)", music_choose: "Choose a sound file…",
    music_file: "{name}, {len}",
    music_cant_read: "This file can't be read here. Save it as WAV or MP3 and try again.", music_start: "Start",
    music_end: "End", music_length: "Length {len}", music_fade_in: "Fade in", music_fade_out: "Fade out",
    music_volume: "Volume", music_match: "As loud as the game's",
    tip_music_match: "Set the volume so your song is as loud as the game's",
    music_matched: "Volume set to {db} dB, as loud as the game's song.", music_play_cut: "Play",
    music_play_game: "The game's", music_use: "Use this", tip_music_use: "Save your song in the current mod",
    music_making: "Making your song…", music_saving: "Saving… {n} %",
    music_saved: "{name}: your song is saved in the mod ({file})."
  });
  Object.assign(words.fr, {
    music_tab: "Musique", tip_tab_music: "Les morceaux du jeu : écoutez-les, et mettez les vôtres à leur place",
    music_title: "Musique",
    music_help: "Tous les morceaux que joue le jeu, selon l'endroit où ils passent. Remplacez-en un par le vôtre : déposez-y un fichier son (WAV, MP3, OGG ou FLAC), coupez-le, ajoutez un fondu, puis Utiliser. Il est enregistré dans le mod actuel, et la prochaine construction le met dans le jeu. Essayé en jeu : le morceau du menu principal, les morceaux des listes de bataille 1 et 2, de nouveaux morceaux ajoutés à ces listes, et la voix d'une unité ; le reste pas encore.",
    music_none: "Aucun morceau dans l'index du jeu : reconstruisez-le dans Paramètres.",
    music_group_menu: "Menu principal", music_group_credits: "Crédits",
    music_group_playlist: "En bataille : liste {n}",
    music_help_playlist: "Dans chaque bataille, le jeu puise dans trois listes et passe de l'une à l'autre selon le combat.",
    music_group_end: "Fin de partie", music_group_goals: "Objectifs de mission",
    music_group_missions: "Chapitres de campagne et Opérations",
    music_help_missions: "Seules les missions qui les nomment les jouent.", music_group_other: "Autres moments",
    music_group_unused: "Jamais joués par le jeu", music_help_unused: "Rien dans le jeu ne joue ces morceaux.",
    music_also_menu: "aussi le menu principal", music_also_credits: "aussi les crédits",
    music_also_playlist: "aussi en bataille, liste {n}", music_also_end: "aussi en fin de partie",
    music_also_goals: "aussi pour les objectifs de mission", music_also_other: "aussi à d'autres moments",
    music_in_missions: "joué par les missions de {n} carte(s)", music_which_missions: "Lesquelles ?",
    music_play: "Écouter", music_stop: "Arrêter", music_reading: "Lecture…", music_replace: "Remplacer…",
    music_change: "Modifier…", music_yours: "Le vôtre", music_play_yours: "Écouter le vôtre",
    music_reset: "Revenir à celui du jeu", music_back_done: "{name} : de nouveau le morceau du jeu.",
    tip_music_play: "Écouter le morceau du jeu",
    tip_music_replace: "Mettez votre morceau ici : déposez un fichier, coupez-le, ajoutez un fondu, puis Utiliser",
    tip_music_reset: "Retirer votre morceau du mod : celui du jeu revient",
    music_editor_title: "Votre morceau pour {name}",
    music_editor_lead: "Le morceau du jeu dure {len}. Le vôtre peut avoir n'importe quelle durée : le Studio le met au format du jeu.",
    music_drop: "Déposez un fichier son ici (WAV, MP3, OGG ou FLAC)", music_choose: "Choisir un fichier son…",
    music_file: "{name}, {len}",
    music_cant_read: "Ce fichier ne peut pas être lu ici. Enregistrez-le en WAV ou MP3 et réessayez.",
    music_start: "Début", music_end: "Fin", music_length: "Durée {len}", music_fade_in: "Fondu d'entrée",
    music_fade_out: "Fondu de sortie", music_volume: "Volume", music_match: "Aussi fort que celui du jeu",
    tip_music_match: "Régler le volume pour que votre morceau soit aussi fort que celui du jeu",
    music_matched: "Volume réglé à {db} dB, aussi fort que le morceau du jeu.", music_play_cut: "Écouter",
    music_play_game: "Celui du jeu", music_use: "Utiliser",
    tip_music_use: "Enregistrer votre morceau dans le mod actuel", music_making: "Préparation de votre morceau…",
    music_saving: "Enregistrement… {n} %", music_saved: "{name} : votre morceau est enregistré dans le mod ({file})."
  });
  Object.assign(words.sc, {
    music_tab: "音乐", tip_tab_music: "游戏的音乐：试听每一首，并换成你自己的", music_title: "音乐",
    music_help: "游戏播放的每一首音乐，按播放场合分组。用你自己的替换：拖入一个声音文件（WAV、MP3、OGG 或 FLAC），剪切、淡入淡出，然后点“使用”。它保存在当前模组中，下次构建会放进游戏。已在游戏中试过：主菜单音乐、战斗列表 1 和 2 的音乐、加入这些列表的新音乐，以及单位的语音；其余尚未试过。",
    music_none: "游戏索引里没有音乐：请在设置中重新建立。", music_group_menu: "主菜单", music_group_credits: "制作人员",
    music_group_playlist: "战斗中：列表 {n}", music_help_playlist: "每场战斗中，游戏从三个列表播放音乐，并随战况在它们之间切换。",
    music_group_end: "比赛结束", music_group_goals: "任务目标", music_group_missions: "战役章节和行动",
    music_help_missions: "只有指定了这些音乐的任务才会播放它们。", music_group_other: "其他时刻", music_group_unused: "游戏中不播放",
    music_help_unused: "游戏中没有任何地方播放这些音乐。", music_also_menu: "也用于主菜单", music_also_credits: "也用于制作人员名单",
    music_also_playlist: "也在战斗列表 {n} 中", music_also_end: "也在比赛结束时", music_also_goals: "也用于任务目标",
    music_also_other: "也在其他时刻", music_in_missions: "在 {n} 张地图的任务中播放", music_which_missions: "哪些？", music_play: "播放",
    music_stop: "停止", music_reading: "读取中…", music_replace: "替换…", music_change: "更改…", music_yours: "你的",
    music_play_yours: "播放你的", music_reset: "恢复游戏原曲", music_back_done: "{name}：已恢复为游戏原曲。", tip_music_play: "试听游戏原曲",
    tip_music_replace: "在这里放入你自己的音乐：拖入文件、剪切、淡入淡出，然后点“使用”", tip_music_reset: "从模组中移除你的音乐：重新播放游戏原曲",
    music_editor_title: "替换 {name} 的音乐", music_editor_lead: "游戏原曲长 {len}。你的可以是任意长度：Studio 会把它转成游戏的格式。",
    music_drop: "把声音文件拖到这里（WAV、MP3、OGG 或 FLAC）", music_choose: "选择声音文件…", music_file: "{name}，{len}",
    music_cant_read: "这里无法读取这个文件。请另存为 WAV 或 MP3 后再试。", music_start: "开始", music_end: "结束", music_length: "长度 {len}",
    music_fade_in: "淡入", music_fade_out: "淡出", music_volume: "音量", music_match: "与游戏原曲一样响",
    tip_music_match: "调整音量，使你的音乐和游戏原曲一样响", music_matched: "音量已设为 {db} dB，与游戏原曲一样响。", music_play_cut: "播放",
    music_play_game: "游戏原曲", music_use: "使用", tip_music_use: "把你的音乐保存到当前模组", music_making: "正在制作你的音乐…",
    music_saving: "保存中… {n} %", music_saved: "{name}：你的音乐已保存到模组（{file}）。"
  });
  // a unit's voice lines (words.toml voice_*)
  Object.assign(words.us, { music_add: "Add a song…", tip_music_add: "Add a song of your own to this list: the game plays it with the list's other songs", music_add_title: "A new song for battle list {n}", music_add_lead: "It joins the songs the game plays from this list. Give it a name, drop a sound file, cut it, then Use this.", music_name: "Name", music_new: "New", music_remove: "Remove", tip_music_remove: "Take this song out of the mod", music_removed: "{name}: taken out of the mod.", music_need_name: "Give the song a name (letters and digits)." });
  Object.assign(words.us, { voice_hidden: "{n} unit(s) no build menu shows" });
  Object.assign(words.us, { voice_saved: "{name}: your line is saved in the mod ({file}).",
    voice_back_done: "{name}: the game's line again." });
  Object.assign(words.us, {
    voice_title: "Voice", voice_own: "What this unit says in the game.",
    voice_shared: "What this unit says in the game. Units of its nation and kind share these lines, so a line changed here is heard from them too: {units}.",
    voice_copy: "A copy speaks with the lines of the unit it copies; a line changed here is heard from that unit too.",
    voice_editor_title: "Your line for {name}",
    voice_editor_lead: "The game's line is {len} long. Yours can be any length: the Studio makes it the game's format.",
    voice_moment_stop: "Stop", voice_moment_move: "Move", voice_moment_impossiblemove: "Can't move there",
    voice_moment_attack: "Attack", voice_moment_impossibleattack: "Can't attack that",
    voice_moment_attacked: "Attacked", voice_moment_heavysplash: "Heavy splash", voice_moment_revealed: "Revealed",
    voice_moment_fire: "Fire", voice_moment_targetdestroyed: "Target destroyed",
    voice_moment_uberstressed: "Very stressed", voice_moment_spawn: "Spawn", voice_moment_fighting: "Fighting",
    voice_moment_decroche: "Break off", voice_moment_gohome: "Go home", voice_moment_abort: "Abort",
    voice_moment_outofammo: "Out of ammo", voice_moment_blind: "Blind",
    voice_moment_attackground: "Attack the ground", voice_moment_ambush: "Ambush", voice_moment_capture: "Capture",
    voice_moment_recon: "Recon"
  });
  Object.assign(words.fr, { music_add: "Ajouter un morceau…", tip_music_add: "Ajouter votre propre morceau à cette liste : le jeu le joue avec les autres morceaux de la liste", music_add_title: "Un nouveau morceau pour la liste de bataille {n}", music_add_lead: "Il rejoint les morceaux que le jeu joue depuis cette liste. Donnez-lui un nom, déposez un fichier son, coupez-le, puis Utiliser.", music_name: "Nom", music_new: "Nouveau", music_remove: "Retirer", tip_music_remove: "Retirer ce morceau du mod", music_removed: "{name} : retiré du mod.", music_need_name: "Donnez un nom au morceau (lettres et chiffres)." });
  Object.assign(words.fr, { voice_hidden: "{n} unité(s) absente(s) des menus de production" });
  Object.assign(words.fr, { voice_saved: "{name} : votre réplique est enregistrée dans le mod ({file}).",
    voice_back_done: "{name} : de nouveau la réplique du jeu." });
  Object.assign(words.fr, {
    voice_title: "Voix", voice_own: "Ce que dit cette unité dans le jeu.",
    voice_shared: "Ce que dit cette unité dans le jeu. Les unités de sa nation et de son type partagent ces répliques : une réplique changée ici s'entend aussi chez elles : {units}.",
    voice_copy: "Une copie parle avec les répliques de l'unité qu'elle copie ; une réplique changée ici s'entend aussi chez cette unité.",
    voice_editor_title: "Votre réplique pour {name}",
    voice_editor_lead: "La réplique du jeu dure {len}. La vôtre peut avoir n'importe quelle durée : le Studio la met au format du jeu.",
    voice_moment_stop: "Arrêt", voice_moment_move: "Déplacement",
    voice_moment_impossiblemove: "Déplacement impossible", voice_moment_attack: "Attaque",
    voice_moment_impossibleattack: "Attaque impossible", voice_moment_attacked: "Attaqué",
    voice_moment_heavysplash: "Gros impact", voice_moment_revealed: "Repéré", voice_moment_fire: "Feu",
    voice_moment_targetdestroyed: "Cible détruite", voice_moment_uberstressed: "Très stressé",
    voice_moment_spawn: "Apparition", voice_moment_fighting: "Combat", voice_moment_decroche: "Décrochage",
    voice_moment_gohome: "Retour à la base", voice_moment_abort: "Annulation",
    voice_moment_outofammo: "Plus de munitions", voice_moment_blind: "Aveugle",
    voice_moment_attackground: "Attaque au sol", voice_moment_ambush: "Embuscade", voice_moment_capture: "Capture",
    voice_moment_recon: "Reconnaissance"
  });
  Object.assign(words.sc, { music_add: "添加音乐…", tip_music_add: "把你自己的音乐加入这个列表：游戏会和列表中的其他音乐一起播放", music_add_title: "战斗列表 {n} 的新音乐", music_add_lead: "它会加入游戏从这个列表播放的音乐。给它起个名字，拖入一个声音文件，剪切，然后点“使用”。", music_name: "名称", music_new: "新增", music_remove: "移除", tip_music_remove: "从模组中移除这首音乐", music_removed: "{name}：已从模组中移除。", music_need_name: "请给音乐起个名字（字母和数字）。" });
  Object.assign(words.sc, { voice_hidden: "{n} 个不在任何生产菜单中的单位" });
  Object.assign(words.sc, { voice_saved: "{name}：你的台词已保存到模组（{file}）。",
    voice_back_done: "{name}：已恢复为游戏原台词。" });
  Object.assign(words.sc, {
    voice_title: "语音", voice_own: "这个单位在游戏中说的话。",
    voice_shared: "这个单位在游戏中说的话。同国家、同类型的单位共用这些台词，所以在这里改掉的台词在它们身上也会听到：{units}。",
    voice_copy: "复制的单位使用原单位的台词；在这里改掉的台词在原单位身上也会听到。", voice_editor_title: "替换 {name} 的台词",
    voice_editor_lead: "游戏原台词长 {len}。你的可以是任意长度：Studio 会把它转成游戏的格式。", voice_moment_stop: "停止", voice_moment_move: "移动",
    voice_moment_impossiblemove: "无法移动到那里", voice_moment_attack: "攻击", voice_moment_impossibleattack: "无法攻击",
    voice_moment_attacked: "遭到攻击", voice_moment_heavysplash: "重型爆炸", voice_moment_revealed: "被发现",
    voice_moment_fire: "开火", voice_moment_targetdestroyed: "目标摧毁", voice_moment_uberstressed: "高度紧张",
    voice_moment_spawn: "出现", voice_moment_fighting: "交战", voice_moment_decroche: "脱离", voice_moment_gohome: "返航",
    voice_moment_abort: "中止", voice_moment_outofammo: "弹药耗尽", voice_moment_blind: "盲目",
    voice_moment_attackground: "对地攻击", voice_moment_ambush: "伏击", voice_moment_capture: "占领",
    voice_moment_recon: "侦察"
  });
  // a map's background sound (words.toml map_sound_*, tip_map_sound; sound.js openAmbience)
  Object.assign(words.us, { map_sound_btn: "Background sound…",
    tip_map_sound: "The sound this map plays under the battle: hear it, and put your own in",
    map_sound_title: "Background sound: {map}",
    map_sound_lead: "Under the battle, the map plays one long sound over and over, made of three layers played together. Hear each layer, then put a sound of yours in its place, or start from the one another map plays.",
    map_sound_untried: "Not tried in the game yet. How loud the game plays each layer, and when, isn't known yet.",
    map_sound_from: "Start from", map_sound_own: "This map's own (heard on {maps})", map_sound_like: "The one heard on {maps}",
    map_sound_layers: "The three layers",
    map_sound_layers_help: "A layer of yours that's shorter than the others plays again from the start until they end.",
    map_sound_layer: "Layer {n}", map_sound_all: "Hear all three together",
    map_sound_no_project: "Pick or make your map changes first: a map's sounds are saved there.",
    map_sound_editor_title: "Layer {n} of the background sound: {map}",
    map_sound_editor_lead: "The game's layer is {len} long. Yours plays over and over under the battle, with the other two layers.",
    map_sound_from_own: "{map} starts from its own background sound again.",
    map_sound_from_other: "{map} now starts from the background sound heard on {maps}.",
    map_sound_saved: "{name}: saved in your map changes ({file}).", map_sound_back_done: "{name}: the game's layer again." });
  Object.assign(words.fr, { map_sound_btn: "Son d'ambiance…",
    tip_map_sound: "Le son que cette carte joue sous la bataille : écoutez-le et mettez le vôtre",
    map_sound_title: "Son d'ambiance : {map}",
    map_sound_lead: "Pendant la bataille, la carte joue en boucle un long son fait de trois couches jouées ensemble. Écoutez chaque couche, puis mettez un son à vous à sa place, ou partez de celui d'une autre carte.",
    map_sound_untried: "Pas encore essayé dans le jeu. On ne sait pas encore à quel volume le jeu joue chaque couche, ni quand.",
    map_sound_from: "Partir de", map_sound_own: "Celui de cette carte (entendu sur {maps})", map_sound_like: "Celui qu'on entend sur {maps}",
    map_sound_layers: "Les trois couches",
    map_sound_layers_help: "Une couche à vous plus courte que les autres reprend du début jusqu'à ce qu'elles finissent.",
    map_sound_layer: "Couche {n}", map_sound_all: "Écouter les trois ensemble",
    map_sound_no_project: "Choisissez ou créez d'abord vos modifications de cartes : les sons d'une carte y sont enregistrés.",
    map_sound_editor_title: "Couche {n} du son d'ambiance : {map}",
    map_sound_editor_lead: "La couche du jeu dure {len}. La vôtre se joue en boucle sous la bataille, avec les deux autres couches.",
    map_sound_from_own: "{map} repart de son propre son d'ambiance.",
    map_sound_from_other: "{map} part maintenant du son d'ambiance qu'on entend sur {maps}.",
    map_sound_saved: "{name} : enregistrée dans vos modifications de cartes ({file}).", map_sound_back_done: "{name} : de nouveau la couche du jeu." });
  Object.assign(words.sc, { map_sound_btn: "背景音…", tip_map_sound: "这张地图在战斗中播放的声音：试听，并换成你自己的",
    map_sound_title: "背景音：{map}",
    map_sound_lead: "战斗中，地图会循环播放一段由三层同时播放组成的长音。逐层试听，然后换成你自己的声音，或者从另一张地图的声音开始。",
    map_sound_untried: "尚未在游戏中试过。游戏以多大音量、在什么时候播放每一层，目前还不清楚。",
    map_sound_from: "起始声音", map_sound_own: "这张地图自己的（在 {maps} 上播放）", map_sound_like: "在 {maps} 上播放的那个",
    map_sound_layers: "三层", map_sound_layers_help: "你的某层比其他层短时，会从头重播，直到其他层结束。",
    map_sound_layer: "第 {n} 层", map_sound_all: "三层一起试听", map_sound_no_project: "请先选择或新建你的地图修改：地图的声音保存在那里。",
    map_sound_editor_title: "背景音第 {n} 层：{map}", map_sound_editor_lead: "游戏原有的这一层长 {len}。你的会在战斗中与另外两层一起循环播放。",
    map_sound_from_own: "{map} 已改回自己的背景音。", map_sound_from_other: "{map} 现在从在 {maps} 上播放的背景音开始。",
    map_sound_saved: "{name}：已保存到你的地图修改（{file}）。", map_sound_back_done: "{name}：已恢复为游戏原有的这一层。" });
  // [prop, its name, type, the game's value, the Nuclear mode's when it differs]: some of rusemod.economy's values
  const ECONOMY = [
    ["money", [["QteDeviseInitiale", "Starting money", "int32", 200], ["TempsGenAutoDevises", "Income: seconds between payments", "int32", 4],
      ["QuantiteGenAutoDevises", "Income: money each payment", "int32", 1], ["StockDeviseSupplementaireFacile", "Extra money on Easy", "int32", 72]]],
    ["supply", [["QteDeviseParCamion", "Money each supply truck brings", "int32", 3, 6], ["NbCamionParConvoi", "Trucks in a supply convoy", "int32", 3],
      ["TempsENtreDeuxConvois", "Seconds between supply convoys", "int32", 30], ["RatioForDepotNearlyDepleted", "A depot is nearly empty at (share left)", "float32", 0.25]]],
    ["production", [["MinProductionTime", "Shortest build time (seconds)", "float32", 1], ["MaxProductionQueueSize", "Production queue length (most)", "uint32", 30],
      ["NbAvionsParAeroport", "Planes per airfield", "int32", 8]]],
    ["cards", [["NbMaxCardsInPool", "Ruse cards in the pool (most)", "int32", 99],
      ["NbInitialCardsInPoolForAllianceTaille_1", "Ruse cards at the start: 1 player per side", "int32", 2, 4],
      ["PaliersTempsToChooseNewCardForAllianceTaille_1", "New ruse cards after (seconds): 1 player per side", "float32", [105, 210, 315], [80, 160, 240]]]],
    ["computer", [["ArmyValueForceLaunchAttack", "Army worth that makes the computer attack", "uint32", 600],
      ["CheckAndCancelWaitingRequest", "The computer cancels orders that waited too long", "bool", 1]]],
    ["decoys", [["ConstructionDelayForFakeBuildingsMin", "Decoy buildings: seconds before building (least)", "int32", 5]]],
  ];
  const economyEdits = new Map();  // prop -> the mod's value (StudioApi.economy_edit)
  // the Music tab: [group, [[member, name, seconds, also, maps]]], as StudioApi.music groups the real game's songs
  const MUSIC_DIR = "gen_sound\\ww2\\sons\\atp_music\\";
  const MUSIC = [
    ["menu", [[MUSIC_DIR + "ruse_menu_ref-1.ess", "Outgame", 175.4, [], []]]],
    ["playlist0", [[MUSIC_DIR + "progression_1-v.1.ess", "Progression 1", 66.0, ["missions"],
      [{ map: "2. TAKING COMMAND!", parts: ["chapter1"] }, { map: "6. FROM BAIT TO PREY", parts: ["chapter1", "chapter2"] }]]]],
    ["playlist1", [[MUSIC_DIR + "battle1.ess", "Battle 1", 38.1, ["missions"], [{ map: "D-Day", parts: ["chapter1"] }]],
      [MUSIC_DIR + "battle-2_ref_1.ess", "Battle 2", 39.7, ["missions"], [{ map: "Face-to-Face", parts: ["challenge"] }]]]],
    ["end", [["gen_sound\\ww2\\sons\\jingles\\jingle-bigvictory.ess", "Big victory", 8.1, [], []]]],
    ["missions", [[MUSIC_DIR + "tunisie.ess", "Tunisie", 60.1, [], [{ map: "2. TAKING COMMAND!", parts: ["chapter1", "chapter3"] }]]]],
    ["unused", [[MUSIC_DIR + "lose1.ess", "Lose", 11.8, [], []]]]];
  const VOICE_DIR = "gen_sound\\ww2\\sons\\generated\\acknows\\";
  const VOICES = [["Stop", 1, 1.2], ["Move", 4, 1.6], ["Attack", 4, 1.8], ["Fire", 4, 1.1], ["Spawn", 3, 2.0]];
  // the game's map backgrounds (StudioApi.map_sound): [file, name, the maps they're heard on, seconds], made up
  const BACKGROUNDS = [["WW2\\Sons\\SFX_ENV\\MultiPiste_Ambiance_Tunisie.wav", "Tunisie", ["Blitz", "Valley", "Gamma", "Beta"], 60.0],
    ["WW2\\Sons\\SFX_ENV\\MultiPiste_Ambiance_Swamp.wav", "Swamp", ["Swamps"], 45.0]];
  const mapSoundUse = new Map();  // map -> the background it starts from (StudioApi.map_sound_use)
  const musicMine = new Map();  // member -> the mod's song (an address the page can fetch)
  const musicUpload = [];
  // a made-up "game song": a soft chord of `seconds` as a WAV the page can fetch
  function fakeTone(seconds, freq) {
    const rate = 22050, n = Math.round(seconds * rate), bytes = new Uint8Array(44 + n * 4), dv = new DataView(bytes.buffer);
    const put = (o, t) => { for (let i = 0; i < t.length; i++) bytes[o + i] = t.charCodeAt(i); };
    put(0, "RIFF"); dv.setUint32(4, 36 + n * 4, true); put(8, "WAVEfmt "); dv.setUint32(16, 16, true);
    dv.setUint16(20, 1, true); dv.setUint16(22, 2, true); dv.setUint32(24, rate, true); dv.setUint32(28, rate * 4, true);
    dv.setUint16(32, 4, true); dv.setUint16(34, 16, true); put(36, "data"); dv.setUint32(40, n * 4, true);
    for (let i = 0; i < n; i++) {
      const t = i / rate, env = Math.min(1, t * 4, (seconds - t) * 4);
      const v = env * 0.25 * (Math.sin(2 * Math.PI * freq * t) + 0.5 * Math.sin(2 * Math.PI * freq * 1.5 * t));
      dv.setInt16(44 + i * 4, v * 32767, true);
      dv.setInt16(46 + i * 4, v * 32767, true);
    }
    return URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
  }
  // the AI tab (words.toml ai_*, tip_tab_ai, tip_ai_reset)
  Object.assign(words.us, { ai_tab: "AI", ai_title: "AI: the computer players",
    tip_tab_ai: "How the computer players play, the units they like to build, and the ruse cards, for every battle with this mod.",
    ai_help: "A change here is saved in the current mod at once. From LittleGroove's AI editor in RUSE Mod Manager. Tried in the game: a ruse card taken out of the menu, a card moved in it, a card's length and when Easy starts attacking; the rest not yet.",
    ai_how_title: "How they play",
    ai_mix: "A computer player mixes three sets of values: Default, its difficulty and its profile (both picked in the game's lobby). For each value the game takes the profile's when it isn't Default's, else the difficulty's when it isn't Default's, else Default's; a value a set doesn't list counts as 0. Only the values a set lists can be changed here.",
    ai_default: "Default", ai_same_default: "Same as Default: doesn't count",
    ai_none: "The game index has none of the computer players' values. Build it again in Settings.",
    ai_bonus_title: "Units they're keener to build",
    ai_bonus_help: "The computer players like these units more, by the number below, in the game modes, difficulties and profiles listed.",
    ai_cards_title: "Ruse cards (every player's)",
    ai_cards_help: "How long each ruse lasts, whether it is in the ruse menu and its place there: for every player, not only the computer.",
    ai_not_in_menu: "Not in the ruse menu", tip_ai_reset: "Put the value back as the game has it.",
    ai_group_attack: "Attacking", ai_group_defense: "Defending", ai_group_harass: "Harassing", ai_group_money: "Money",
    ai_group_depots: "Depots and trucks", ai_group_production: "Building units", ai_group_weights: "What it likes to build",
    ai_group_ruses: "Ruses", ai_group_retaliation: "Retaliation", ai_group_intel: "Intelligence", ai_group_other: "Other",
    ai_scripts_title: "Map and mission scripts",
    ai_scripts_help: "The scripts the game runs on its maps: the campaign's chapters, challenges, Operations and its own tests (IA_Common.dat), shown as Python. A big one takes a few seconds to open. Change this script lets you change one in your mod. From LittleGroove's AI editor and his Mission Script editor.",
    ai_scripts_pick: "Pick a script…", ai_scripts_opening: "Opening {name}… (a big script takes a few seconds)",
    ai_scripts_shown: "{name}: {n} lines ({file})", ai_scripts_missing: "This copy of the Studio can't show the scripts: {why}",
    ai_scripts_copy: "Copy", tip_ai_scripts_copy: "Copy the whole script.", ai_scripts_copied: "Script copied.",
    upgrade_title: "Upgrade and research",
    upgrade_help: "The unit this one is an upgrade of, as in the game: heavy infantry of light infantry, the Jackson of the Wolverine. An upgrade is researched for its price and time before it can be built. From LittleGroove's units editor. Not tried in the game yet.",
    upgrade_from: "Upgrade of", upgrade_none: "None: a unit of its own", upgrade_children: "Its upgrades: {names}",
    tip_upgrade_from: "Pick the unit this one is an upgrade of (the same nation's, in the same build menu), or none.",
    tip_upgrade_undo: "Put it back as the game has it." });
  Object.assign(words.fr, { ai_tab: "IA", ai_title: "IA : les joueurs ordinateur", ai_default: "Défaut",
    ai_group_attack: "Attaque", ai_group_money: "Argent", ai_not_in_menu: "Pas dans le menu des ruses" });
  Object.assign(words.sc, { ai_tab: "AI", ai_title: "AI：电脑玩家", ai_default: "默认", ai_group_attack: "进攻",
    ai_group_money: "资金", ai_not_in_menu: "不在计谋菜单中" });
  // [address, kind, number in the lobby, name, lobby line, [[group, [[prop, its name, type, the game's value]]]]]: some of
  // the game's sets of values, as the real index has them (rusemod.ai)
  const AI_SETS = "$/GFX/Everything/AIConfiguration";
  const AI = [
    [`${AI_SETS}:DefaultAndDifficultyAndProfil[0].Items[class=TAIConfiguration].OverridenParams`, "default", 0, null, null,
      [["attack", [["AttaqueTempsActivation", "Seconds before it starts attacking", "float32", 30],
        ["OffensiveNbMissionMax", "Most attacks at once (-1: no limit)", "int32", -1]]],
       ["harass", [["HarcelementActif", "Harasses the enemy", "bool", 1]]],
       ["money", [["PercentMoneyToReserveForBatimentAdmin", "% of money kept for admin buildings", "int32", 20]]]]],
    [`${AI_SETS}/AIDifficultyList:Items[0].OverridenParams`, "difficulty", 0, "Easy", null,
      [["attack", [["AttaqueTempsActivation", "Seconds before it starts attacking", "float32", 300],
        ["OffensiveNbMissionMax", "Most attacks at once (-1: no limit)", "int32", -1]]],
       ["money", [["PercentMoneyToReserveForBatimentAdmin", "% of money kept for admin buildings", "int32", 20]]]]],
    [`${AI_SETS}/AIDifficultyList:Items[2].OverridenParams`, "difficulty", 2, "Hard", null,
      [["money", [["DeviseBonusIA", "Extra money at the start (cheat)", "int32", 150],
        ["IncomeBonusIA", "Extra income each payment (cheat)", "int32", 1],
        ["PercentMoneyToReserveForBatimentAdmin", "% of money kept for admin buildings", "int32", 25]]]]],
    [`${AI_SETS}/AIDescriptorList:Items[0].OverridenParams`, "personality", 0, "Regular", "This AI will behave as a standard general",
      [["attack", [["AttaqueTempsActivation", "Seconds before it starts attacking", "float32", 30]]],
       ["production", [["NbProdIdleTank", "Built when idle: tanks", "int32", 3]]]]],
    [`${AI_SETS}/AIDescriptorList:Items[4].OverridenParams`, "personality", 4, "Blitzkrieg", "This AI will use rush tactics to defeat you",
      [["production", [["NbProdIdleTank", "Built when idle: tanks", "int32", 4]]]]],
  ];
  const AI_BONUS = "$/GFX/Everything/AISpecificBonusList:SpecificBonusList[class=TAISpecificBonus]";
  // [address, name, line, [[prop, its name, type, the game's value]]]: some of the ruse cards, in the menu's order
  const AI_CARDS = [
    ["$/GFX/Everything/BluffZoneManager:BluffCardDescriptors[9]", "BLITZ", "Increases your units' speed in the sector by 50%.",
      [["LifeDuration", "How long it lasts (seconds)", "float32", 120], ["ShowInMenu", "Shown in menu", "bool", 1],
       ["PositionInMenu", "Menu slot", "int32", 5]]],
    ["$/GFX/Everything/BluffZoneManager:BluffCardDescriptors[14]", "DECOY AT BASE", "Allows you to deploy dummy anti-tank base.",
      [["LifeDuration", "How long it lasts (seconds)", "float32", 360], ["PositionInMenu", "Menu slot", "int32", 10]]],
    ["$/GFX/Everything/BluffZoneManager:BluffCardDescriptors[5]", "SPY", "Reveals all unidentified units in the sector.",
      [["LifeDuration", "How long it lasts (seconds)", "float32", 60], ["ShowInMenu", "Shown in menu", "bool", 1],
       ["PositionInMenu", "Menu slot", "int32", 60]]],
  ];
  const aiEdits = new Map();  // `${address}|${prop}` -> the mod's value (StudioApi.ai_edit)
  const aiGame = (address, prop) => {
    for (const [a, , , , , groups] of AI) if (a === address) for (const [, rows] of groups) for (const r of rows) if (r[0] === prop) return r;
    if (address === AI_BONUS) return [["BonusValue", "Extra preference for these units", "int32", 400],
      ["UnitIDs", "Units (by number)", "int32", [3008, 3009]]].find((r) => r[0] === prop);
    const card = AI_CARDS.find((c) => c[0] === address);
    return card ? card[3].find((r) => r[0] === prop) : undefined;
  };
  const aiNow = (address, prop) => {
    const key = `${address}|${prop}`;
    if (aiEdits.has(key)) return aiEdits.get(key);
    const r = aiGame(address, prop);
    return r ? r[3] : 0;  // a value a set doesn't list counts as 0
  };
  const aiSame = (address, prop) => {
    const set = AI.find((s) => s[0] === address);
    return set && set[1] !== "default" ? aiNow(address, prop) === aiNow(AI[0][0], prop) : null;
  };
  const aiRowOf = (address, lang, [prop, label, type, game]) => {
    const key = `${address}|${prop}`;
    return { prop, label: lang === "base" ? prop : label, type, list: Array.isArray(game), game,
      value: aiEdits.has(key) ? aiEdits.get(key) : null, same_default: aiSame(address, prop) };
  };
  // the All values tab's words (words.toml values_*, tip_values_*)
  Object.assign(words.us, {"values_tab": "All values", "tip_tab_values": "Every value of the game's units and other objects, even the ones the other tabs don't show. For when the other tabs don't have what you want to change.", "values_help": "Every value of the game's unit data, even the ones the other tabs don't show. 1. Pick a file or type a name on the left. 2. Click what you want. 3. Change a value: it's saved in the current mod at once. Hold the mouse over anything to see what it does. From LittleGroove's raw editor in RUSE Mod Manager. Not tried in the game yet.", "values_file_label": "File", "tip_values_file": "Show only the objects of one file of the game's unit data, or of every file. Most units are in everything.cpp.gladndfbin.", "values_file_all": "Every file", "values_find_label": "Name or kind", "values_find_hint": "e.g. Sherman, Ammo, TAmmunition", "tip_values_find": "Type part of a name (Sherman) or of a kind of object (TAmmunition). The list updates as you type.", "values_by_title": "Look for a value", "tip_values_by": "Open this to find objects by a value they hold: every ammunition with a damage of 120, say.", "values_by_help": "Fill one box or both. The value's name is the game's own (Puissance is damage, PorteeMaximale is range).", "values_prop_label": "Value's name", "values_prop_hint": "e.g. Puissance", "tip_values_prop": "Part of the value's name, as the game spells it: Puissance (damage), PorteeMaximale (range), ProductionPrice (price).", "values_value_label": "Holds", "values_value_hint": "e.g. 120, or Sherman", "tip_values_value": "A number, or part of a text or of a linked object's name, that the value holds.", "values_go": "Look", "tip_values_go": "Look again with what's in the boxes (it also looks by itself as you type).", "values_start": "Type a name or pick a file to start.", "values_looking": "Looking…", "values_none": "Nothing found. Try fewer letters, or Every file.", "values_count": "Found: {n}", "values_some": "The first {shown} of {n}: type more to narrow it down.", "tip_values_object": "{kind}, in {file}. Click to see every value it has.", "values_pick": "Click something on the left to see every value it has.", "values_back": "← Back", "tip_values_back": "Go back to what you were looking at before.", "values_part_of": "↑ Part of {name}", "tip_values_part_of": "This is a part of another object: open that one.", "tip_values_copy": "Copy this object's address (its full name in the game's data) to paste it somewhere else.", "values_copied": "Address copied.", "tip_values_code_name": "Its name in the game's data.", "values_meta": "{kind} · {file} · object {n}", "tip_values_meta": "What kind of object this is, which of the game's files it's in, and its number in that file.", "values_why_outside": "This isn't in the game's unit data, so a mod can't change it. You can look, not change.", "values_why_not_stable": "Nothing with a name leads to this object, so a mod can't find it to change it. You can look, not change.", "values_how": "Change a value and press Enter (or click elsewhere): it's saved in the current mod at once. “Game's value” undoes it. Use Test in game to try it.", "values_shared": "{n} objects share this part: a change here changes it for all of them.", "values_users_warn": "{n} other objects use this one: a change here changes it for all of them.", "values_rows": "Its values ({n})", "values_used_by": "Used by ({n})", "tip_values_user": "This object uses the one shown: click to open it.", "values_users_more": "And {n} more.", "values_yes": "Yes", "values_no": "No", "values_link_none": "Nothing (empty)", "values_kind_number": "A number. Type a new one and press Enter: it's saved in the mod at once.", "values_kind_bool": "Yes or no. Tick the box for yes.", "values_kind_text": "A text. Type a new one and press Enter. If it's a file's name, only use a file the game has.", "values_kind_key": "Which of the game's texts is shown here, by its key (like N_UNI_137). The words it shows are under the box. Only type a key the game has.", "values_kind_vector": "Numbers that go together, one per box: a position, a size, a direction, or a colour (red, green, blue, see-through: 0 to 255).", "values_kind_guid": "A unique id. Leave it as it is unless you know why it should change.", "values_kind_numbers": "A list of numbers, with a comma between each (like 20, 20, 20). It may be made longer or shorter.", "values_kind_link": "A link to another object. Type part of a name and pick one from the list, or empty the box for nothing. Open shows the object it links to.", "values_kind_part": "A part of this object (its weapons, its look...). Click to open it and change its values.", "values_kind_written": "Several values together, written the way mod files write them: [ ] around a list, MAP [ ] for pairs. Only change it if you know that way of writing.", "values_kind_fixed": "Raw data: it can't be changed here.", "values_cant_row": "This value can't be changed here.", "tip_values_words": "The words the game shows for this key, in your language.", "values_words_none": "(no words for this key in this language)", "tip_values_swatch": "The colour these numbers make.", "values_items": "Items: {n}", "values_open_part": "Open this part", "tip_values_part": "Open this part to see and change its values.", "values_open": "Open", "tip_values_open": "Open the object this links to.", "values_reset": "Game's value", "tip_values_reset": "Put the value back as the game has it (takes your change out of the mod).", "values_removed": "Taken out by the mod.", "values_game": "The game has: {value}", "values_saved": "Saved in the mod: {name}.", "values_same": "{name} is the game's value again.", "values_open_all": "All values", "tip_values_open_all": "See and change every value this has, even the ones this page doesn't show (the All values tab)."});
  Object.assign(words.us, {"values_as_text": "Edit as a list", "tip_values_as_text": "Type the whole list in one box, with a comma between the numbers: to add numbers or take some out.", "values_item_n": "Number {n} in the list"});
  Object.assign(words.us, {"values_words_edit": "Change the words…", "tip_values_words_edit": "Change what this text says in the game, in each language (a unit's name, say).", "values_words_help": "What players see for this text, one box per language. Languages you leave as they are keep the game's words. Not tried in the game yet.", "tip_values_words_lang": "What players who play in {lang} see.", "values_words_save": "Save the words", "tip_values_words_save": "Save these words in the current mod.", "values_words_reset": "Game's words", "tip_values_words_reset": "Put back the game's words in every language (takes the change out of the mod).", "values_words_saved": "Saved the words of {key} in the mod.", "values_words_back": "{key} has the game's words again.", "values_words_mine": "(your mod's words)", "values_words_no_text": "The game has no words for this key."});
  Object.assign(words.us, {"scen_item_title": "This item's values", "tip_scen_item_title": "Change what the picked item is like in this scenario: whose it is, a depot's trucks, a zone's size, a town's name. Saved in your map changes at once.", "scen_item_camp": "Whose it is", "tip_scen_item_camp": "Who gets this unit or building when the scenario starts: nobody (neutral, anyone can take it) or one of the scenario's sides.", "tip_scen_item_camp_skirmish": "On a battle map every item stays neutral: a skirmish game spawns only neutral items.", "scen_item_trucks": "Supply trucks", "tip_scen_item_trucks": "How many supply trucks this depot has (the game's depots have 15 to 72). 0 to 1000.", "scen_item_radius": "Radius", "scen_item_width": "Width", "scen_item_height": "Length", "tip_scen_item_size": "The zone's size in metres. Missions use zones to tell where things happen.", "scen_item_metres": "{m} m", "scen_item_zone_note": "Zones are used by the scenario's mission: a size changed here changes where it happens.", "scen_item_town": "Town name", "tip_scen_item_words": "The town's name on the map, in every language. Saved in your map changes.", "scen_item_game": "The game has: {value}", "scen_item_reset": "Game's value", "tip_scen_item_reset": "Put this value back as the game has it (takes your change out of the map changes).", "scen_item_untested": "Changes here are saved in your map changes at once. Not tried in the game yet."});
  Object.assign(words.us, {"ai_script_edit": "Change this script", "tip_ai_script_edit": "Change this mission's script in your mod: its whole text, checked with the game's own Python before it's saved.", "ai_script_editing_help": "Change the text, then Check and Save in the mod. A script runs inside the game for everyone who plays your mod, and a mistake can stop the mission: test it in the game. The steps and the reference on the right help find your way. Not tried in the game yet.", "ai_script_check": "Check", "tip_ai_script_check": "Have the game's own Python read the text, without saving: it says the line of the first mistake.", "ai_script_save": "Save in the mod", "tip_ai_script_save": "Check the text and, when the game's Python reads it, save it in the current mod with the form the game runs.", "ai_script_reset": "Game's script", "tip_ai_script_reset": "Take your change of this script out of the mod: the game runs its own script again.", "ai_script_close": "Stop changing", "tip_ai_script_close": "Close the editor and show the script again. Text not saved yet stays only until you open another script.", "tip_ai_script_area": "The script's text, as Python 2.5 (the game's). Tab puts 4 spaces.", "ai_outline_title": "The mission's steps", "tip_ai_outline": "What the mission does, in order (LittleGroove's outline): click a step to go to where it is written.", "tip_ai_outline_step": "Go to line {line}, where this step is written.", "ai_outline_none": "No steps found here (a helper script, or a mission written another way).", "ai_ref_title": "Reference: the game's script parts (in English)", "tip_ai_ref": "LittleGroove's catalogue of the 1,133 parts the game's scripts are built from: what each does, its values, and a line to insert.", "ai_ref_find": "Find a part: Victory, Spawn, Camera…", "tip_ai_ref_find": "Type part of a name (the catalogue is in English): the list shows the parts the game uses most first.", "tip_ai_ref_kind": "Show only one kind of part: actions, conditions, objectives, the AI, camps, variables…", "ai_ref_kind_all": "Every kind", "ai_ref_insert": "Insert", "tip_ai_ref_insert": "Put this part in the script on a line of its own, above the cursor, named IR_NEW: rename it, then use it in a step.", "ai_ref_used": "Used {n} times in the game's missions", "ai_ref_params": "Its values (* needed)", "ai_ref_none": "Nothing found. Try fewer letters.", "ai_scripts_changed": "changed", "ai_script_mine": "Your mod changes this script: this is its text.", "ai_script_no_compiler": "This copy of the Studio can't make scripts the game runs ({why}).", "ai_script_unsaved": "Not saved yet", "ai_script_checking": "Checking…", "ai_script_ok": "The game's Python reads it: no mistakes found.", "ai_script_bad": "Line {line}: {error}", "ai_script_saved_here": "Saved in the mod.", "ai_script_game_again": "The game's own script again.", "ai_script_saved": "Saved in the mod: the script of {name}.", "ai_script_back": "{name}: the game's own script again."});
  Object.assign(words.us, {"tip_ai_script_pick": "Pick one of the game's scripts, by map: it shows below, and Change this script changes it in your mod."});
  Object.assign(words.us, {"ai_outline_more": "Only the first {n} steps are listed here; {more} more are further down in the script."});
  Object.assign(words.us, {"scen_mark_tool": "Add a name or zone", "tip_scen_mark": "Put a town or hill name, a named point or a zone on the map: pick what, then click the map where it goes.", "scen_mark_town": "Town name", "tip_scen_mark_town": "A town's name written on the map, as the game shows its towns. You type the name; it's the same in every language until you change one.", "scen_mark_hill": "Hill name", "tip_scen_mark_hill": "A hill's name written on the map, as the game shows its hills. You type the name; it's the same in every language until you change one.", "scen_mark_point": "Named point", "tip_scen_mark_point": "An invisible spot with a name. Mission scripts use these names to send units somewhere or to check where they are.", "scen_mark_circle": "Round zone", "tip_scen_mark_circle": "An invisible round area with a name. Mission scripts use it to notice when units go in or out.", "scen_mark_rect": "Square zone", "tip_scen_mark_rect": "An invisible rectangle with a name. Mission scripts use it to notice when units go in or out.", "scen_mark_town_help": "Type the town's name below, then click the map where it goes.", "scen_mark_hill_help": "Type the hill's name below, then click the map where it goes.", "scen_mark_point_help": "Click the map where the named point goes. It gets a name you can change after (point_1, point_2…).", "scen_mark_circle_help": "Click the map where the zone's middle goes. You can change its size and name after.", "scen_mark_rect_help": "Click the map where the zone's middle goes. You can change its size, turn and name after.", "scen_mark_words": "Name to show", "scen_mark_words_hint": "e.g. Springfield", "tip_scen_mark_words": "The words written on the map, in every language. To give one language other words, pick the name on the map after and use Change the words…", "scen_mark_words_first": "Type the name to show first, then click the map.", "scen_layer_points": "Named spots", "tip_scen_take_out_point": "Take it out of the match. A mission script that uses its name may stop working. You can put it back.", "scen_item_hill": "Hill name", "tip_scen_item_no_key": "This name isn't one of the game's texts, so its words can't be changed here.", "scen_item_name": "Name", "tip_scen_item_name": "The name mission scripts find it by. Changing it can break a script that uses the old name.", "scen_item_no_name": "(no name)", "scen_item_turn": "Turn", "tip_scen_item_turn": "Which way it faces, in degrees."});
  Object.assign(words.us, {"values_words_help_new": "This is your map's own name, one box per language. A box you leave empty gets the English words. Not tried in the game yet."});
  Object.assign(words.us, {"tip_scen_remove_place": "Take this name, point or zone back out of your map changes: the game's map is as before.", "tip_scen_remove_mine": "Take what you added back out of your map changes.", "tip_scen_put_back": "Put it back where the game has it (your move is undone)."});
  Object.assign(words.us, {"notes_title": "Notes", "notes_hint": "Your own notes about this: what you changed and why, ideas to try…", "tip_notes": "Only you see these: they're kept in your mod's folder (notes.json), never in the game or in a mod you export. Saved when you click elsewhere.", "notes_saved": "Note saved."});
  Object.assign(words.us, {"values_text_new": "New text…", "tip_values_text_new": "Give this value words of its own: a new text of your mod's, so no other unit or menu that shares the game's text changes with it.", "values_text_new_help": "The words, in English; every language gets them until you change one with Change the words…", "values_text_new_hint": "e.g. Sherman Firefly", "values_text_new_make": "Make the new text", "values_text_new_done": "A new text of your mod's: the value now shows it."});
  Object.assign(words.us, {"files_tab": "Files", "tip_tab_files": "Look at any file inside the game's packs (pictures, texts, scripts, data), save a copy, or change it in your mod. The game's own files are never touched.", "files_intro": "Every file inside the game's packs. Pick a pack, then a file to see it, save a copy, or change it in your mod (only what you change is kept; the game's files are never touched).", "files_pack_label": "Pack", "tip_files_pack": "One of the game's packs (big files that hold many smaller ones): its data, its texts and pictures, its scripts, or one map's own.", "files_pack_gameplay": "Gameplay (units, economy, menus)", "files_pack_gameplay_fixed": "Gameplay, not patchable", "files_pack_scripts": "Mission scripts and the computer players", "files_pack_maps": "Maps (scenarios and placements)", "files_pack_texts": "Texts, pictures and sounds", "files_pack_common": "Common (videos, fonts)", "files_pack_map": "Map · {file}", "files_find_label": "Look for", "files_find_hint": "part of a name, e.g. .tgv or baseunite", "tip_files_find": "Shows only the files whose path has these letters (upper or lower case doesn't matter).", "files_loading": "Reading…", "files_count": "{n} of its {total} files", "files_more": "(the first {n} shown: look for part of a name to find the rest)", "files_pick": "Pick a file on the left to see it.", "tip_files_row": "Click to see this file.", "files_kind_ndf": "Game data", "files_kind_texture": "Texture", "files_kind_image": "Picture", "files_kind_picture": "Picture", "files_kind_table": "Text table", "files_kind_script": "Mission script", "files_kind_text": "Text", "files_kind_scenario": "Scenario", "files_kind_pack": "Pack inside the pack", "files_kind_binary": "Other file", "files_kind_bytes": "Other file", "files_save": "Save a copy…", "tip_files_save": "Save this file, as the game has it, wherever you choose (to open it in another program). The game isn't touched.", "files_saved": "Saved: {path}", "files_open_pack": "Open this pack", "tip_files_open_pack": "This file is itself a pack with files inside: list them, as for the game's packs.", "files_inside": "{n} files inside.", "files_in_pack": "Inside: {path}", "files_back_out": "Back out", "tip_files_back_out": "Back to the pack this one is inside.", "files_not_read": "Not shown as its kind ({why}): its first bytes instead.", "files_ndf_objects": "Objects", "files_ndf_classes": "Kinds of object", "files_ndf_props": "Value names", "files_ndf_packed": "Packed", "files_ndf_top": "Its most used kinds of object", "files_picture_size": "{w} × {h} shown; {fw} × {fh} in the game · {format}", "files_table_count": "{n} texts ({shown} shown here; save a copy to see them all).", "files_scenario_zones": "Zones (sectors)", "files_bytes_more": "…and {n} more bytes (save a copy to see them all)."});
  Object.assign(words.us, {"files_changed_mark": "changed in your mod", "files_added_mark": "added by your mod", "files_showing_mine": "shown here as your mod has it", "files_showing_game": "shown here as the game has it", "files_change": "Change it with a file of mine…", "tip_files_change": "Pick a file of yours of the same kind (a texture for a texture...): it's checked, then your mod keeps only what differs from the game's file. The game's files are never touched.", "files_changed_done": "Changed in your mod. Test in game builds it in.", "files_show_mine": "Show my version", "files_show_game": "Show the game's version", "tip_files_show": "Switch between the file as your mod changes it and as the game has it.", "files_reset": "Put the game's back", "tip_files_reset": "Take your change of this file out of your mod: the game's own file is used again.", "files_remove_added": "Take it out of my mod", "tip_files_remove_added": "Take this file you added out of your mod.", "files_mine_error": "Your change of this file no longer fits the game's file ({why}).", "files_cannot": "This file can't be changed in a mod: {why}", "files_add": "Add a file of mine to this pack…", "tip_files_add": "Add a new file of yours (a texture, a picture, a text table...) to this pack, in your mod's own folder there, for your mod's values to point at.", "files_add_help": "Its name in your mod's folder in the pack (folders with /). It goes in mods/<your mod>/.", "files_add_name": "Name of the new file", "files_add_hint": "e.g. pictures/my_flag.tgv", "tip_files_add_name": "Letters, digits, _, - and dots; its ending says what it is (.tgv a texture, .dic a text table...).", "files_add_pick": "Pick the file…", "tip_files_add_pick": "Choose the file on your PC: it's checked as a file of its kind, then put in your mod.", "files_added_done": "Added to your mod.", "files_safe": "Your mod keeps only what you change, never a copy of the game's file, and the game's own files are never touched. Not tried in the game yet."});
  Object.assign(words.us, {"mission_open": "Menus, files and texts of this mission…", "tip_mission_open": "See where the game's menus list this mission, check every file the game needs to start it, and change its texts in every language (LittleGroove's mission steps).", "mission_title": "{name}: menus, files and texts", "mission_tab_menu": "In the menus", "tip_mission_tab_menu": "Whether the game lists this mission, where, and its values and texts there.", "mission_tab_files": "Files check", "tip_mission_tab_files": "Every file the game needs to start this mission, from its menu entry to the mission itself, each checked.", "mission_tab_texts": "Texts", "tip_mission_tab_texts": "Every text this mission owns: in the menu, and what its mission script shows during the game.", "mission_loading": "Reading the game's files…", "mission_new_map": "This map is new in your mod. Its missions are checked by Check this map, which builds your mod first.", "mission_unbound": "No menu of the game loads this one: it's a test or an unused setup.", "mission_listed": "The game lists it in {menu}: number {n} of {total}.", "mission_not_listed": "No menu lists this mission, so the game never shows it.", "mission_order_head": "The menu, as the player sees it", "tip_mission_order": "Every entry of this menu, in your mod's order (the game's when your mod gives none), in its groups. This mission is highlighted.", "mission_values_head": "Its values in the menu", "tip_mission_values": "What the game's menu entry for this mission says. Change them with the button below.", "mission_values_change": "Change these values…", "tip_mission_values_change": "Opens this menu entry in the All values tab, where each value is changed and saved in your mod.", "mission_values_cannot": "This menu entry can't be opened in the All values tab.", "mission_menu_texts_head": "Its texts in the menu", "tip_mission_menu_texts": "The name and briefing the player reads in the menu before pressing Start.", "mission_v_NbPlayers": "Players", "mission_v_GameType": "Game type", "mission_v_MapSize": "Map size", "mission_v_GameModeMulti": "Game mode", "mission_v_ChapterId": "Chapter number", "mission_v_CategoryId": "Group in the list", "mission_v_NbSecondaryObjectives": "Secondary objectives", "mission_v_PopCapPlayer": "Unit limit (player)", "mission_v_PopCapIA": "Unit limit (computer)", "mission_v_PrivilegeId": "Privilege number", "mission_t_Description": "Name in the menu", "mission_t_LongDescription": "Briefing", "mission_t_LongDescription1": "Briefing, part 1", "mission_t_LongDescription2": "Briefing, part 2", "mission_t_LongDescription3": "Briefing, part 3", "mission_t_LongDescription4": "Briefing, part 4", "mission_files_ok": "Everything the game needs to start this mission is there.", "mission_files_broken": "{n} missing or not matching: the game can't start this mission as it is.", "mission_files_note": "These are the game's own files. To check them with your mod's changes, use Check this map: it builds your mod first.", "mission_state_ok": "Fine", "mission_state_missing": "Missing", "mission_state_mismatch": "Doesn't match", "mission_state_optional": "Not needed here", "mission_state_unknown": "Can't tell", "mission_why_scenario_file_ok": "The mission's setup file is in the game's map data.", "mission_why_scenario_file_missing": "The mission's setup file isn't in the game's map data.", "mission_why_scenario_cluster_ok": "A loader on this map opens the mission.", "mission_why_scenario_cluster_missing": "Nothing on this map opens the mission, so the game can't load it.", "mission_why_cluster_scenario_ok": "The loader names the mission's setup file.", "mission_why_cluster_scenario_missing": "The loader names no setup file.", "mission_why_script_ok": "The mission script is where the game looks for it.", "mission_why_script_missing": "The mission script isn't where the game looks for it, so it never runs.", "mission_why_script_unknown": "The loader gives the game no place to look for a mission script.", "mission_why_dico_ok": "The mission's texts are there.", "mission_why_dico_missing": "The mission's texts are missing, so they show blank in the game.", "mission_why_optional": "Not needed by this mission: the game's own are the same.", "mission_why_dico_langs_ok": "In {n} languages.", "mission_why_terrain_cluster_ok": "The map's ground is found.", "mission_why_terrain_cluster_missing": "The map's ground isn't found.", "mission_why_terrain_cluster_unknown": "The loader names no ground.", "mission_why_terrain_subcluster_ok": "The ground has the part this mission asks for.", "mission_why_terrain_subcluster_mismatch": "The ground doesn't have the part this mission asks for.", "mission_why_terrain_dat_ok": "The ground names its map data.", "mission_why_terrain_dat_missing": "The ground names no map data.", "mission_why_mapload_ok": "A map slot starts this mission.", "mission_why_mapload_missing": "No map slot starts this mission, so nothing can launch it.", "mission_why_mapload_no_id": "The map slot has no id, so no menu entry can point at it.", "mission_why_cluster_entry_ok": "The map slot finds the part it asks for.", "mission_why_cluster_entry_mismatch": "The map slot asks for a part this mission doesn't have.", "mission_why_registration_ok": "A menu entry points at the map slot.", "mission_why_registration_missing": "No menu entry points at this map slot: it loads, but the menus never show it.", "mission_why_pack_ok": "The menu entry is in one of the menu's lists.", "mission_why_pack_missing": "The menu entry is in no list, so the menu never shows it.", "mission_texts_no_script": "The mission script's texts can't be read in this copy of the Studio (the script viewer is missing a part): only the menu's texts are shown.", "mission_texts_count": "{n} texts. Each one changes in every language at once, and is saved in your mod.", "mission_texts_line": "Mission script, line {line}", "mission_texts_script": "Mission script", "tip_mission_words": "Change these words in every language at once. Saved in your mod.", "mc_mission_link": "Mission {mission}: {why}", "mc_missions_unread": "The map's missions couldn't be checked: {why}"});
  Object.assign(words.us, {"tip_mission_move_pack": "The mission next to it comes from another of the game's lists: the menu shows each list's missions in the list's own order, so they can't swap.", "mission_move_up": "Move up", "tip_mission_move_up": "Put this mission one place higher in its group of the menu. Saved in your mod. Not tried in the game yet.", "mission_move_down": "Move down", "tip_mission_move_down": "Put this mission one place lower in its group of the menu. Saved in your mod. Not tried in the game yet.", "mission_order_reset": "Game's order", "tip_mission_order_reset": "Put this mission's group back in the game's own order (takes your mod's order for it out).", "tip_mission_order_reset_none": "Your mod doesn't change the order of this mission's group.", "tip_mission_move_top": "It's already first in its group: a mission moves only among the missions grouped with it.", "tip_mission_move_bottom": "It's already last in its group: a mission moves only among the missions grouped with it.", "tip_mission_move_unnamed": "A mission of its group has no scenario file a mod can name, so this group's order can't change.", "mission_group": "Group {n}", "tip_mission_group": "Missions the menu shows together, under the menu's own heading. A mission moves only within its group, among the missions from the same list of the game's.", "mission_order_mine": "Your mod changes the order of this mission's group.", "mission_moved": "Saved in your mod. Not tried in the game yet."});
  Object.assign(words.us, {"map_more": "Show more ▾", "tip_map_more": "Open the rest of this panel: how many buildings, props and trees, what the colours on the ground mean, the see-through layers, where the scenario is in the game, and the keys.", "map_less": "Show less ▴", "tip_map_less": "Close the rest of this panel again, so it takes less room on the map."});
  Object.assign(words.us, {"values_new": "New object…", "tip_values_new": "Make a brand-new object of one of the game's kinds (an ammunition, a weapon…) with a name of your own, in your mod. It starts empty: give it values on its page.", "values_new_help": "A new object starts with no values: give it some with Add a value… on its page. The game only uses it once something links to it. Not tried in the game yet.", "values_new_kind_label": "Kind", "values_new_kind_hint": "e.g. TAmmunition", "tip_values_new_kind": "The kind of object, by the game's own name for it (TAmmunition is an ammunition). Type part of it and pick one from the list.", "values_new_kind_count": "{n} in the game", "values_new_name_label": "Name", "values_new_name_hint": "e.g. Ammo_My_Shell", "tip_values_new_name": "Its name in the game's data: letters A-Z, digits and _, starting with a letter. Start it with something of your mod's own, so it's never a name the game has.", "values_new_make": "Make it", "tip_values_new_make": "Make the new object in your mod and open it.", "values_new_done": "{name} is made in your mod: give it values with Add a value…", "values_mine_mark": "made by your mod", "values_deleted_mark": "deleted by your mod", "values_mine": "Made by your mod: it has only the values you give it. Not tried in the game yet.", "values_meta_mine": "{kind} · made by your mod", "values_why_deleted": "Your mod deletes this object (or the one it's part of), so its values can't be changed here. Put it back to change them.", "values_put_back": "Put it back", "tip_values_put_back": "Take the delete out of your mod: the object is in the game again, with any changes your mod makes to it.", "values_put_back_done": "{name} is back.", "values_add": "Add a value…", "tip_values_add": "Give this object a value it doesn't have yet: one that other objects of its kind have. Saved in your mod.", "values_add_help": "Pick a value that other objects of this kind have, check what it should be, then click Add. You can change it on its row after. Not tried in the game yet.", "values_add_pick_label": "Which value", "tip_values_add_pick": "The values other objects of this kind have and this one doesn't.", "values_add_value_label": "Its value", "tip_values_add_value": "What the new value is. It starts as another object of this kind has it.", "values_add_go": "Add", "tip_values_add_go": "Add this value to the object, in your mod.", "values_add_none": "This object already has every value its kind has here.", "values_add_some_cant": "{n} more can't be added here (parts and raw data).", "values_added_done": "Added in your mod: {name}.", "values_added": "Added by your mod (the game's object doesn't have it).", "values_given": "Given by your mod.", "tip_values_take_out_added": "Take this value back out of your mod.", "values_take_out": "Take out", "tip_values_take_out": "Take this value out of the object, in your mod: the game then uses its own default for it. You're asked first. Not tried in the game yet.", "values_take_out_sure": "Take {name} out of this object? The game then uses its own default for it.", "values_take_out_yes": "Take it out", "values_took_out": "{name} is taken out in your mod.", "values_delete": "Delete this object…", "tip_values_delete": "Take this whole object out of the game's data, in your mod. You're told first what points at it. Hiding a unit from the build menus is usually safer. Not tried in the game yet.", "values_delete_sure": "Delete {name}? It's taken out of the game's data when your mod is built. Not tried in the game yet.", "values_delete_sure_mine": "Delete {name}? It's taken out of your mod, with its values.", "values_delete_yes": "Delete it", "tip_values_delete_yes": "Delete this object in your mod.", "values_delete_listed": "{name} can't be deleted: the game's list of units names it, and the game fails to load its units when one is missing. Hide it from the build menus instead.", "values_deleted_done": "{name} is deleted in your mod.", "values_points_at": "Things that point at it ({n}):", "values_points_after": "If it goes, they point at nothing: the game may fail where they're used, and your mod won't build until each one points somewhere else.", "values_your_change": "your change", "values_inside_go": "Your changes inside it go with it ({n})."});
  // the All values tab (StudioApi.values_files / values_find / value_object...): a few objects of the unit data, each
  // row as rusemod.values.row makes it: [prop, label, kind, type, value, text, to, extra]
  const EV = "$/GFX/Everything/";
  const VALUE_FILE = "genglad/patchable/gfx/everything.cpp.gladndfbin";
  const VALUE_OBJECTS = {
    [EV + "Descriptor_Unit_M4_Sherman"]: { class: "TUniteAuSolDescriptor", name: "SHERMAN", index: 58910, users: [], rows: [
      ["DescriptorId", "Id", "number", "uint32", 1143, "uint32(1143)"],
      ["SeuilMort", "Health", "number", "float32", 400, "400.0"],
      ["ProductionPrice", "Price", "numbers", "int32", [20, 20, 20, 20, 20], "[20, 20, 20, 20, 20]"],
      ["StickToGround", "StickToGround", "bool", "bool", 1, "true"],
      ["ClassNameForDebug", "Debug name", "text", "string", "Unit_M4_Sherman", "'Unit_M4_Sherman'"],
      ["NameInMenuToken", "Name (text key)", "key", "key", "N_UNI_137", "key(N_UNI_137)", null, { words: "SHERMAN" }],
      ["WeaponDescriptor", "WeaponDescriptor", "part", "TWeaponManagerDescriptor", null, null, EV + "Descriptor_Unit_M4_Sherman:WeaponDescriptor"],
      ["ArmorDescriptor", "Armour", "link", "reference", EV + "Descriptor_Unit_Char_DCA_M4_SKINK:ArmorDescriptor", null,
        EV + "Descriptor_Unit_Char_DCA_M4_SKINK:ArmorDescriptor"],
      ["UpgradeRequire", "Upgrade of", "link", "reference", EV + "Descriptor_Unit_M3_Lee", EV + "Descriptor_Unit_M3_Lee", EV + "Descriptor_Unit_M3_Lee"],
      ["ShowInMenu", "Shown in menu", "numbers", "bool", [1, 1, 0, 1, 1], "[true, true, false, true, true]"]] },
    [EV + "Descriptor_Unit_M4_Sherman:WeaponDescriptor"]: { class: "TWeaponManagerDescriptor", name: null, index: 58911,
      owner: EV + "Descriptor_Unit_M4_Sherman", users: [[EV + "Descriptor_Unit_M4_Sherman", "WeaponDescriptor"]], rows: [
        ["Turrets", "Turrets", "list", "list", null, null, null, { count: 1, items: [{ path: "Turrets[0]", part: true,
          class: "TTurretTwoAxisDescriptor", to: EV + "Descriptor_Unit_M4_Sherman:WeaponDescriptor.Turrets[0]" }] }],
        ["Salves", "Salves", "numbers", "int32", [4, 30], "[4, 30]"],
        ["AlwaysOrientArmorTowardsThreat", "AlwaysOrientArmorTowardsThreat", "bool", "bool", 0, "false"]] },
    [EV + "Descriptor_Unit_M3_Lee"]: { class: "TUniteAuSolDescriptor", name: "LEE", index: 58320,
      users: [[EV + "Descriptor_Unit_M4_Sherman", "UpgradeRequire"]], rows: [
        ["SeuilMort", "Health", "number", "float32", 300, "300.0"],
        ["ProductionPrice", "Price", "numbers", "int32", [15, 15, 15, 15, 15], "[15, 15, 15, 15, 15]"]] },
    [EV + "Ammo_Canon_AP_75"]: { class: "TAmmunition", name: "AP shell · Medium cal.", index: 1201, users: [], rows: [
      ["Puissance", "Damage", "number", "float32", 120, "120.0"],
      ["PorteeMaximale", "Range", "number", "float32", 104000, "104000.0"],
      ["TypeName", "TypeName", "key", "key", "AP_shell", "key(AP_shell)", null, { words: "AP shell" }]] },
    [EV + "LightSettings_Day"]: { class: "TLightDescriptor", name: null, index: 77, users: [], rows: [
      ["Direction", "Direction", "vector", "Float3", [0, -0.7, 0.7], "Float3[0.0, -0.7, 0.7]"],
      ["Color", "Color", "vector", "RGBA", [255, 230, 200, 255], "RGBA[255, 230, 200, 255]"],
      ["Tags", "Tags", "map", "map", null, "MAP [('day', 1), ('night', 0)]", null, { count: 2, items: [] }],
      ["Id", "Id", "guid", "guid", "8a1f9c0e-35b2-4c55-9e7d-0d3e5f6a7b8c", "GUID:{8a1f9c0e-35b2-4c55-9e7d-0d3e5f6a7b8c}"],
      ["Blob", "Blob", "fixed", "0x14", "48 bytes", null]] },
  };
  // a made-up mission script (never the game's), the mod's changed ones, and two parts of the reference
  const FAKE_SCRIPT = ["# a made-up mission script for the preview", "import leveldesignsolo.objectif", "",
    "IR_1 = leveldesign.descriptor.DescriptorWaitDuree(Duree=10)",
    "IR_2 = leveldesign.descriptor.DescriptorPrint(Message=u'Hold the bridge', ObjectList=[])",
    "IR_3 = leveldesignsolo.objectif.DescriptorDeclencheVictoire(Duree=1, Chapter=1)",
    "IR_4 = leveldesign.descriptor.DescriptorSequentiel(SubActions=[IR_1, IR_2, IR_3])", ""].join("\n");
  const fakeScripts = new Map();  // path -> the mod's text (StudioApi.ai_script_save)
  const FAKE_PARTS = [
    { name: "DescriptorDeclencheVictoire", label: "Trigger victory", kind: "objective", category: "Objectives & endings",
      help: "Ends the mission in victory.", params: [{ name: "Duree", type: "object", default: 1, required: false, help: "" },
        { name: "Chapter", type: "int", default: 1, required: false, help: "" }], used: 27, examples: ["m01_leipzig__scripting"],
      snippet: "IR_NEW = leveldesignsolo.objectif.DescriptorDeclencheVictoire(Duree=1, IdMapSoloForLadder=-1, Chapter=1, DeclencheCredits=False)" },
    { name: "DescriptorWaitDuree", label: "Wait (seconds)", kind: "action", category: "Control flow", help: "Waits this many seconds.",
      params: [{ name: "Duree", type: "float", default: 0, required: true, help: "Seconds." }], used: 640, examples: [],
      snippet: "IR_NEW = leveldesign.descriptor.DescriptorWaitDuree(Duree=0)" }];
  const valueEdits = new Map();  // `${address}|${prop}` -> { value, text } (StudioApi.value_edit)
  const valueWords = new Map();  // text key -> { lang: words } (StudioApi.value_words_set)
  const VALUE_LANGS = ["us", "fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"];
  const valueRowOf = (address, lang, [prop, label, kind, type, value, text, to, extra]) => {
    const key = `${address}|${prop}`;
    const locked = prop === "DescriptorId";
    const gone = valueDeleted.has(address.split(":")[0]), edited = valueEdits.get(key) || null;
    const added = !!(extra && extra.added);
    return { prop, label: lang === "base" ? prop : label, kind, type, value, text, to: to || null, locked,
      can: !!current && !gone && !locked && kind !== "part" && kind !== "fixed", words: (extra && extra.words) || null,
      words_mine: kind === "key" && valueWords.has(value) ? valueWords.get(value)[lang === "base" ? "us" : lang] || null : null,
      count: extra && extra.count, items: extra && extra.items, edited, added,
      deletable: !!current && !gone && !locked && !added && !(edited && edited.removed) };
  };
  // values added and taken out, objects made and deleted (StudioApi.value_prop_add / value_object_new...)
  const valueDeleted = new Set();  // the game's objects the mod deletes
  const VALUE_KIND_PROPS = {  // what objects of each kind can be given: [prop, label, kind, type, start]
    TUniteAuSolDescriptor: [["UpgradePrice", "Research price", "number", "int32", "50"],
      ["IsUpgrade", "Is an upgrade", "bool", "bool", "0"], ["Factory", "Factory", "number", "int32", "10"],
      ["DescriptorId", "Id", "number", "uint32", ""]],
    TAmmunition: [["Puissance", "Damage", "number", "float32", "120"], ["PorteeMaximale", "Range", "number", "float32", "104000"],
      ["TypeName", "TypeName", "key", "key", "AP_shell"], ["NbTirParSalves", "Shots per salvo", "number", "int32", "1"]],
    TWeaponManagerDescriptor: [["Salves", "Salves", "numbers", "int32", "4, 30"]],
  };
  const valueGameWords = (key) => ({ N_UNI_137: "SHERMAN", AP_shell: "AP shell", PortIsland: "Port Island",
    NATION_0: "USA", NATION_1: "Germany", NATION_2: "UK", NATION_3: "France", NATION_4: "Italy", NATION_5: "USSR",
    NATION_7: "Japan", NAT_NAME_0: "American 1st Army", NAT_NAME_1: "German Transition Army",
    NAT_NAME_2: "British 21st Army", NAT_NAME_3: "French 1st Army", NAT_NAME_4: "Italian Co-Belligerent Army",
    NAT_NAME_5: "Russian 1st Belorussian Front" })[key] || null;
  // the Nations tab's made-up flags (the real Studio hands the page the game's own 28 x 28 pictures): a round badge
  // in each nation's colours, and the mod's own flags (StudioApi.nation_flag_set) by nation
  const NATION_COLOURS = [["#2b4fa8", "#ffffff"], ["#d33", "#111"], ["#c8102e", "#012169"], ["#0055a4", "#ef4135"],
    ["#1a8a4a", "#d22"], ["#d22", "#ffd700"], ["#fff", "#d00"]];
  const fakeBadge = ([a, b]) => "data:image/svg+xml;base64," + btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28"><circle cx="14" cy="14" r="13" fill="${a}"/><circle cx="14" cy="14" r="6" fill="${b}"/></svg>`);
  const nationFlags = new Map();
  const newWords = new Map();  // a new label's own text key -> { lang: words } (StudioApi._new_label_text)
  const fakeNotes = new Map();  // mod -> { key: note } (StudioApi.note_set)
  const fakeGameFiles = new Map();  // `${mod}|${pack}|${nested}|${path}` -> "changed" or "added" (StudioApi.files_change)
  const FAKE_FILES = {  // the Files tab's made-up packs (never the game's files)
    gameplay: [{ path: "genglad\\patchable\\gfx\\everything.cpp.gladndfbin", kind: "ndf", size: 597431 },
      { path: "genglad\\patchable\\readme.txt", kind: "text", size: 120 }],
    texts: [{ path: "gen\\ww2\\res2d\\interface\\flags\\flag_us.tgv", kind: "texture", size: 3720 },
      { path: "genlocalisation\\ww2\\localisation\\us\\baseunite.dic", kind: "table", size: 44676 },
      { path: "gen\\pack\\menuus.ppk", kind: "pack", size: 26229 }],
    "map:DataMapIsland_v09.dat": [{ path: "output\\highdef.tms", kind: "binary", size: 2048 }],
    inner: [{ path: "gen\\ww2\\res2d\\texanimationuniticone\\eu\\soldat_us_leger.tgv", kind: "texture", size: 3716 }],
  };
  const valuePage = (address, lang) => {
    const o = VALUE_OBJECTS[address];
    if (!o) throw new Error(`There's nothing at ${address} in this game build.`);
    const gone = valueDeleted.has(address.split(":")[0]);
    return { address, class: o.class, named: !o.owner, name: lang === "base" ? null : o.name, file: o.mine ? null : VALUE_FILE,
      pack: "ZZ_GladPatchableWin.dat", index: o.index, shared: false, owners: 1,
      owner: o.owner ? { address: o.owner, name: lang === "base" ? null : VALUE_OBJECTS[o.owner].name } : null,
      editable: !!current && !gone, why_not: !current ? "no_mod" : gone ? "deleted" : "",
      rows: o.rows.map((r) => valueRowOf(address, lang, r)),
      used_by: o.users.map(([a, path]) => ({ address: a, path, name: lang === "base" ? null : (VALUE_OBJECTS[a] || {}).name })),
      users: o.users.length, mine: !!o.mine, deleted: gone };
  };
  const valueTyped = (row, value) => {  // what rusemod.values.typed makes of what was typed (enough for the preview)
    const [, , kind, type, game] = row;
    if (kind === "number" || kind === "bool") {
      const n = typeof value === "boolean" ? Number(value) : Number(value);
      if (!Number.isFinite(n)) throw new Error(`${row[0]}: '${value}' isn't a number`);
      const v = type === "float32" ? n : Math.round(n);
      return { value: v, text: String(v), same: v === game };
    }
    if (kind === "numbers" || kind === "vector") {
      const list = (Array.isArray(value) ? value : String(value).split(/[\s,;]+/).filter(Boolean)).map(Number);
      if (list.some((n) => !Number.isFinite(n))) throw new Error(`${row[0]}: numbers only, with a comma between each`);
      return { value: list, text: `[${list.join(", ")}]`, same: JSON.stringify(list) === JSON.stringify(game) };
    }
    if (kind === "link") {
      const v = String(value || "").trim();
      if (v && !VALUE_OBJECTS[v] && !v.startsWith(EV)) throw new Error(`${row[0]}: there's nothing at ${v} in the game data to link to`);
      return { value: v || null, text: v || "nil", same: (v || null) === game };
    }
    return { value: kind === "list" || kind === "map" || kind === "pair" ? null : String(value), text: String(value),
      same: String(value) === String(kind === "list" || kind === "map" || kind === "pair" ? row[5] : game) };
  };
  // Delete map (words.toml delete_map, tip_delete_map, really_delete_map, map_deleted)
  Object.assign(words.us, {"delete_map": "Delete map", "tip_delete_map": "Take this new map out of your map changes, with everything changed on it. Its folder goes to the Recycle Bin, so it can be put back from there. The game's own maps can't be deleted.", "really_delete_map": "Delete {name}? Everything changed on it goes to the Recycle Bin with it.", "map_deleted": "{name} was deleted: its folder is in the Recycle Bin, if you want it back."});
  const exported = { path: "C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod", file: "sherman-test-0.1.0.rusemod",
    size: 2711, size_text: "3 KB", sha256: "5d1c0f4b0e7f7c3ad8b0a4f6f1f0a0e8c4b2d6e1f3a5c7e9b1d3f5a7c9e1b3d5",
    entry: ["[[mod]]", 'id = "sherman-test"', 'name = "sherman-test"', 'version = "0.1.0"', 'description = "Made in the RUSE Studio."',
      'download = ""  # the https:// link to the .rusemod once it is uploaded (a GitHub Release)', "size = 2711",
      'sha256 = "5d1c0f4b0e7f7c3ad8b0a4f6f1f0a0e8c4b2d6e1f3a5c7e9b1d3f5a7c9e1b3d5"', 'game_build = "24687178"',
      'fingerprint = "K7Q2-M9XD"', 'made_with = "RUSE Studio 0.9.8"', 'tags = []  # e.g. ["gameplay"]; a cheat or a test tool: ["cheat"]'].join("\n") + "\n",
    made_with: "RUSE Studio 0.9.8", credit: "Made with RUSE Studio 0.9.8 (https://github.com/sneadtristen6/R.U.S.E-2.0-Project)" };
  const jobs = {
    index: [["  ZZ_Win.dat"], "The game index is ready."],
    export: [["Building the mod on the game, to record the game build and the fingerprint…", "  fingerprint: K7Q2-M9XD",
      "Saved as C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod", "Size: 2711 bytes",
      "SHA-256: 5d1c0f4b0e7f7c3ad8b0a4f6f1f0a0e8c4b2d6e1f3a5c7e9b1d3f5a7c9e1b3d5"],
      "Saved as C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod"],
    check: [["Building the mod on this map, in a folder removed afterwards…", "  roads: 1 new road joined to the road network",
      "  bridges open", "Checking the movement graphs for infantry and vehicles…"], "The map is checked."],
    test: [["Building the modded copy of R.U.S.E. for sherman-test in D:\\RUSE-Instances\\Modded game…",
      "  1 change in 1 file", "  modded copy ready: 41 files linked, 1 replaced", "Starting R.U.S.E. from the modded copy…"],
      "R.U.S.E. is starting."],
  };

  // the game folder (?fake=notfound: not found until one is chosen), and the troubleshooter's made-up findings: one of
  // each level, two with a fix that takes them away, and the game missing (with its fix) until a folder is chosen
  const PICKED = "D:\\Games\\R.U.S.E";
  let fakeGame = mode === "notfound" ? null : "D:\\Steam\\steamapps\\common\\R.U.S.E";
  const doctorState = { running: true, leftovers: true };
  function fakeDoctor() {
    const f = (key, level, say, fix, data) => ({ key, level, say, data: data || {}, fix: fix || null });
    const copies = "D:\\RUSE-Instances";
    const findings = [fakeGame ? f("game", "ok", "doc_game_ok", null, { path: fakeGame })
      : f("game", "fail", "doc_game_missing", "choose_game"), f("steam", "info", "doc_steam_off"),
    doctorState.running ? f("running", "warn", "doc_running_copy", "close_game", { names: "RUSE.exe (4120)" })
      : f("running", "ok", "doc_running_none")];
    if (fakeGame) {  // no game: no place for modded copies yet, so no checks of them
      findings.push(f("drive", "ok", "doc_drive_ok", null, { path: copies, fs: "NTFS" }), f("space", "ok", "doc_space_ok", null, { gb: 182.4 }),
        doctorState.leftovers ? f("leftovers", "info", "doc_left", "clear_leftovers", { names: "studio-sherman-test.old" })
          : f("leftovers", "ok", "doc_left_none"),
        f("readonly", "info", "doc_readonly", null, { n: 3 }),
        f("write", "fail", "doc_write_fail", null, { path: copies, why: "Access is denied" }));
    }
    const lines = findings.map((x) => {
      const data = Object.entries(x.data).map(([k, v]) => `${k}=${v}`).join(", ");
      return `[${x.level}] ${x.key}: ${x.say}` + (data ? ` (${data})` : "");
    });
    return { findings, report: ["RUSE Studio 0.6.3, Windows 10.0.26200"].concat(lines).join("\n") };
  }

  // the clean game backup (rusemod.backup): none at first (?fake=backup: one already made, with the game's files
  // changed since; ?fake=oldbackup: one of an older build; ?fake=nospace: no room for one; ?fake=running: a restore
  // refused while R.U.S.E. runs). Its jobs run like the real ones: progress lines, then a result
  const BUILD = "24687178", BACKUPS = "D:\\RUSE-Backup";
  const backupOf = (b, date) => ({ path: `${BACKUPS}\\${b}`, build: b, made: date.replace(" ", "T") + ":00", date,
    files: 61, size: 5690000000, size_gb: 5.3, matches: b === BUILD });
  const changedSince = mode === "backup" || mode === "running";  // another mod manager changed files since the backup
  let backups = changedSince ? [backupOf(BUILD, "2026-09-28 18:05")]
    : mode === "oldbackup" ? [backupOf("24087620", "2026-08-02 11:40")] : [];
  let gameClean = !changedSince;
  const backupStatus = () => !fakeGame ? { found: false, backups: [], current: null, busy: "" }
    : { found: true, build: BUILD, folder: BACKUPS, drive: "D:", backups: backups.slice(), current: backups.find((b) => b.matches) || null,
        need_gb: 5.4, free_gb: mode === "nospace" ? 2.1 : 182.4, enough: mode !== "nospace", busy: "" };
  const gameDiffers = () => gameClean ? { changed: [], missing: [], added: [] } : {
    changed: ["Data/PC/190852/ZZ_GladPatchableWin.dat", "Data/PC/190852/ZZ_Win.dat"], missing: ["Data/lang.ini"],
    added: ["Data/PC/190852/ZZ_GladPatchableWin.dat.bak", "Mods/load_order.txt"] };
  const backupJobs = {};
  const steps = (prefix) => [0, 12, 25, 37, 50, 62, 75, 87, 100].map((p) => `${prefix}${p}%`);
  const backupJob = (lines, message, result, then) => {
    const id = `backup-${Object.keys(backupJobs).length + 1}`;
    backupJobs[id] = { step: 0, lines, message, result, then };
    return { job: id };
  };
  const backupJobView = (id, since) => {
    const j = backupJobs[id];
    j.step = Math.min(j.step + 1, j.lines.length);
    const done = j.step >= j.lines.length;
    if (done && j.then) { j.then(); j.then = null; }
    const state = done ? (j.result ? "done" : "failed") : "running";
    return { id, state, message: done ? j.message : "", lines: j.lines.slice(since, j.step), count: j.step,
      ...(state === "done" ? { result: j.result } : {}) };
  };

  window.pywebview = {
    api: {
      backup_status: async () => backupStatus(),
      backup_requested: async () => ({ make: mode === "firstbackup" && !backups.some((b) => b.matches) }),  // the installer asked
      backup_make: async (replace) => {
        if (backups.some((b) => b.matches) && !replace) throw new Error("There's already a backup of this build.");
        if (mode === "nospace") {
          return backupJob(["0%"], "There isn't enough free space on D:\\ for the backup: it needs 5.4 GB, and 2.1 GB is free. Free some space, then try again.", null);
        }
        return backupJob(steps(""), "The backup is made.", { path: `${BACKUPS}\\${BUILD}`, build: BUILD, files: 61, size: 5690000000, size_gb: 5.3 },
          () => { backups = [backupOf(BUILD, "2026-09-30 22:15")].concat(backups.filter((b) => !b.matches)); gameClean = true; });
      },
      backup_check: async (deep) => backupJob(steps(""), "The game's files are checked.",
        { build_matches: true, build: BUILD, backup_build: BUILD, ...gameDiffers(), files: 61, hashed: deep ? 61 : 2 }),
      backup_restore: async () => {
        if (mode === "running") return backupJob(steps("check "), "R.U.S.E. is running: RUSE.exe (process 4312). Close the game, then restore.", null);
        const d = gameDiffers();
        return backupJob(steps("check ").concat(steps("")), "The game's files are restored.",
          { restored: d.changed.length + d.missing.length, set_aside: d.added.length, kept: d.changed.length, left: [], build: BUILD,
            set_aside_to: d.added.length + d.changed.length ? `${BACKUPS}\\set-aside-2026-09-30-221503` : null }, () => { gameClean = true; });
      },
      steam_verify: async () => ({ opened: "steam://validate/21970" }),
      languages: async () => [{ code: "base", name: null }, { code: "us", name: "English" }, { code: "fr", name: "Français" },
        { code: "ger", name: "Deutsch" }, { code: "ita", name: "Italiano" }, { code: "spa", name: "Español" },
        { code: "pol", name: "Polski" }, { code: "ru", name: "Русский" }, { code: "cz", name: "Čeština" },
        { code: "jpn", name: "日本語" }, { code: "sc", name: "简体中文" }],
      strings: async (lang) => words_(lang),
      language_choice: async () => ({ suggested: mode === "lang" ? "fr" : "us", from: mode === "lang" ? "steam" : "pc",
        chosen: Boolean(prefs.lang_chosen) || !(mode === "lang" || mode === "noindex") }),
      nations: async (lang) => nations[lang] || nations.us,
      status: async () => mode === "noindex" ? { ready: false, can_build: true }
        : mode === "oldindex" ? { ready: false, can_build: true, old: true } : { ready: true, build: "24687178" },
      units: async (lang, kind = "all", nation = -1, search = "", group = "all") => {
        if (kind === "ammo") {
          const copies = myAmmo().map((n) => ({ address: ammoAddress(n.id), name: n.name, base_name: "Ammo_" + n.id, kind: "ammo",
            id: null, users: [], nations: nationsOf(ammo.find((a) => ammoAddress(a.id) === n.source), lang), nation: -1, nation_name: "", factory: null, slot: null, new: true, source: n.source,
            source_name: ammoName(ammo.find((a) => ammoAddress(a.id) === n.source), lang),
            group: ammo.find((a) => ammoAddress(a.id) === n.source).group }));
          const out = copies.concat(ammo.map((a) => ({ address: ammoAddress(a.id), name: ammoName(a, lang), base_name: "Ammo_" + a.id,
            kind: "ammo", id: a.ammoId, users: a.users.map((id) => nameOf(units.find((x) => x.id === id), lang)),
            nations: nationsOf(a, lang), nation: -1,
            nation_name: "", factory: null, slot: null, new: false, source: null, group: a.group })))
            .filter((a) => !search || a.name.toLowerCase().includes(search.toLowerCase()) ||
              a.users.some((x) => x.toLowerCase().includes(search.toLowerCase())));
          const order = ["ap", "he", "aa", "mg", "infantry_weapons", "antitank_weapons", "bombs", "rockets", "other"];
          return { units: out.filter((a) => group === "all" || a.group === group), total: ammo.length + copies.length,
            groups: order.filter((g) => out.some((a) => a.group === g)) };
        }
        const made = mine().map((n) => {
          const src = units.find((x) => E + x.id === n.source);
          return { id: n.id, kind: src.kind, nation: n.nation, factory: n.factory, slot: null, names: { us: n.name },
            new: true, source: n.source, group: groupOf(src) };
        });
        const shown = made.concat(units).filter((u) => (kind === "all" || u.kind === kind) && (nation < 0 || u.nation === nation));
        const present = new Set(shown.map((u) => u.group || groupOf(u)));
        // the game's own type of each unit (StudioApi.units: TypeUnitHintToken's text), the subsections under a kind
        const typeOf = (u) => { const t = FAKE_TYPES[u.new ? u.source.slice(E.length) : u.id]; return t ? t[lang] || t.us : null; };
        const types = ["ground", "infantry", "air"].includes(kind)
          ? [...new Set(shown.map(typeOf).filter(Boolean))] : [];
        const out = shown.filter((u) => group === "all" || (group.startsWith("type:") ? typeOf(u) === group.slice(5)
          : (u.group || groupOf(u)) === group))
          .map((u) => ({ address: E + u.id, name: u.new ? u.names.us : nameOf(u, lang), base_name: "Descriptor_Unit_" + u.id,
            kind: u.kind, nation: u.nation, nation_name: (nations[lang] || nations.us)[u.nation], factory: u.factory,
            slot: u.slot, new: Boolean(u.new), source: u.source || null, group: u.group || groupOf(u), type: typeOf(u),
            ...(u.new ? { game_name: u.names.us, desc: aboutOf(u.source).desc } : aboutOf(E + u.id)),
            decoy: (u.group || groupOf(u)) === "fake" }))
          .filter((u) => !search || u.name.toLowerCase().includes(search.toLowerCase()));
        return { units: out, total: units.length + made.length, groups: GROUPS.filter((g) => present.has(g)), types };
      },
      menus: async (lang) => {
        const names = nations[lang] || nations.us;
        return { nations: names.map((name, n) => {
          const factories = [...new Set(units.filter((u) => u.nation === n).map((u) => u.factory))].sort((a, b) => a - b);
          return { nation: n, name, factories: factories.map((f) => {
            const inside = units.filter((u) => u.nation === n && u.factory === f).sort((a, b) => a.slot - b.slot);
            return { factory: f, units: inside.slice(0, 3).map((u) => nameOf(u, lang)), count: inside.length };
          }) };
        }) };
      },
      new_unit: async (source, name, price, nation, factory) => {
        if (!current) throw new Error("Pick or make a mod first: a new unit is saved in a mod.");
        const src = units.find((u) => E + u.id === source);
        if (!src) throw new Error(`${source} isn't a unit or building, so it can't be copied here`);
        const stem = safeName(name) || `New_${mine().length + 1}`;
        if (units.some((u) => u.id === stem) || mine().some((n) => n.id === stem)) {
          throw new Error(`There's already a unit called Descriptor_Unit_${stem} (from '${name}'). Pick another name.`);
        }
        newUnits.push({ mod: current, id: stem, source, name, price: Math.round(price), nation: nation >= 0 ? nation : src.nation,
          factory: factory >= 0 ? factory : src.factory });
        return { address: newAddress(stem), name, saved: current + "/src/studio.rndf" };
      },
      weapons: async (address, lang) => weaponsOf(address, lang),
      prefs: async () => ({ ...prefs }),
      game_folder: async () => ({ path: fakeGame, picked: fakeGame === PICKED, version: "0.6.3" }),
      choose_game_folder: async () => { fakeGame = PICKED; return { path: fakeGame, picked: true, version: "0.6.3" }; },
      set_pref: async (key, value) => { if (value === null) delete prefs[key]; else prefs[key] = value; return { ...prefs }; },
      set_ammo: async (unitAddress, weapon, chosen) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const w = weaponsOf(unitAddress, "us");
        if (!w.weapons.some((x) => x.address === weapon)) throw new Error(`${weapon} isn't a weapon of ${unitAddress}`);
        if (!w.choices.some((c) => c.address === chosen)) throw new Error(`There's no ammunition at ${chosen}.`);
        const edited = chosen !== w.weapons[0].game_ammo;
        if (edited) edits.set(editKey(weapon, "Ammunition", ""), chosen); else edits.delete(editKey(weapon, "Ammunition", ""));
        return { saved: current + "/src/studio.rndf", ammo: chosen, edited };
      },
      // a weapon's range, as api.set_range: "shared" changes the ammo for every unit that fires it; "own" this unit only
      // (the weapon gets a copy of the ammo, Ammo_Range_..., unless no other unit fires it)
      set_range: async (unitAddress, weapon, value, mode) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const w = weaponsOf(unitAddress, "us").weapons.find((x) => x.address === weapon);
        if (!w) throw new Error(`${weapon} isn't a weapon of ${unitAddress}`);
        const alone = w.firing.every((f) => f.address === unitAddress);
        let target = w.ammo.address, copied = false;
        if (mode === "own" && !alone) {
          const c = myAmmo().find((n) => ammoAddress(n.id) === target);
          const stem = `Range_${unitAddress.split("/").pop().replace(/^Descriptor_[A-Za-z]+_/, "")}_1`;
          newAmmo.push({ mod: current, id: stem, source: c ? c.source : target, name: stem.replace(/_/g, " ") });
          edits.set(editKey(weapon, "Ammunition", ""), ammoAddress(stem));
          target = ammoAddress(stem);
          copied = true;
        }
        const key = editKey(target, "PorteeMaximale", "");
        if (value === rangeOf(target, true)) edits.delete(key); else edits.set(key, value);
        const c = myAmmo().find((n) => ammoAddress(n.id) === target);
        if (c && c.id.startsWith("Range_") && value === rangeOf(target, true) && alone) {  // back to the game's ammo
          edits.delete(editKey(weapon, "Ammunition", ""));
          newAmmo.splice(newAmmo.indexOf(c), 1);
          target = c.source;
        }
        return { saved: current + "/src/studio.rndf", ammo: target, range: value, copied };
      },
      new_ammo: async (source, name) => {
        if (!current) throw new Error("Pick or make a mod first: a copy is saved in a mod.");
        if (!ammo.some((a) => ammoAddress(a.id) === source)) throw new Error(`${source} isn't an ammunition, so it can't be copied here`);
        const stem = safeName(name) || `New_${myAmmo().length + 1}`;
        if (ammo.some((a) => a.id === stem) || myAmmo().some((n) => n.id === stem)) throw new Error(`There's already a copy at Ammo_${stem}. Pick another name.`);
        newAmmo.push({ mod: current, id: stem, source, name });
        return { address: ammoAddress(stem), name, saved: current + "/src/studio.rndf" };
      },
      flags: async (lang) => ({ flags: knownFlags.map((f) => ({ ...f, meaning: f.meaning ? (f.meaning[lang] || f.meaning.us) : null })) }),
      delete_unit: async (address) => {
        const j = newAmmo.findIndex((n) => n.mod === current && ammoAddress(n.id) === address);
        if (j >= 0) {
          const [gone] = newAmmo.splice(j, 1);
          for (const k of [...edits.keys()]) if (k.split("|")[1].startsWith(address) || edits.get(k) === address) edits.delete(k);
          return { deleted: address, source: gone.source, saved: current + "/src/studio.rndf" };
        }
        const i = newUnits.findIndex((n) => n.mod === current && newAddress(n.id) === address);
        if (i < 0) throw new Error(`${address} isn't a unit made in this mod, so it can't be deleted here`);
        const [gone] = newUnits.splice(i, 1);
        for (const k of [...edits.keys()]) if (k.split("|")[1].startsWith(address)) edits.delete(k);
        return { deleted: address, source: gone.source, saved: current + "/src/studio.rndf" };
      },
      unit: async (address, lang, via) => unit(address, lang, via),
      upgrade: async (address, lang) => upgradeOf(address, lang),
      set_upgrade: async (address, parent, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const game = upgradeOf(address, lang).game_parent;
        if ((game ? game.address : null) === parent) upgradeEdits.delete(address); else upgradeEdits.set(address, parent);
        return { saved: current + "/src/studio.rndf", ...upgradeOf(address, lang) };
      },
      set_research: async (address, prop, value) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const game = upgradeOf(address, "us").research[prop].game;
        const v = value === null ? null : Math.round(value);
        if (v === null || v === game) researchEdits.delete(`${address}|${prop}`); else researchEdits.set(`${address}|${prop}`, v);
        return { saved: current + "/src/studio.rndf", value: v === null ? game : v };
      },
      // a unit's look (?fake=noblender: Blender not found): every unit has one made-up model and two pictures
      look: async (address) => fakeLook(address),
      model_import: async (address, file, size) => {
        if (!fakeLook(address).new_unit) throw new Error("Only a new unit made in this mod can get a model of its own: copy the unit first.");
        await new Promise((r) => setTimeout(r, 400));
        fakeModels.set(address, { ...FAKE_IMPORT, scale: 2.46 * (size || 1) });
        return { model: fakeModels.get(address), ...fakeLook(address) };
      },
      model_import_remove: async (address) => { fakeModels.delete(address); return fakeLook(address); },
      look_open: async (address) => {
        if (mode === "noblender") throw new Error("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use Choose Blender… to show the Studio where blender.exe is.");
        fakeLooks.add(address);
        return { ...fakeLook(address), message: "Opening 1 model(s) in Blender. Paint on the model there, then come back and click Bring back: it saves your paint and puts it in your mod." };
      },
      look_bring_back: async (address) => {
        fakePainted.add(address);
        return { ...fakeLook(address), brought: [{ texture: "gen\\ww2\\fake\\tsccombcs_combineddsctexture01.tgv", kind: "colour" }],
                 message: `Brought back 1 painted picture(s) into ${current}. Click Test in game to see them.` };
      },
      unit_preview: async (address) => {
        const real = new URLSearchParams(location.search).get("preview");
        if (real) return { models: [{ url: real, name: "preview" }], paint: {}, card: fakeCard(address) };
        await new Promise((r) => setTimeout(r, 300));
        return { models: [{ url: fakeModelUrl(), name: "fake" }], card: fakeCard(address),
                 paint: fakePainted.has(address) ? { "gen\\ww2\\fake\\tsccombcs_combineddsctexture01.tgv": fakeShot("#8d2b22", "#6e1f18") } : {} };
      },
      look_card: async (address, picture) => {
        if (!picture.startsWith("data:image/png")) throw new Error("The card picture couldn't be read (not a PNG).");
        fakeCards.set(address, picture);
        return { card: fakeCard(address), message: `The card is in ${current} now. Click Test in game to see it in the build menu.` };
      },
      look_card_reset: async (address) => {
        fakeCards.delete(address);
        return { card: fakeCard(address), message: "The game's own card is back." };
      },
      choose_blender: async () => ({ blender: mode === "noblender" ? "" : "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" }),
      get_blender: async () => ({ url: "https://www.blender.org/download/" }),
      mods: async (kind) => kind === "map" ? mapsView() : modsView(),
      new_mod: async (name, kind) => {
        if (kind === "map") {
          const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "my-map";
          maps.push({ path: home + "maps/" + slug, name: slug });
          currentMap = home + "maps/" + slug;
          return mapsView();
        }
        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "my-mod";
        mods.push({ path: home + slug, name: slug });
        current = home + slug;
        return modsView();
      },
      choose_mod: async (path, kind) => kind === "map" ? (currentMap = path, mapsView()) : (current = path, modsView()),
      open_mod_folder: async () => {
        const path = "D:/Mods/another-mod";
        if (!mods.some((m) => m.path === path)) mods.push({ path, name: "another-mod" });
        current = path;
        return modsView();
      },
      edited: async () => [...new Set([...edits.keys()].filter((k) => k.startsWith(current + "|")).flatMap((k) => {
        const [, address, , how, via] = k.split("|");
        return how === "shared" ? BLAST_OWNERS.map((id) => E + id) : how === "own" ? [via] : [address.split(":")[0]];
      }))],
      edit: async (address, prop, value, how, via) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (address === BLAST && !["own", "shared"].includes(how)) throw new Error("change it for one unit, or for all");
        const r = unit(address, "us", via).groups.flatMap((g) => g.rows).find((x) => x.prop === prop);
        const whole = (v) => r.type === "float32" ? v : Math.sign(v) * Math.round(Math.abs(v));
        let v = Array.isArray(value) ? value.map(whole) : whole(value);
        if (prop === "InitialFlagSet") v = [...new Set(v)];
        const base = how === "own" && r.edited !== null ? [].concat(r.edited) : r.numbers;
        const same = [].concat(v).length === base.length && [].concat(v).every((x, i) => x === base[i]);
        if (same) edits.delete(editKey(address, prop, how, via)); else edits.set(editKey(address, prop, how, via), v);
        return { saved: current + "/src/studio.rndf", value: v };
      },
      reset: async (address, prop, how, via) => {
        edits.delete(editKey(address, prop, how, via));
        return { saved: current + "/src/studio.rndf" };
      },
      // the Economy tab (StudioApi.economy): a few of the game's values, as the real index has them
      economy: async (lang) => ({ ready: mode !== "noindex", groups: ECONOMY.map(([id, rows]) => ({ id, rows: rows.map(
        ([prop, label, type, game, atomic]) => ({ prop, label: lang === "base" ? prop : label, type, list: Array.isArray(game),
          game, atomic: atomic === undefined ? null : atomic, value: economyEdits.has(prop) ? economyEdits.get(prop) : null })) })) }),
      economy_edit: async (prop, value) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const row = ECONOMY.flatMap(([, rows]) => rows).find((r) => r[0] === prop);
        const whole = (v) => row[2] === "float32" ? v : Math.round(v);
        const v = Array.isArray(value) ? value.map(whole) : whole(value);
        if (JSON.stringify(v) === JSON.stringify(row[3])) economyEdits.delete(prop); else economyEdits.set(prop, v);
        return { saved: current + "/src/studio.rndf", value: v };
      },
      economy_reset: async (prop) => { economyEdits.delete(prop); return { saved: current + "/src/studio.rndf" }; },
      // the Music tab (StudioApi.music, ruse_studio.music): a few of the game's songs; each "game song" is a made-up
      // tone (the real Studio hands the page the game's own file)
      music: async () => ({ mod: Boolean(current), groups: MUSIC.map(([id, songs]) => ({ id, songs: [...songs.map(
        ([member, name, seconds, also, maps]) => ({ member, name, seconds, channels: 2, rate: 48000, also, maps,
          mine: musicMine.has(member) })),
        // the mod's new songs in a battle list ("new:list<N>/<name>", StudioApi.music)
        ...[...musicMine.keys()].filter((m) => id.startsWith("playlist") && m.startsWith(`new:list${Number(id.slice(-1)) + 1}/`))
          .map((m) => ({ member: m, name: m.split("/").pop().split("_").join(" "), seconds: 0, channels: 2, rate: 48000,
            also: [], maps: [], mine: true, new: true }))] })) }),
      // a unit's voice lines (StudioApi.unit_voices): the US medium tanks' set, for any tank; none for the rest
      unit_voices: async (address) => {
        if (!/Sherman|Lee|M4|M3/.test(address)) return { moments: [], shared: [], copy: false };
        return { copy: false, shared: ["LEE"], hidden: 3, moments: VOICES.map(([id, n, seconds]) => ({ id, lines: Array.from(
          { length: n }, (_, i) => { const member = `${VOICE_DIR}eu_mediumtank_${id.toLowerCase()}_${i + 1}.ess`;
            return { member, name: `${id} ${i + 1}`, version: i + 1, seconds, channels: 1, rate: 44100,
              mine: musicMine.has(member), also: [], maps: [] }; }) })) };
      },
      music_sound: async (member, which = "game") => {
        const song = MUSIC.flatMap(([, s]) => s).find((s) => s[0] === member)
          || (member.startsWith(VOICE_DIR) || member.startsWith("new:") || member.startsWith("layer:")
            ? [member, member.slice(VOICE_DIR.length), 2] : null);
        if (!song) throw new Error(`${member} isn't one of the game's songs`);
        if (which === "mod") {
          if (!musicMine.has(member)) throw new Error("This mod has no song of its own here.");
          return { url: musicMine.get(member), kind: "wav" };
        }
        return { url: fakeTone(Math.min(song[2], 12), 220 + 40 * (song[1].length % 7)), kind: "wav" };
      },
      // a map's background sound (StudioApi.map_sound, map_sound_use): its layers are heard and saved like songs
      map_sound: async (pack) => {
        const own = /swamp/i.test(pack) ? BACKGROUNDS[1] : BACKGROUNDS[0], use = mapSoundUse.get(pack) || own[0];
        const at = BACKGROUNDS.find((b) => b[0] === use);
        return { map: pack, own: own[0], use, seconds: at[3], mod: Boolean(currentMap),
          choices: [own, ...BACKGROUNDS.filter((b) => b !== own)].map(([file, name, heard, seconds]) => ({
            file, name, maps: heard, seconds, own: file === own[0], use: file === use })),
          layers: [1, 2, 3].map((n) => ({ member: `layer:${pack}/${n}`, n, mine: musicMine.has(`layer:${pack}/${n}`),
            seconds: at[3], channels: 2, rate: 48000 })) };
      },
      map_sound_use: async (pack, file, lang) => {
        if (!currentMap) throw new Error("Pick or make a map project first: a map's sounds are saved in it.");
        if (file) mapSoundUse.set(pack, file); else mapSoundUse.delete(pack);
        return window.pywebview.api.map_sound(pack, lang);
      },
      music_save: async (member, part, index, count) => {
        if (member.startsWith("layer:") ? !currentMap : !current) throw new Error("Pick or make a mod first: songs are saved in a mod.");
        if (index === 0) musicUpload.length = 0;
        musicUpload.push(part);
        if (index < count - 1) return { part: index };
        const bytes = musicUpload.map((p) => Uint8Array.from(atob(p), (c) => c.charCodeAt(0)));
        const blob = new Blob(bytes, { type: "audio/wav" });
        if (member.startsWith("new:")) {  // a new song: its name made safe, as StudioApi does
          const [list, name] = member.slice(4).split("/");
          member = `new:${list}/${name.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_+|_+$/g, "")}`;
        }
        musicMine.set(member, URL.createObjectURL(blob));
        if (member.startsWith("layer:")) {  // a map's background layer: in the map project (maps/<map>/background_<n>.wav)
          const [pack, n] = member.slice(6).split("/");
          return { saved: `${currentMap}/maps/${pack}/background_${n}.wav`, seconds: 0 };
        }
        return { saved: `${current}/files/replace/${member.split("\\").join("/")}.wav`, seconds: 0 };
      },
      music_reset: async (member) => { musicMine.delete(member); return { saved: current }; },
      // the AI tab (StudioApi.ai): a few of the game's sets of values, the bonus and some ruse cards
      ai: async (lang) => ({ ready: mode !== "noindex",
        words: { ai: "AI", difficulty: "Difficulty", profile: "Profile", nuclear: "Nuclear mode" },
        profiles: AI.map(([id, kind, index, name, hint, groups]) => ({ id, kind, index, name, hint,
          groups: groups.map(([gid, rows]) => ({ id: gid, rows: rows.map((r) => aiRowOf(id, lang, r)) })) })),
        bonuses: [{ id: AI_BONUS, rows: [
          aiRowOf(AI_BONUS, lang, ["BonusValue", "Extra preference for these units", "int32", 400]),
          { ...aiRowOf(AI_BONUS, lang, ["UnitIDs", "Units (by number)", "int32", [3008, 3009]]),
            names: aiNow(AI_BONUS, "UnitIDs").map((n) => ({ 3008: "NUCLEAR LONG TOM", 3009: "NUCLEAR HOWITZER" })[n] || String(n)) }] }],
        cards: AI_CARDS.map(([id, name, about, rows]) => ({ id, name, about, in_menu: rows.some((r) => r[0] === "ShowInMenu"),
          rows: rows.map((r) => aiRowOf(id, lang, r)) })) }),
      ai_edit: async (address, prop, value) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const row = aiGame(address, prop);
        const whole = (v) => row[2] === "float32" ? v : Math.round(v);
        const v = Array.isArray(value) ? value.map(whole) : whole(value);
        if (JSON.stringify(v) === JSON.stringify(row[3])) aiEdits.delete(`${address}|${prop}`);
        else aiEdits.set(`${address}|${prop}`, v);
        return { saved: current + "/src/studio.rndf", value: v, same_default: aiSame(address, prop) };
      },
      ai_reset: async (address, prop) => {
        aiEdits.delete(`${address}|${prop}`);
        return { saved: current + "/src/studio.rndf", same_default: aiSame(address, prop) };
      },
      // the All values tab (StudioApi.values_files...): the made-up objects of VALUE_OBJECTS
      values_files: async () => ({ pack: "ZZ_GladPatchableWin.dat", files: [
        { path: "genglad/patchable/flashinterface.cpp.gladndfbin", objects: 271 }, { path: VALUE_FILE, objects: 63686 }] }),
      values_find: async (file, words, prop, value, lang) => {
        await new Promise((r) => setTimeout(r, 150));
        const found = Object.entries(VALUE_OBJECTS).filter(([a, o]) => (!file || file === VALUE_FILE)
          && (words || "").split(/\s+/).filter(Boolean).every((wd) => (a + " " + o.class).toLowerCase().includes(wd.toLowerCase()))
          && (!prop && !value || o.rows.some((r) => r[0].toLowerCase().includes((prop || "").toLowerCase())
            && String(r[4] ?? r[5]).toLowerCase().includes((value || "").toLowerCase()))))
          .map(([a, o]) => ({ address: a, class: o.class, export: o.owner ? null : a, file: o.mine ? null : VALUE_FILE, index: o.index,
            name: lang === "base" ? null : o.name, match: prop || value ? (o.rows.filter((r) => r[0].toLowerCase().includes((prop || "").toLowerCase()))
              .map((r) => `${r[0]} = ${r[4] ?? r[5]}`)[0] || null) : null, mine: !!o.mine, deleted: valueDeleted.has(a.split(":")[0]) }));
        return { objects: found, total: found.length };
      },
      value_object: async (address, lang) => valuePage(address, lang),
      value_edit: async (address, prop, value, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const row = (VALUE_OBJECTS[address] || { rows: [] }).rows.find((r) => r[0] === prop);
        if (!row) throw new Error(`${address} has no ${prop}`);
        if (prop === "DescriptorId") throw new Error(`${prop} isn't changed here: the Studio keeps each of these numbers unique`);
        const t = valueTyped(row, value);
        if (t.same) valueEdits.delete(`${address}|${prop}`);
        else valueEdits.set(`${address}|${prop}`, { value: t.value, text: t.text, words: row[2] === "key" ? null : undefined });
        return { saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      value_reset: async (address, prop, lang) => {
        valueEdits.delete(`${address}|${prop}`);
        return { saved: current ? current + "/src/studio.rndf" : null, page: valuePage(address, lang) };
      },
      // a new text of the mod's own for a text value (StudioApi.value_text_new): pointed at, with its words
      value_text_new: async (address, prop, words, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (!String(words || "").trim()) throw new Error("Type the words first (one line).");
        const key = (String(words).replace(/[^A-Za-z0-9]/g, "").slice(0, 6) || "Text") + "_" + Math.random().toString(36).slice(2, 5);
        newWords.set(key, Object.fromEntries(VALUE_LANGS.map((l) => [l, String(words).trim()])));
        valueEdits.set(`${address}|${prop}`, { value: key, text: key, words: String(words).trim() });
        return { saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      // the Nations tab (StudioApi.nations_view, ruse_studio.nations): the seven nations, their lobby and army words
      // (value_words, above), their flags and how many units each has
      nations_view: async () => ({ mod: Boolean(current), nations: ["usa", "germany", "uk", "france", "italy", "ussr", "japan"].map((code, n) => {
        const nameKey = `NATION_${n < 6 ? n : 7}`, armyKey = n < 6 ? `NAT_NAME_${n}` : null;
        const wordsOf = (key) => VALUE_LANGS.map((lang) => ({ lang, game: valueGameWords(key),
          mine: valueWords.has(key) ? valueWords.get(key)[lang] ?? null : null }));
        const game = fakeBadge(NATION_COLOURS[n]), mine = nationFlags.get(n);
        return { nation: n, code, name_key: nameKey, army_key: armyKey, name: wordsOf(nameKey), army: armyKey ? wordsOf(armyKey) : null,
          flag: { texture: `gen\\ww2\\res2d\\interface\\flags\\flag_${code}.tgv`, width: 28, height: 28, own: Boolean(mine), url: mine || game, game_url: game },
          units: [92, 95, 90, 88, 79, 91, 77][n] };
      }) }),
      nation_flag_set: async (n, picture) => {
        if (!current) throw new Error("Pick or make a mod first: the flag goes into it.");
        nationFlags.set(Number(n), picture);
        return {};
      },
      nation_reset: async (n, what = "all") => {
        if (["flag", "all"].includes(what)) nationFlags.delete(Number(n));
        for (const [which, key] of [["name", `NATION_${n < 6 ? n : 7}`], ["army", `NAT_NAME_${n}`]]) {
          if (what === which || what === "all") valueWords.delete(key);
        }
        return {};
      },
      value_words: async (key) => newWords.has(key)
        ? { key, table: "ville_multi", new: true, words: VALUE_LANGS.map((lang) => ({ lang, game: null, mine: newWords.get(key)[lang] })) }
        : ({ key, table: valueGameWords(key) ? "baseunite" : null,
          words: valueGameWords(key) ? VALUE_LANGS.map((lang) => ({ lang, game: valueGameWords(key),
            mine: valueWords.has(key) ? valueWords.get(key)[lang] ?? null : null })) : [] }),
      value_words_set: async (key, texts) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (newWords.has(key)) {  // a new label's own text: every language kept, an empty one given the English
          const old = newWords.get(key), row = Object.fromEntries(VALUE_LANGS.map((lang) => [lang, (texts[lang] ?? old[lang]) || ""]));
          if (!row.us) throw new Error("The English words can't be empty: the other languages fall back to them.");
          for (const lang of VALUE_LANGS) row[lang] = row[lang] || row.us;
          newWords.set(key, row);
          return { key, table: "ville_multi", new: true, words: VALUE_LANGS.map((lang) => ({ lang, game: null, mine: row[lang] })) };
        }
        const row = Object.fromEntries(VALUE_LANGS.map((lang) => [lang, texts[lang] || valueGameWords(key) || ""]));
        if (VALUE_LANGS.every((lang) => row[lang] === valueGameWords(key))) valueWords.delete(key);
        else valueWords.set(key, row);
        return { key, table: "baseunite", words: VALUE_LANGS.map((lang) => ({ lang, game: valueGameWords(key),
          mine: valueWords.has(key) ? valueWords.get(key)[lang] : null })) };
      },
      value_links: async (address, prop, words) => ({ class: null, objects: Object.entries(VALUE_OBJECTS)
        .filter(([a, o]) => !o.owner && !valueDeleted.has(a) && a.toLowerCase().includes((words || "").toLowerCase()))
        .map(([a, o]) => ({ address: a, class: o.class, name: o.name })) }),
      // values added and taken out, objects made and deleted (StudioApi.value_prop_choices...): on VALUE_OBJECTS
      value_prop_choices: async (address, lang) => {
        const o = VALUE_OBJECTS[address];
        if (!o) throw new Error(`There's nothing at ${address} in this game build.`);
        const have = new Set(o.rows.map((r) => r[0]));
        return { class: o.class, props: (VALUE_KIND_PROPS[o.class] || []).filter(([prop]) => !have.has(prop))
          .map(([prop, label, kind, type, start]) => ({ prop, label: lang === "base" ? prop : label, kind, type,
            start: prop === "DescriptorId" ? "" : start, can: prop !== "DescriptorId" })) };
      },
      value_prop_add: async (address, prop, value, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const o = VALUE_OBJECTS[address];
        const spec = (VALUE_KIND_PROPS[o.class] || []).find(([p]) => p === prop);
        if (!spec || o.rows.some((r) => r[0] === prop)) throw new Error(`It has ${prop} already: change it on its row.`);
        const row = [prop, spec[1], spec[2], spec[3], null, null, null, { added: true }];
        const t = valueTyped(row, value);
        o.rows.push(row);
        valueEdits.set(`${address}|${prop}`, { value: t.value, text: t.text });
        return { saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      value_prop_delete: async (address, prop, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const o = VALUE_OBJECTS[address], i = o.rows.findIndex((r) => r[0] === prop);
        if (i < 0) throw new Error(`${address} has no ${prop}`);
        if (o.rows[i][7] && o.rows[i][7].added) { o.rows.splice(i, 1); valueEdits.delete(`${address}|${prop}`); }
        else valueEdits.set(`${address}|${prop}`, { value: null, text: null, removed: true });
        return { saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      value_pointing: async (address, prop) => {
        await new Promise((r) => setTimeout(r, 150));
        if (prop) return { users: [], total: 0, inside: 0, blocked: null };
        const o = VALUE_OBJECTS[address] || { users: [] };
        const mine = [...valueEdits.entries()].filter(([k, v]) => v.value === address && !k.startsWith(address + "|"))
          .map(([k]) => ({ address: k.split("|")[0], path: k.split("|")[1], name: null, mine: true }));
        const users = o.users.map(([a, path]) => ({ address: a, path, name: (VALUE_OBJECTS[a] || {}).name || null, mine: false }))
          .concat(mine);
        return { users, total: users.length, inside: 0, blocked: address === EV + "Descriptor_Unit_M4_Sherman" ? "listed" : null };
      },
      value_classes: async () => ({ classes: [{ class: "TAmmunition", count: 1610 }, { class: "TMountedWeaponDescriptor", count: 2207 },
        { class: "TUniteAuSolDescriptor", count: 512 }, { class: "TWeaponManagerDescriptor", count: 700 }] }),
      value_object_new: async (cls, name, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (!/^[A-Za-z_]\w*(?:-\w+)*$/.test(String(name || "").trim())) {  // as the mod format reads a name
          throw new Error("Give the new object a name of letters A-Z, digits and _, starting with a letter (like Ammo_My_Shell).");
        }
        if (!VALUE_KIND_PROPS[cls]) throw new Error(`${cls} isn't a kind of object the game's unit data has: pick one from the list.`);
        const address = EV + String(name).trim();
        if (VALUE_OBJECTS[address]) throw new Error(`There's already something called ${name} in the game or your mod. Pick another name.`);
        VALUE_OBJECTS[address] = { class: cls, name: null, index: null, users: [], rows: [], mine: true };
        return { address, saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      value_object_delete: async (address, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (VALUE_OBJECTS[address] && VALUE_OBJECTS[address].mine) {
          delete VALUE_OBJECTS[address];
          return { saved: current + "/src/studio.rndf", page: null };
        }
        if (address === EV + "Descriptor_Unit_M4_Sherman") {
          throw new Error("Descriptor_Unit_M4_Sherman can't be deleted: the game's list of units names it, and the game fails to load its units when one of them is missing. Hide it from the build menus instead (ShowInMenu).");
        }
        valueDeleted.add(address);
        return { saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      value_object_restore: async (address, lang) => {
        valueDeleted.delete(address);
        return { saved: current + "/src/studio.rndf", page: valuePage(address, lang) };
      },
      // the Files tab (StudioApi.files_packs / files_list / files_preview / files_export): made-up packs and files
      files_packs: async () => ({ packs: [{ id: "gameplay", file: "ZZ_GladPatchableWin.dat", size: 24000000, map: false },
        { id: "texts", file: "ZZ_Win.dat", size: 2100000000, map: false },
        { id: "map:DataMapIsland_v09.dat", file: "DataMapIsland_v09.dat", size: 46000000, map: true }] }),
      files_list: async (pack, nested, words) => {
        const key = (p) => `${current}|${pack}|${(nested || []).join(">")}|${p}`;
        const all = (nested && nested.length ? FAKE_FILES.inner : FAKE_FILES[pack] || [])
          .map((f) => ({ ...f, ...(fakeGameFiles.has(key(f.path)) ? { mine: "changed" } : {}) }))
          .concat(nested && nested.length ? [] : [...fakeGameFiles.entries()]
            .filter(([k, v]) => v === "added" && k.startsWith(`${current}|${pack}|`))
            .map(([k]) => ({ path: k.split("|").pop(), kind: "texture", size: 3720, mine: "added" })));
        const found = all.filter((f) => f.path.toLowerCase().includes(String(words || "").toLowerCase()));
        return { files: found, total: all.length, matching: found.length };
      },
      files_preview: async (pack, nested, path, mine) => {
        const state = fakeGameFiles.get(`${current}|${pack}|${(nested || []).join(">")}|${path}`);
        const f = [...Object.values(FAKE_FILES)].flat().find((x) => x.path === path) || { kind: state === "added" ? "texture" : "binary", size: 64 };
        const taken = ["texture", "table", "ndf"].includes(f.kind);
        const base = { path, size: f.size, changed: state === "changed", added: state === "added", showing_mine: Boolean(mine && state),
          can_change: taken && state !== "added", why_not: taken ? null : `${path}: this kind of file can't be checked by the build yet, so a mod can't change or add it` };
        if (f.kind === "ndf") return { ...base, kind: "ndf", objects: 63686, classes: 386, props: 3338, packed: true,
          top: [["TConstantInteger", 8520], ["TIntrinsicCall_2Param", 5350], ["TConstantFloat", 4577]] };
        if (f.kind === "texture") return { ...base, kind: "picture", width: 2, height: 2, full: [512, 512], format: "DXT1",
          picture: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGP4z8DwnoGB4T8D0wQGBgAs4AT/6hx7RQAAAABJRU5ErkJggg==" };
        if (f.kind === "table") return { ...base, kind: "table", count: 2, rows: [["N_UNI_137", "SHERMAN"], ["N_UNI_138", "PANZER IV"]] };
        if (f.kind === "pack") return { ...base, kind: "pack", files: FAKE_FILES.inner.length };
        return { ...base, kind: "bytes", lines: ["00000000  65 64 61 74 01 00 00 00                          edat...."], more: 0 };
      },
      // changing a game file in the mod (StudioApi.files_change / files_reset / files_add): as if a file were picked
      files_change: async (pack, nested, path) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        fakeGameFiles.set(`${current}|${pack}|${(nested || []).join(">")}|${path}`, "changed");
        return window.pywebview.api.files_preview(pack, nested, path, true);
      },
      files_reset: async (pack, nested, path) => {
        const key = `${current}|${pack}|${(nested || []).join(">")}|${path}`, was = fakeGameFiles.get(key);
        fakeGameFiles.delete(key);
        return was === "added" ? { path, gone: true } : window.pywebview.api.files_preview(pack, nested, path);
      },
      files_add: async (pack, name) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (!/^[A-Za-z0-9_][A-Za-z0-9_./-]*$/.test(String(name).trim()) || name.includes("..")) {
          throw new Error("Give the new file a name of letters, digits, _, - and dots (folders with /), like pictures/my_flag.tgv.");
        }
        const mod = String(current).split(/[\\/]/).pop();
        fakeGameFiles.set(`${current}|${pack}||mods\\${mod}\\${name.trim().replace(/\//g, "\\")}`, "added");
        return window.pywebview.api.files_list(pack, [], "");
      },
      files_export: async (pack, nested, path) => ({ saved: "C:\\Users\\You\\Desktop\\" + path.split("\\").pop() }),
      // private notes (StudioApi.note / note_set), per mod
      note: async (key) => ({ key, text: (fakeNotes.get(current) || {})[key] || "", can: Boolean(current) }),
      note_set: async (key, text) => {
        if (!current) throw new Error("Pick or make a mod first: notes are kept in it.");
        const notes = fakeNotes.get(current) || {};
        if (String(text).trim()) notes[key] = String(text).trimEnd(); else delete notes[key];
        fakeNotes.set(current, notes);
        return { key, text: notes[key] || "", can: true };
      },
      // the AI tab's scripts (StudioApi.ai_scripts / ai_script): a made-up list, and a made-up script (never the game's)
      ai_scripts: async () => ({ missing: mode === "noindex" ? "ImportError: a library isn't there" : null, scripts: [
        { path: "genpython\\1000\\test\\map\\m01_leipzig\\scripting\\effetmap.xyz", map: "1. COLDITZ CASTLE", part: "",
          file: "effetmap.xyz", detail: "m01_leipzig/scripting/effetmap.xyz" },
        { path: "genpython\\1000\\test\\map\\m04_cotentin\\scripting_chapter1\\effetmap.xyz",
          map: "D-Day / 10. UTAH BEACH / 11. THE HEDGEROW WAR …", part: "chapter1", file: "effetmap.xyz",
          detail: "m04_cotentin/scripting_chapter1/effetmap.xyz" },
        { path: "genpython\\1000\\test\\map\\supercrossroads4\\scripting_challenge\\effetmap.xyz", map: "Blitz / Anzio",
          part: "challenge", file: "effetmap.xyz", detail: "supercrossroads4/scripting_challenge/effetmap.xyz" }]
        .map((s) => ({ ...s, mine: fakeScripts.has(s.path) })) }),
      ai_script: async (path) => {
        await new Promise((r) => setTimeout(r, 600));  // a big one takes seconds
        const text = FAKE_SCRIPT;
        return { path, text, lines: text.split("\n").length - 1, mine: fakeScripts.get(path) ?? null,
          can_change: Boolean(current), compiler_missing: mode === "nocompiler" ? "the game's Python (2.5.1) isn't with this copy of the apps" : null };
      },
      // changing a script (StudioApi.ai_script_check / ai_script_save / ai_script_reset): a line with "oops" in it is the
      // made-up mistake the game's Python finds
      ai_script_check: async (path, text) => {
        const bad = text.split("\n").findIndex((l) => l.includes("oops"));
        return bad < 0 ? { ok: true, error: null, line: null } : { ok: false, error: "SyntaxError: invalid syntax", line: bad + 1 };
      },
      ai_script_save: async (path, text, kind) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const bad = text.split("\n").findIndex((l) => l.includes("oops"));
        if (bad >= 0) throw new Error(`The game's Python can't read this script (line ${bad + 1}): SyntaxError: invalid syntax. Nothing was saved.`);
        if (text.trim() === FAKE_SCRIPT.trim()) fakeScripts.delete(path); else fakeScripts.set(path, text);
        return { path, text: FAKE_SCRIPT, lines: FAKE_SCRIPT.split("\n").length - 1, mine: fakeScripts.get(path) ?? null,
          can_change: true, compiler_missing: null };
      },
      ai_script_reset: async (path) => {
        fakeScripts.delete(path);
        return { path, text: FAKE_SCRIPT, lines: FAKE_SCRIPT.split("\n").length - 1, mine: null, can_change: Boolean(current), compiler_missing: null };
      },
      script_outline: async (text) => ({ steps: text.split("\n").map((l, i) => [l, i + 1]).filter(([l]) => /^IR_\d+ = /.test(l))
        .map(([l, line], k) => ({ depth: k ? 1 : 0, ir: l.split(" ")[0], kind: k ? (l.includes("Wait") ? "wait" : "action") : "flow",
          label: l.split("(")[0].split(".").pop().replace("Descriptor", ""), line })) }),
      script_reference: async (words, kind) => ({ kinds: ["action", "condition", "objective"], classes: FAKE_PARTS
        .filter((c) => (!kind || c.kind === kind) && (c.name + c.label).toLowerCase().includes((words || "").toLowerCase())) }),
      test_in_game: async () => ({ job: "test" }),
      // a made-up road network: one road east-west across the island, one north-south (Stick to roads)
      map_road_graph: async () => ({ nodes: [[300000, 600000], [1000000, 600000], [655000, 350000], [655000, 900000]],
        edges: [[0, 1], [2, 3]], offset: { depot: 11696, hq: 13580 } }),
      test_problems: async () => ({ problems: mode !== "testmistakes" ? [] : [
        { text: FAKE_MISTAKES[0], mod: "test2", fixes: [
          { kind: "spawn_neutral", path: "maps/M04_cotentin/scenario.toml", what: "Unit_Konoe_Shidan" },
          { kind: "spawn_remove", path: "maps/M04_cotentin/scenario.toml", what: "Unit_Konoe_Shidan" },
          { kind: "spawns_neutral_all", path: "maps/M04_cotentin/scenario.toml", file: "leveldesign_3v3_v01.scenario", count: 57 },
          { kind: "spawns_remove_all", path: "maps/M04_cotentin/scenario.toml", file: "leveldesign_3v3_v01.scenario", count: 57 }] },
        { text: FAKE_MISTAKES[1], mod: "test2", fixes: [
          { kind: "road_remove", path: "maps/M04_cotentin/roads.toml", road: 2, points: [] }] }] }),
      test_fix: async (fix) => ({ done: fix.kind === "road_remove" ? `road ${fix.road}: taken out`
        : `${fix.count ? `${fix.count} team spawn(s) in ${fix.file}` : fix.what}: ${fix.kind.includes("neutral") ? "made neutral" : "taken out"}` }),
      mod_info: async () => ({ id: "sherman-test", name: "sherman-test", version: "0.1.0", authors: [], author: "",
        description: "Made in the RUSE Studio.", builds: [], data_revision: "", fingerprint: "" }),
      export_mod: async () => ({ job: "export" }),
      build_index: async () => ({ job: "index" }),
      job: async (id, since) => backupJobs[id] ? backupJobView(id, since || 0)
        : mode === "testfails" && id === "test"  // a test stopped by a leftover copy, as a player's was
        ? { state: "failed", message: "[WinError 5] Access is denied: 'D:\\RUSE-Instances\\studio-sherman-test.old'",
          lines: jobs.test[0].slice(0, 1), count: 1 }
        : mode === "testmistakes" && id === "test"  // a test the build stopped on two old mistakes (owner, 2026-10-02)
        ? { state: "failed", message: "These mods have errors (listed above). Nothing was changed.",
          lines: jobs.test[0].slice(0, 1).concat(FAKE_MISTAKES.map((t) => "  error    " + t)), count: 3,
          errors: FAKE_MISTAKES }
        : { state: "done", message: jobs[id][1], lines: jobs[id][0], count: jobs[id][0].length,
            ...(id === "export" ? { result: exported } : {}),  // the file for "Share your mod"
            ...(id === "check" ? { result: { pack: checkPack, findings: fakeFindings(checkPack) } } : {}) },
      share_info: async () => ({ repo: "sneadtristen6/Ruse-Mods", page: "https://github.com/sneadtristen6/Ruse-Mods",
        credit: "Made with RUSE Studio 0.9.8 (https://github.com/sneadtristen6/R.U.S.E-2.0-Project)" }),
      publish_mod: async () => ({ opened: "https://github.com/sneadtristen6/Ruse-Mods/issues/new?template=add-mod.yml",
        zip: "C:\\Users\\You\\Documents\\sherman-test-0.1.0.zip" }),
      maps: async () => ({ maps: fakeMaps }),
      duplicate_options: async (pack) => {
        const m = fakeMaps.find((x) => x.pack === pack) || {};
        const source = m.copy_of || pack;
        return { source, entries: FAKE_ENTRIES[source] || [], name: "", folder: currentMap,
          why: FAKE_ENTRIES[source] ? null : "No menu offers this map (BATTLES, OPERATIONS or the CAMPAIGN), so it has no entry to copy." };
      },
      duplicate_map: async (pack, name, entry, preset) => {  // preset: a blank start (the preview copies either way)
        const at = fakeMaps.findIndex((x) => x.pack === pack), m = fakeMaps[at];
        if (preset && !["blank_terrain"].includes(preset)) throw new Error(`There's no '${preset}' to start from.`);
        const own = (name.normalize("NFKD").replace(/[̀-ͯ]/g, "").match(/[A-Za-z0-9]+/g) || [])
          .map((x) => x[0].toUpperCase() + x.slice(1)).join("") || "NewMap";
        const kind = ((FAKE_ENTRIES[m.copy_of || pack] || []).find((e) => e.name === entry) || {}).kind || "battles";
        fakeMaps.splice(at + 1, 0, { ...m, pack: own, names: [name], paths: [own], file: `DataMap${own}_v09.dat`,
          kinds: [kind === "battles" ? "skirmish" : kind], titles: { us: [name], fr: [name], sc: [name] },
          copy_of: m.copy_of || pack });
        return { pack: own, maps: fakeMaps };
      },
      // a map's menu pictures (StudioApi.menu_pictures and its window's calls); no file picker here: as if menu.png /
      // menu-wide.png were picked, and Blender saved its pictures as soon as it opened
      menu_pictures: async (pack) => fakeMenu(pack),
      pick_menu_picture: async (pack, key) => {
        const s = fakeMenuState(pack);
        s[key] = key === "picture" ? "menu.png" : "menu-wide.png";
        if (key === "wide_picture") s.start_dots = false;
        return fakeMenu(pack);
      },
      clear_menu_picture: async (pack, key) => {
        const s = fakeMenuState(pack);
        s[key] = null;
        if (key === "wide_picture") s.start_dots = false;
        return fakeMenu(pack);
      },
      set_start_dots: async (pack, on) => {
        const s = fakeMenuState(pack);
        if (!s.wide_picture) throw new Error("The start dots go on the map's own 3D map picture: pick one or make it in Blender first. The game's own have their dots drawn in.");
        s.start_dots = Boolean(on);
        return fakeMenu(pack);
      },
      menu_pictures_blender: async (pack) => {
        Object.assign(fakeMenuState(pack), { scene: true, saved: true });
        return { ...fakeMenu(pack), message: "Opening Blender. Change anything you like, click Save menu pictures at the top of Blender's 3D view, then Bring back here." };
      },
      menu_pictures_bring_back: async (pack) => {
        const s = fakeMenuState(pack);
        if (!s.saved) return { ...fakeMenu(pack), message: "Nothing saved in Blender yet: click Save menu pictures at the top of Blender's 3D view first (it takes a minute or two), then Bring back." };
        Object.assign(s, { picture: "menu.png", wide_picture: "menu-wide.png", start_dots: true, saved: false });
        return { ...fakeMenu(pack), message: "Brought back both pictures. Click Test in game to see them in the menus." };
      },
      delete_map: async (pack) => {
        const at = fakeMaps.findIndex((x) => x.pack === pack);
        if (at < 0 || !fakeMaps[at].copy_of) throw new Error(`${pack} isn't a new map made in these map changes, so it can't be deleted here: the game's own maps stay.`);
        const [gone] = fakeMaps.splice(at, 1);
        return { deleted: gone.pack, copy_of: gone.copy_of, maps: fakeMaps };
      },
      map_view: async (pack, lod) => fakeGround(pack, lod || "lowdef"),
      map_ground: async () => ({ url: null }),
      map_models: async () => ({}),  // no game models in the preview: the shapes stay  // the made-up island has only its colours
      app_version: async () => ({ app: "Studio", version: "0.8.1" }),
      // the start-up log: here, the page's moment kept in window.fakeStartMarks (ms since the page began loading)
      start_mark: async (what) => { (window.fakeStartMarks = window.fakeStartMarks || {})[what] = performance.now(); return {}; },
      update_check: async () => mode === "update"
        ? { available: true, version: "9.9.9", current: "0.8.1", installed: true, size: 60000000,
            changes: [
              { version: "9.9.9", before: "A unit given to another nation crashed the game when built.",
                now: "It's built, fights and can be selected in any match." },
              { version: "9.9.9", before: "", now: "Transparency sliders for the map's layers." }],
            page: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases" }
        : { available: false, version: "0.8.1", current: "0.8.1" },
      update_install: async () => { throw new Error("The preview can't install updates."); },
      update_page: async () => ({ opened: "" }),
      help_links: async () => ({ wiki: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/wiki" }),
      open_help: async (what) => ({ opened: what }),
      report_problem: async (message) => ({ opened: `report: ${message}` }),
      troubleshoot: async () => fakeDoctor(),
      troubleshoot_fix: async (action) => {
        if (action === "close_game") { doctorState.running = false; return { done: 1, left: [] }; }
        if (action === "clear_leftovers") { doctorState.leftovers = false; return { done: 1, left: [] }; }
        throw new Error(`There's no fix called '${action}'.`);
      },
      map_scenery: async (pack) => fakeScenery(pack),
      scenery: async (pack) => ({ objects: current ? (placed.get(`${current}|${pack}`) || []) : [],
        erase: current ? (erased.get(`${current}|${pack}`) || []) : [], saved: null, mod: current }),
      scenery_erase: async (pack, areas) => {  // the same file's [[erase]] tables
        if (!current) throw new Error("Pick or make a mod first: what you place is saved in it.");
        const key = `${current}|${pack}`;
        const list = (erased.get(key) || []).concat(areas.map((a) => ({ what: ["vegetation", "prop"], types: [], ...a })));
        erased.set(key, list);
        return { count: list.length, saved: `${current}/maps/${pack}/scenery.toml` };
      },
      scenery_erase_undo: async (pack, count = 1) => {
        const key = `${current}|${pack}`, list = erased.get(key) || [], n = Math.min(count, list.length);
        erased.set(key, list.slice(0, list.length - n));
        return { count: list.length - n, removed: n, saved: null };
      },
      scenery_erased: async (pack) => {  // the made-up village's objects in the circles (the real count reads them all)
        const list = (current && erased.get(`${current}|${pack}`)) || [], d = fakeScenery(pack), takes = {};
        for (const [group, flat] of Object.entries(d.items)) {
          for (let k = 0; k < flat.length; k += 5) {
            const x = flat[k + 1], y = flat[k + 2];
            if (list.some((a) => a.what.includes(group) && (x - a.x) ** 2 + (y - a.y) ** 2 <= a.radius ** 2)) {
              takes[group] = (takes[group] || 0) + 1;
            }
          }
        }
        await new Promise((r) => setTimeout(r, 300));  // the real count takes a second or two
        return { count: list.length, takes, error: "" };
      },
      scenery_add: async (pack, objects) => {
        if (!current) throw new Error("Pick or make a mod first: what you place is saved in it.");
        const key = `${current}|${pack}`, list = (placed.get(key) || []).concat(objects);
        placed.set(key, list);
        return { count: list.length, saved: `${current}/maps/${pack}/scenery.toml` };
      },
      scenery_undo: async (pack, count = 1, objects = null) => {
        const key = `${current}|${pack}`, list = placed.get(key) || [];
        if (objects) {  // those objects, wherever they are (the last one like each)
          const left = list.slice(), same = (a, b) => ["type", "x", "y", "turn", "size"].every((k) => a[k] === b[k]);
          for (const o of objects.slice().reverse()) {
            const at = left.map((p) => same(p, o)).lastIndexOf(true);
            if (at >= 0) left.splice(at, 1);
          }
          placed.set(key, left);
          return { count: left.length, removed: list.length - left.length, saved: null };
        }
        const n = Math.min(count, list.length);
        placed.set(key, list.slice(0, list.length - n));
        return { count: list.length - n, removed: n, saved: null };
      },
      terrain: async (pack) => {
        if (!current) return { strokes: [], saved: null, mod: null };
        const list = terrains.get(`${current}|${pack}`) || [];
        return { strokes: list.map((s) => ({ height: 0, level: 0, weight: 1, ...s })), mod: current,
          saved: list.length ? `${current}/maps/${pack}/terrain.toml` : null };
      },
      map_cover: async () => {
        const n = 64, bits = new Uint8Array(n * n / 8);
        for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
          if ((c - 20) ** 2 + (r - 34) ** 2 < 49 || (c - 44) ** 2 / 4 + (r - 20) ** 2 < 16) bits[(r * n + c) >> 3] |= 1 << ((r * n + c) & 7);
        }
        return { size: n, box: [0, 0, 1310720, 1310720], bits: btoa(String.fromCharCode(...bits)) };
      },
      roads: async (pack) => ({ roads: (fakeRoads[pack] || []).map((points) => ({ points, join: 3000,
        crossings: fakeCrossings(pack, points) })), bridge: (fakeBridges[pack] || [])[0]?.type || null, mod: current,
        saved: null, take_out: current ? fakeTakeOut[`${current}|${pack}`] || [] : [] }),
      road_take_out: async (pack, roads, bridges) => {
        if (!current) throw new Error("Pick or make a mod first: the change is saved in it.");
        fakeTakeOut[`${current}|${pack}`] = [...(roads ? ["roads"] : []), ...(bridges ? ["bridges"] : [])];
        return window.pywebview.api.roads(pack);
      },
      map_bridges: async (pack) => ({ kinds: fakeBridges[pack] || [], kind: (fakeBridges[pack] || [])[0]?.type || null }),
      bridge_add: async (pack, kind, x, y, turn, length) => {
        if (!current) throw new Error("Pick or make a mod first: what you place is saved in it.");
        const k = (fakeBridges[pack] || []).find((b) => b.type === kind);
        if (!k) throw new Error(`${kind} isn't one of this map's own bridge kinds, so the map can't take it.`);
        if (!k.placed) throw new Error(`This map places no ${k.name} of its own, so there's no floor to copy for one: units would walk on the riverbed under it. Pick a kind the map places.`);
        if (length < k.least || length > k.most) throw new Error(`${k.name} stretches from ${Math.ceil(k.least / 260)} to ${Math.floor(k.most / 260)} m long`);
        const o = { type: kind, x, y, turn: (turn + k.turn) % 360, size: 1, solid: false,
          stretch: Math.round(Math.max(0.9, length / k.length) * 1e4) / 1e4, lift: k.lift };
        const key = `${current}|${pack}`, list = (placed.get(key) || []).concat([o]);
        placed.set(key, list);
        return { count: list.length, saved: `${current}/maps/${pack}/scenery.toml`, object: o };
      },
      map_check: async (pack) => {
        if (!current) throw new Error("Pick or make a mod first: the check builds it.");
        checkPack = pack;
        return { job: "check" };
      },
      road_add: async (pack, points) => { (fakeRoads[pack] = fakeRoads[pack] || []).push(points); return { count: fakeRoads[pack].length, saved: null }; },
      road_undo: async (pack, n = 1) => { const list = fakeRoads[pack] || []; const removed = Math.min(n, list.length);
        list.splice(list.length - removed, removed); return { count: list.length, removed, saved: null }; },
      map_roads: async () => ({ pieces: [  // a ring road and a straight crossing, in the made-up map's units
        200000, 650000, 200000, 350000, 350000, 200000, 650000, 200000,
        650000, 200000, 950000, 200000, 1100000, 350000, 1100000, 650000,
        1100000, 650000, 1100000, 950000, 950000, 1100000, 650000, 1100000,
        650000, 1100000, 350000, 1100000, 200000, 950000, 200000, 650000,
        200000, 650000, 500000, 650000, 800000, 650000, 1100000, 650000] }),
      map_movement: async () => {  // off the map's edge is closed to all; the cover wood above is closed to vehicles
        const n = 64, inf = new Uint8Array(n * n / 8), veh = new Uint8Array(n * n / 8);
        for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
          const i = r * n + c, bit = 1 << (i & 7);
          if ((c - 32) ** 2 + (r - 32) ** 2 > 29 ** 2) continue;
          inf[i >> 3] |= bit;
          if (!((c - 20) ** 2 + (r - 34) ** 2 < 49)) veh[i >> 3] |= bit;
        }
        const b64 = (a) => btoa(String.fromCharCode(...a));
        return { size: n, box: [0, 0, 1310720, 1310720], infantry: b64(inf), vehicles: b64(veh) };
      },
      map_scenarios: async (pack) => withScenarioEdits(pack),
      // a mission's three steps (StudioApi.mission_steps): a sample battle map's place in BATTLES, its chain, its texts
      mission_steps: async (pack, file) => ({
        kind: "mp", script: null,
        menu: { listed: true, address: "$/Misc/Globals/MultiPackManager:MultiPackList[0].MultiList[0]",
          ...missionMenuOrder(),
          values: [{ prop: "NbPlayers", label: "NbPlayers", value: 2 }, { prop: "MapSize", label: "MapSize", value: 1 }],
          texts: [{ prop: "Description", label: "Description", key: "0x00964A4E1D10AF16", words: "Blitz" }] },
        chain: { broken: 0, links: [
          { kind: "scenario-file", why: "scenario_file_ok", state: "ok", depth: 0, detail: "" },
          { kind: "scenario-cluster", why: "scenario_cluster_ok", state: "ok", depth: 0, detail: "" },
          { kind: "script", why: "optional", state: "optional", depth: 1, detail: "" },
          { kind: "dico-langs", why: "dico_langs_ok", state: "ok", depth: 2, detail: "us,fr,ger" },
          { kind: "mapload", why: "mapload_ok", state: "ok", depth: 0, detail: "" },
          { kind: "registration", why: "registration_ok", state: "ok", depth: 0, detail: "" },
          { kind: "pack", why: "pack_ok", state: "ok", depth: 1, detail: "" }] },
        texts: [{ key: "0x00964A4E1D10AF16", where: "menu", prop: "Description", line: null, words: "Blitz", mine: false }],
      }),
      // Move up / Move down / Game's order (StudioApi.mission_move, mission_order_reset): the sample's first group
      mission_move: async (pack, file, delta, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const at = missionOrder.indexOf("MP01"), to = at + (delta < 0 ? -1 : 1);
        if (to < 0) throw new Error("It can't move: it's already first in its group.");
        if (to > 2) throw new Error("It can't move: the mission next to it is in another of the game's lists, which keep their order.");
        [missionOrder[at], missionOrder[to]] = [missionOrder[to], missionOrder[at]];
        return window.pywebview.api.mission_steps(pack, file, lang);
      },
      mission_order_reset: async (pack, file, lang) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        missionOrder.splice(0, 3, "MP01", "MP02", "MP06");
        return window.pywebview.api.mission_steps(pack, file, lang);
      },
      scenario_move: async (pack, file, item, x, y) => {
        const e = scenEdits(pack);
        const old = e.moves.find((m) => m.file === file && m.item === item);
        e.moves = e.moves.filter((m) => m !== old).concat([{ file, item, x, y, camera: old && old.camera, rotation: old && old.rotation }]);
        return withScenarioEdits(pack);
      },
      scenario_turn_camera: async (pack, file, item, turn) => {
        const e = scenEdits(pack), old = e.moves.find((m) => m.file === file && m.item === item);
        const it = baseScenarios().scenarios.find((x) => x.file === file).items[item];
        e.moves = e.moves.filter((m) => m !== old).concat([{ ...(old || { file, item, x: it.x, y: it.y }), camera: turn }]);
        return withScenarioEdits(pack);
      },
      scenario_turn_start_camera: async (pack, number, turn) => {
        scenEdits(pack).starts[number].camera = turn;
        return withScenarioEdits(pack);
      },
      scenario_put_back: async (pack, file, item) => {
        const e = scenEdits(pack);
        e.moves = e.moves.filter((m) => !(m.file === file && m.item === item));
        e.removes = e.removes.filter((r) => !(r.file === file && r.item === item));
        return withScenarioEdits(pack);
      },
      scenario_sectors: async (pack, whole) => {
        scenEdits(pack).wholeMap = Boolean(whole);
        return withScenarioEdits(pack);
      },
      scenario_change: async (pack, file, item, field, value) => {
        const e = scenEdits(pack), s = baseScenarios().scenarios.find((x) => x.file === file);
        const it = s && s.items[item];
        if (!it) throw new Error(`${file} has no item ${item}`);
        if (field === "camp" && value !== -1 && s.kind === "skirmish") {
          throw new Error("A skirmish map's items stay neutral: a skirmish game spawns only neutral items, so the game would leave it out.");
        }
        e.changes = e.changes || [];
        let c = e.changes.find((x) => x.file === file && x.item === item);
        if (!c) { c = { file, item, values: {} }; e.changes.push(c); }
        const game = field === "camp" ? (it.camp ?? 0) : it[field];
        if (value === game) delete c.values[field]; else c.values[field] = value;
        if (!Object.keys(c.values).length) e.changes = e.changes.filter((x) => x !== c);
        return withScenarioEdits(pack);
      },
      scenario_remove: async (pack, file, items) => {
        const e = scenEdits(pack), base = baseScenarios().scenarios.find((x) => x.file === file);
        for (const item of [].concat(items)) {
          const it = base && base.items[item];
          if (!it) throw new Error(`${file} has no item ${item}`);
          if (it.kind === "StartingPoint") throw new Error("A starting point can't be taken out: every player needs one. Move it instead.");
          if (!e.removes.some((r) => r.file === file && r.item === item)) e.removes.push({ file, item, kind: it.kind });
          e.moves = e.moves.filter((m) => !(m.file === file && m.item === item));
        }
        return withScenarioEdits(pack);
      },
      scenario_spawn: async (pack, file, unit, x, y, camp = -1) => {
        scenEdits(pack).spawns.push({ file, what: unit.replace(E, "Unit_"), x, y, camp });
        return withScenarioEdits(pack);
      },
      // the mod check: one made-up broken file at first (as Studio 0.7.0 left one), set aside on request
      check_mod: async () => ({ mod: current, problems: current ? checkProblems : [] }),
      rename_map_folder: async () => ({ mod: current, problems: checkProblems }),
      set_aside: async (file) => {
        const p = checkProblems.find((x) => x.file === file);
        if (!p) throw new Error(`${file} isn't one of this mod's map files`);
        checkProblems = checkProblems.filter((x) => x !== p);
        return { mod: current, problems: checkProblems, kept: `${current}/${file.replace(".toml", ".broken.toml")}` };
      },
      scenario_spawn_many: async (pack, file, unit, points, camp = -1, rotation = 0) => {
        for (const [x, y] of points) scenEdits(pack).spawns.push({ file, what: unit.replace(E, "Unit_"), x, y, camp, rotation });
        return withScenarioEdits(pack);
      },
      scenario_move_spawn: async (pack, number, x, y) => {
        Object.assign(scenEdits(pack).spawns[number], { x, y });
        return withScenarioEdits(pack);
      },
      scenario_remove_spawn: async (pack, number) => {
        scenEdits(pack).spawns.splice(number, 1);
        return withScenarioEdits(pack);
      },
      scenario_add_start: async (pack, file, team, x, y) => {
        scenEdits(pack).starts.push({ file, team, x, y });
        return withScenarioEdits(pack);
      },
      // Add a name or zone (StudioApi.scenario_place and its move, change and take back), and a turn (scenario_turn)
      scenario_place: async (pack, file, kind, x, y, words = "") => {
        const e = scenEdits(pack);
        e.places = e.places || [];
        const s = withScenarioEdits(pack).scenarios.find((q) => q.file === file);
        const free = (stem) => { let n = 1; while (s.items.some((it) => it.name === `${stem}_${n}`)) n += 1; return `${stem}_${n}`; };
        if (kind === "LabelVille" || kind === "LabelMontagne") {
          if (!words.trim()) throw new Error("Type the name to show on the map first (one line).");
          const key = (words.replace(/[^A-Za-z0-9]/g, "").slice(0, 6) || "Name") + "_" + Math.random().toString(36).slice(2, 5);
          newWords.set(key, Object.fromEntries(VALUE_LANGS.map((lang) => [lang, words.trim()])));
          e.places.push({ file, kind, x, y, name: "", text: key, key });
        } else if (kind === "Name") e.places.push({ file, kind, x, y, name: free("point") });
        else e.places.push({ file, kind, x, y, name: free("zone"), ...(kind === "CircularZone" ? { radius: 50000 } : { width: 50000, height: 50000 }) });
        return withScenarioEdits(pack);
      },
      scenario_move_place: async (pack, number, x, y) => {
        Object.assign(scenEdits(pack).places[number], { x, y });
        return withScenarioEdits(pack);
      },
      scenario_place_set: async (pack, number, field, value) => {
        const p = scenEdits(pack).places[number];
        if (field === "name" && !String(value).trim()) throw new Error("Name is one line of 1 to 200 letters.");
        p[field] = field === "name" ? String(value).trim() : Number(value);
        return withScenarioEdits(pack);
      },
      scenario_remove_place: async (pack, number) => {
        const [gone] = scenEdits(pack).places.splice(number, 1);
        if (gone && gone.key) newWords.delete(gone.key);
        return withScenarioEdits(pack);
      },
      scenario_turn: async (pack, file, item, turn) => {
        const e = scenEdits(pack), old = e.moves.find((m) => m.file === file && m.item === item);
        const it = baseScenarios().scenarios.find((x) => x.file === file).items[item];
        if (!it.turns) throw new Error(`this ${it.kind} has no turn of its own to change`);
        const same = Math.abs(turn - it.turn) < 1e-4;
        const m = { ...(old || { file, item, x: it.x, y: it.y }), rotation: same ? null : turn };
        e.moves = e.moves.filter((q) => q !== old).concat(m.rotation !== null || m.camera || m.x !== it.x || m.y !== it.y ? [m] : []);
        return withScenarioEdits(pack);
      },
      scenario_move_start: async (pack, number, x, y) => {
        Object.assign(scenEdits(pack).starts[number], { x, y });
        return withScenarioEdits(pack);
      },
      scenario_remove_start: async (pack, number) => {
        scenEdits(pack).starts.splice(number, 1);
        return withScenarioEdits(pack);
      },
      // how many players: the made-up island is a two-team, 2-player map
      map_players: async (pack) => fakePlayers(pack),
      set_players: async (pack, n) => {
        if (!current) throw new Error("Pick or make a mod first: the player count is saved in it.");
        if (n === null) playerCounts.delete(`${current}|${pack}`); else playerCounts.set(`${current}|${pack}`, n);
        return fakePlayers(pack);
      },
      terrain_add: async (pack, strokes) => {
        if (!current) throw new Error("Pick or make a mod first: the shaped ground is saved in it.");
        const key = `${current}|${pack}`, list = (terrains.get(key) || []).concat(strokes);
        terrains.set(key, list);
        return { count: list.length, saved: `${current}/maps/${pack}/terrain.toml` };
      },
      terrain_undo: async (pack, count = 1) => {
        if (!current) throw new Error("Pick or make a mod first: the shaped ground is saved in it.");
        const key = `${current}|${pack}`, list = terrains.get(key) || [], n = Math.min(count, list.length);
        terrains.set(key, list.slice(0, list.length - n));
        return { count: list.length - n, removed: n, saved: list.length - n ? `${current}/maps/${pack}/terrain.toml` : null };
      },
    },
  };
  window.addEventListener("load", () => window.dispatchEvent(new Event("pywebviewready")));
})();
