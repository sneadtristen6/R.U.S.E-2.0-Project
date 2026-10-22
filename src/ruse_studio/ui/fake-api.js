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
      edit_installed: "Edit an installed mod…", edit_title: "Edit an installed mod",
      edit_lead: "The mods installed in the Launcher. Pick one: its units and maps open here. A mod made by someone else becomes a copy of your own with a name of its own, so its updates never touch your changes.",
      edit_none: "No mods are installed in the Launcher yet.", edit_has_units: "units and other changes", edit_has_maps: "maps",
      edit_by: "by {author}", edit_older: "A RUSE Mod Manager mod (.rmod): in your copy its value changes become Studio changes you can change; its new units, texts and files stay as they are.",
      edit_open: "Edit", tip_edit_open: "Open your own mod here: everything in it shows in the Units and Maps tabs, and your changes go into it.",
      tip_edit_copy: "Make a copy of this mod of your own, with a name of its own, and open it here with everything in it.",
      edit_yours: "Yours", edit_copy_lead: "{name} is {author}'s mod. Your changes go into a copy of your own; give it a name of its own:",
      edit_someone: "someone else", edit_copy_name: "Your copy's name", edit_copy_go: "Make my copy and edit",
      edit_search: "Search installed mods", tip_edit_search: "Type part of a mod's name, its author or what it does.", edit_no_match: "No installed mod matches that.",
      pp_stops: "The game would stop loading the mod here.", pp_item_n: "{item} {n}",
      pp_item_stroke: "Map Paint stroke", pp_item_erase: "erase area", pp_item_object: "placed object",
      pp_item_move: "moved map item", pp_item_remove: "removed map item", pp_item_set: "changed map item",
      pp_item_place: "named place", pp_item_spawn: "unit placed at the start", pp_item_start: "starting point",
      pp_item_paint: "cover paint", pp_item_block: "blocked area", pp_item_open: "opened area",
      pp_item_road: "new road", pp_file_terrain: "ground changes", pp_file_scenery: "placed and erased objects",
      pp_file_scenario: "starting points and placed units", pp_file_places: "named places",
      pp_file_items: "changed map items", pp_file_cover: "cover paint", pp_file_movement: "blocked and opened areas",
      pp_file_roads: "new roads", pp_file_map: "map settings", pp_key_level: "water height", pp_key_radius: "size",
      pp_key_size: "size", pp_key_x: "position", pp_key_y: "position", pp_key_x2: "end point", pp_key_y2: "end point",
      pp_key_colour: "colour", pp_key_brush: "tool", pp_key_weight: "strength", pp_key_what: "unit",
      pp_key_camp: "side", pp_key_trucks: "trucks", pp_key_name: "name",
      pp_missing: "On {map}, {item} is missing its {key}.",
      pp_unknown_key: "On {map}, {item} has a setting the game doesn't know: {key}.",
      pp_bad_value: "On {map}, {item} has a {key} the game can't use.",
      pp_bad_item: "On {map}, {item} has a value the game can't use.",
      pp_unreadable: "On {map}, the file of its {what} can't be read: it has a typing mistake.",
      pp_map_file: "On {map}, the file of its {what} has a mistake.",
      pp_unit_file: "The unit changes file {file} has a mistake on line {line}.",
      pp_text_file: "The text file {file} has a mistake on line {line}.",
      pp_manifest: "The mod's settings file (mod.toml) has a mistake.",
      pp_how_item: "Fix it with a button. Removing the {item} keeps everything else on the map, and the file as it was is kept beside it.",
      pp_how_file: "Put the file aside: it's kept, renamed, and the map goes without these changes until it's fixed. Details says exactly what's wrong.",
      pp_how_unit_file: "Put the file aside: it's kept, renamed, and the mod goes without the changes in it until it's fixed. Details says exactly what's wrong.",
      pp_how_studio_file: "This is the Studio's own record of your unit changes: putting it aside takes all of them out of the mod (the file is kept). Details says exactly what's wrong; ask on the Discord if you're not sure.",
      pp_how_manifest: "Open the mod's folder and correct mod.toml in a text editor. Details says exactly what's wrong.",
      pp_how_other: "Details says exactly what's wrong. Open the mod's folder to fix it by hand, or ask on the Discord.",
      pp_fix_fill_level: "Use the map's water height", pp_fix_fill: "Use the map's {key}",
      pp_fix_remove_key: "Take out {key}", pp_fix_remove_item: "Remove this {item}",
      pp_fix_open_folder: "Open the mod's folder", pp_details: "Details", pp_fixed: "Fixed.",
      tip_pp_fill: "Fills in the value the rest of the map has, the way Map Paint would. The file as it was is kept beside it.",
      tip_pp_remove_item: "Takes out just this one; everything else stays. The file as it was is kept beside it.",
      tip_pp_remove_key: "Takes out just this setting; the rest of the item stays. The file as it was is kept beside it.",
      tip_pp_open_folder: "Opens the mod's folder on your PC, to fix the file by hand.",
      tip_pp_details: "Shows the mistake as the game build reports it: handy when asking for help.",
      model_copy: "Give it its own copy of the model", tip_model_copy: "The same model with textures of its own: Repaint in Blender then changes only this unit, not the unit it copies.", model_copy_how: "Now it draws the model of the unit it copies, so a repaint changes both. With its own copy, a repaint changes only this one.", model_copy_has: "This unit has its own copy of the model: Repaint in Blender changes only this unit.", model_copy_remove: "Use the shared model again", tip_model_copy_remove: "Back to the model of the unit it copies. Its paint stays in the mod, for when it gets a copy again.",
      number_about_value: "about {v} {unit}", unit_m: "m", unit_kmh: "km/h", unit_ms2: "m/s²", unit_deg: "°", unit_degs: "° a second", unit_s: "s", unit_money: "$", unit_pct: "%", number_base: "Base stat {v}", number_from_base: "{pct}% from the base stat", number_slider: "{name}: smaller or larger", tip_number_slider: "Makes it smaller or larger than the game's value, {base} (its base stat): from -90% to +300%. Let go to save it. The box takes any exact number.", number_this_unit: "This unit: {v}", number_among: "Among the game's {n} of this kind (lowest, middle, highest):", number_scale_unmeasured: "(this scale comes from the community; not measured by us yet)", number_sure_tried: "seen in the game", number_sure_known: "certain, from the game's own data and menus", number_sure_community: "from the community, not checked by us yet", number_sure_name: "from its name and the values the game's units have; not tried yet",
      weapons_how_title: "How weapons and ammo work", weapons_how_1: "Each weapon (Weapon 1 is the main gun) fires one ammo. The list beside it picks which: any of the game's ammo, sorted by type (AP, HE, anti-aircraft, machine guns, bombs, rockets...), or a copy you made. Its muzzle flash and sound come with it.", weapons_how_2: "The ammo decides what the weapon does: its damage, its range, how fast it fires and what it can hit. Open the ammo to see and change those numbers.", weapons_how_3: "Changing an ammo's own numbers changes every unit that fires it (its page lists them). For this unit only: on the ammo's page click Copy this ammo..., change the copy, then pick the copy in the weapon's list here.", weapons_how_4: "Hits, under a weapon, picks whether it fires at the ground, at planes, or both. A plane's Role box (Fighter, Fighter-bomber, Bomber, Scout) sets how it attacks; a bomber drops its bombs from a bomb bay.", weapons_how_5: "Adding a weapon to a unit, or taking one off, isn't possible yet: weapons are tied to the model's animations, and we're not that far along yet.",
      flags_about: "Flags are on/off switches that tell the game what this unit is and what it can do. Hover a flag to see exactly what it does. The Studio checks this unit's flags every time you change them, and again before the game starts: it stops anything known to crash the game, and warns you about anything expected to break the unit.", flag_guide: "Flag guide: every flag explained", tip_flag_guide: "Opens the guide: every flag by what it's for, what it does, how to use it, how sure we are, and which ones crash the game.", flag_guide_title: "Unit flags: what each one is and does", flag_guide_lead: "Every flag the game reads (0 to 104). 'Tried in the game' means someone ran it in the game; 'from the game's units' comes from which of the game's own units have it; 'expected' is what studying the game says, not tried yet. Flags the game sets on its own while it runs do nothing in a unit's list. The Studio won't start the game with a flag marked 'crashes the game' where it crashes.", flag_guide_search: "Search: a number, a word (woods, truck, recon...)", flag_guide_none: "No flag matches that.", flag_how: "How to use it", flag_sure: "How sure we are", flag_sure_tried: "tried in the game", flag_sure_units: "from the game's units", flag_sure_expected: "expected, not tried yet", flag_sure_state: "the game sets it itself", flag_sure_unused: "unused", flag_danger_crash: "crashes the game", flag_danger_breaks: "can break the unit", flag_this_unit: "this unit has it", flag_crash_head: "This crashes the game:", flag_warn_head: "Expected to break the unit:", flag_take_off: "Take {n} off", flag_add_this: "Add {n}", flag_put_back: "Put {n} back", flag_blocked: "The Studio won't start the game with this mod until it's fixed, because the game would crash.", flag_crashes_here: "crashes the game on this unit", flag_breaks_here: "expected to break this unit", flag_group_kind: "What the unit is", flag_group_kind_help: "These decide what kind of unit the game treats it as: a plane, a truck, a building, infantry... Many only make sense on that kind of unit.", flag_group_combat: "Fighting", flag_group_combat_help: "Whether it fires, how, whether it can be hit, and whether it captures.", flag_group_movement: "Moving", flag_group_movement_help: "Where it can go: woods, off the map, standing still.", flag_group_sight: "Seeing and being seen", flag_group_sight_help: "How it sees and how enemies see it.", flag_group_player: "The player's control", flag_group_player_help: "Selecting it, clicking it, ordering it, and whether its team counts it. Keep these as the game has them.", flag_group_preview: "Placement previews", flag_group_preview_help: "Only for the see-through previews the game shows while you place something.", flag_group_state: "Set by the game while it runs", flag_group_state_help: "The game turns these on and off by itself (in combat, camouflaged, flying home...). Putting them in a unit's list does nothing, so leave them out.", flag_group_unused: "Unused", flag_group_unused_help: "Nothing in the game uses these: they do nothing.",
      uniform_title: "Uniform", uniform_default: "Default uniform: the game's own. Other squads and the gun and vehicle crews wear it too, so it isn't repainted here. Pick Custom uniform to give this squad one of its own.", uniform_custom: "Custom uniform", tip_uniform_custom: "Gives this squad a uniform of its own (its own copy of its soldiers), so what you paint after Open in Blender changes only this squad.", uniform_has: "Custom uniform: only this squad wears it. Paint it with Open in Blender, then Bring back.", uniform_default_again: "Back to the default uniform", tip_uniform_default_again: "This squad wears the game's uniform again. Your paint stays in the mod, for when it gets a custom one again.", uniform_shared_paint: "This mod repaints the default uniform itself ({n} picture(s)), so every squad and crew that wears it changes.", card_stale: "Its picture in the build menu still shows the game's paint.", card_take: "Take a new picture", tip_card_take: "Takes a picture of the unit with your paint, from the front corner, as its picture in the build menu.", card_choose: "Choose a picture…", tip_card_choose: "Use a picture file of your own (PNG or JPG). It's fitted to the card's size, cut at the edges if it has to be.", rides_in: "Rides in", tip_rides_in: "The truck this unit turns into on the roads. Pick another nation's, or a copy of a truck you made and repainted.", rides_in_how: "The truck it turns into on the roads. To give a squad a truck of its own look: open a truck, copy it, give the copy its own copy of the model and repaint it, then pick it here.", rides_in_game: "(the game's)", rides_in_mine: "(yours)", rides_in_open: "Open the truck", tip_rides_in_open: "Opens the truck's page: copy it there to give it a look of its own.",
      only_mod: "In this mod", tip_only_mod: "Show only what the mod being edited has: its new units and the ones it changes.",
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
      brush_look: "Look around", brush_undo: "Undo", brush_redo: "Redo",
      tip_place_redo: "Put back what Undo last took off the map (Ctrl+Y).",
      tip_road_redo: "Draw again the last road Undo took back (Ctrl+Y).",
      tip_bridges_redo: "Put back the last bridge Undo took off the map (Ctrl+Y).",
      tip_brush_redo: "Put back the last stroke Undo took back (Ctrl+Y).",
      tip_erase_redo: "Put back the last circles Undo took back (Ctrl+Y).",
      format_older: "{name} is in an older mod format ({have}; this Studio writes {now}). Update this mod brings its files up to date; a backup of the whole mod is kept first.",
      format_newer: "{name} was saved by a newer RUSE Studio (mod format {have}; this one knows {now}). Update the Studio before changing it: this one could drop what it doesn't know.",
      format_update: "Update this mod",
      tip_format_update: "Rewrite this mod's files the way this Studio reads them, keeping what they mean. A zip of the whole mod goes into the Studio's mod-backups folder first.",
      format_updated: "{name} is up to date. Its backup: {backup}",
      format_newer_ask: "{name} was saved by a newer RUSE Studio. This one could drop what it doesn't know when it saves. Open it anyway?",
      unsaved_title: "Close RUSE Studio?", unsaved_text: "Not everything is saved yet:",
      unsaved_close: "Close anyway? Yes closes it and loses that; No keeps the Studio open.",
      unsaved_script: "the AI tab's script has changes you haven't saved",
      unsaved_typed: "a box has text typed but not yet entered (press Enter or click elsewhere)",
      unsaved_music: "the music editor has a sound cut but not used yet", unsaved_saving: "a change is still being saved",
      unsaved_test: "Test in game is still building its copy",
      place_select: "Select",
      tip_place_select: "Pick what stands on the map, what this mod placed or the map's own: click one, Shift+click to add, or drag a box. Then drag to move, Turn and Size, or Delete.",
      sel_help: "Click to pick · Shift+click to add · drag a box around several · drag a picked one to move it · Delete takes them away · Esc picks none",
      sel_hint: "Click a building, prop or tree to pick it, or drag a box around several.",
      sel_one: "{name}: {whose}", sel_whose_map: "the map's own", sel_whose_mod: "placed by this mod",
      sel_many: "{n} picked: {own} of the map's own, {placed} placed by this mod",
      sel_delete: "Delete", tip_sel_delete: "Take what's picked off the map (Delete key). The map's own go when the mod is built; Undo puts them back.",
      sel_restore: "Put back as the map has it", tip_sel_restore: "The map's own picked objects go back where the map has them, as they were.",
      sel_clear: "Pick none", tip_sel_clear: "Pick nothing (Esc).", sel_nothing: "Nothing to pick there.",
      sel_more: "More than 2,000 in that box: the 2,000 nearest its middle are picked.",
      sel_box_ground: "Drag the box over the ground only.",
      tip_sel_undo: "Take back the last move, turn, size or delete (Ctrl+Z).",
      tip_sel_redo: "Do again the last move, turn, size or delete Undo took back (Ctrl+Y).",
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
      price_dates: "One price per game mode, in the game's order: 1945, 1942, 1939, Total War, Nuclear (each box is named). The host picks the mode when setting up a battle.",
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
      brush_strength_m: "Strength {m} m", brush_strength_pct: "Strength {n}%",
      tip_brush_strength_m: "How high one stroke raises the ground at its middle (or how deep it digs, how high the plateau or the water stands above where you click), in metres on this map: 100 is 60% of the map's height from its lowest to its highest point (- and = keys).",
      tip_brush_strength_pct: "How much of the way to the level one stroke moves the ground: 100% gets there in one stroke, less goes part of the way, so strokes build up (- and = keys).",
      tip_brush_angle: "Which way the square brush is turned, in degrees.",
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
      keys_head: "Keys: ", keys_move: "{k} or arrows move", keys_turn: "{k} turn", keys_zoom: "{k} zoom", keys_fast: "Shift faster", keys_brushes: "1-9 0 brushes", keys_brush: "{k} brush", keys_place: "{k} place", keys_look: "Esc look around", keys_undo: "Ctrl+Z undo, Ctrl+Y redo", keys_size: "{k} size", keys_strength: "{k} strength or turn", keys_change: "Change keys…", tip_keys_change: "Pick your own keys for the map view.", keys_press: "Press a key…", keys_reset: "Defaults", keys_fixed: "Click a key and press another. The arrows, Esc, Ctrl+Z and the digits stay as they are.", key_forward: "Forward", key_back: "Back", key_left: "Left", key_right: "Right", key_turn_left: "Turn left", key_turn_right: "Turn right", key_zoom_in: "Zoom in", key_zoom_out: "Zoom out", key_brush: "Brush", key_place: "Place", key_size_down: "Smaller", key_size_up: "Bigger", key_strength_down: "Weaker, or turn left", key_strength_up: "Stronger, or turn right",
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
      place_path: "Path", tip_place_path: "Click along the way, then double-click, press Enter or Finish: the picked object follows a smooth curve through your clicks (a hedge, a tree line). With a width, a belt of them; trees with Cover hide units.", place_path_help: "Click along the way; double-click, Enter or Finish places it. Esc drops a path half made.", place_path_next: "Click on along the way; double-click, Enter or Finish when it's done.", place_width: "Width {m} m", place_width_line: "Width: one line", tip_place_width: "0: one line of objects along the path. Wider than the spacing: a belt of them scattered along it, the spacing apart (a tree belt, a wood's edge).", place_cover: "Cover (units hide in it)", tip_place_cover: "A path of trees gives cover along it, as the Forest brush's woods do (placed trees alone give none): Cover strokes reaching half its width either side, 10 m at least. The place tray's Undo takes them back with the trees.", tip_place_finish: "Place the path clicked so far (or double-click, or Enter).", place_again: "Along the last path", tip_place_again: "Lay the picked object along the last path placed, at its own spacing and width: a hedge's bushes first, then pick a tree and add its trees.", place_placed_cover: "{n} trees placed with their cover and saved in the mod. Ctrl+Z takes them back in one go.", place_cover_left: "The trees are taken back; their cover stays, as brush strokes were made after it (Cover & movement's Undo takes those first).",
      place_line_count: "{n} objects along {m} m", place_grid: "Grid", tip_place_grid: "Rows of objects, as in Cities: Skylines: click where the first row starts and where it ends, then move out the rows and click. Near a road (Face the roads), the first row follows it.", place_grid_help: "Click where the first row starts, then where it ends; move out the rows and click to place them. Esc drops a grid half made.", place_grid_next: "Now click where the first row ends.", place_grid_rows: "Now move out the rows, and click to place them.", place_grid_count: "{n} objects: {per} in a row × {rows} rows", place_box: "Box", tip_place_box: "Drag a box on the ground: it fills with the picked object in rows, at the spacing along a row and the gap between rows.", place_box_help: "Drag a box on the ground and let go: it fills with the picked object.", place_box_count: "{n} objects: {cols} × {rows}, {w} × {h} m", place_rows: "Between rows {m} m", tip_place_rows: "How far apart the rows of a grid or a box are, centre to centre.", place_roads: "Face the roads", tip_place_roads: "Near a road, an object goes beside it and turns to face it, and a row follows it; a grid or a box leaves the roads clear. The turn slider still turns it (try 180° if a house shows its back).",
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
      brush_strength: "Force", brush_look: "Regarder", brush_undo: "Annuler", brush_redo: "Rétablir",
      tip_place_redo: "Remettre sur la carte ce que l'annulation vient de retirer (Ctrl+Y).",
      tip_road_redo: "Retracer la dernière route retirée par l'annulation (Ctrl+Y).",
      tip_bridges_redo: "Remettre le dernier pont retiré par l'annulation (Ctrl+Y).",
      tip_brush_redo: "Rétablir le dernier coup de pinceau annulé (Ctrl+Y).",
      tip_erase_redo: "Rétablir les derniers cercles annulés (Ctrl+Y).",
      format_older: "{name} est dans un format de mod plus ancien ({have} ; ce Studio écrit le {now}). Mettre ce mod à jour remet ses fichiers à niveau ; une sauvegarde du mod entier est gardée avant.",
      format_newer: "{name} a été enregistré par un RUSE Studio plus récent (format de mod {have} ; celui-ci connaît le {now}). Mettez le Studio à jour avant de le modifier : celui-ci pourrait perdre ce qu'il ne connaît pas.",
      format_update: "Mettre ce mod à jour",
      tip_format_update: "Réécrire les fichiers de ce mod comme ce Studio les lit, en gardant leur sens. Un zip du mod entier va d'abord dans le dossier mod-backups du Studio.",
      format_updated: "{name} est à jour. Sa sauvegarde : {backup}",
      format_newer_ask: "{name} a été enregistré par un RUSE Studio plus récent. Celui-ci pourrait perdre ce qu'il ne connaît pas en enregistrant. L'ouvrir quand même ?",
      unsaved_title: "Fermer RUSE Studio ?", unsaved_text: "Tout n'est pas encore enregistré :",
      unsaved_close: "Fermer quand même ? Oui ferme et perd cela ; Non garde le Studio ouvert.",
      unsaved_script: "le script de l'onglet IA a des changements non enregistrés",
      unsaved_typed: "une case contient du texte tapé mais pas encore validé (Entrée ou cliquer ailleurs)",
      unsaved_music: "l'éditeur de musique contient un son découpé mais pas encore utilisé",
      unsaved_saving: "un changement est encore en cours d'enregistrement",
      unsaved_test: "Tester en jeu construit encore sa copie",
      place_select: "Sélection",
      tip_place_select: "Choisir ce qui se trouve sur la carte, ce que ce mod a placé ou ce qui appartient à la carte : cliquer sur un objet, Maj+clic pour en ajouter, ou tracer un cadre. Puis glisser pour déplacer, Rotation et Taille, ou Supprimer.",
      sel_help: "Clic pour choisir · Maj+clic pour ajouter · tracer un cadre autour de plusieurs · glisser un objet choisi pour le déplacer · Suppr les retire · Échap pour ne rien choisir",
      sel_hint: "Cliquez sur un bâtiment, un objet ou un arbre pour le choisir, ou tracez un cadre autour de plusieurs.",
      sel_one: "{name} : {whose}", sel_whose_map: "propre à la carte", sel_whose_mod: "placé par ce mod",
      sel_many: "{n} choisis : {own} propres à la carte, {placed} placés par ce mod",
      sel_delete: "Supprimer", tip_sel_delete: "Retirer de la carte ce qui est choisi (touche Suppr). Les objets propres à la carte partent quand le mod est construit ; Annuler les remet.",
      sel_restore: "Remettre comme sur la carte", tip_sel_restore: "Les objets choisis propres à la carte reviennent à leur place d'origine, tels qu'ils étaient.",
      sel_clear: "Ne rien choisir", tip_sel_clear: "Ne rien choisir (Échap).", sel_nothing: "Rien à choisir ici.",
      sel_more: "Plus de 2 000 dans ce cadre : les 2 000 les plus proches du centre sont choisis.",
      sel_box_ground: "Tracez le cadre sur le sol uniquement.",
      tip_sel_undo: "Annuler le dernier déplacement, rotation, changement de taille ou suppression (Ctrl+Z).",
      tip_sel_redo: "Rétablir le dernier déplacement, rotation, changement de taille ou suppression annulé (Ctrl+Y).",
      brush_help: "Cliquez ou glissez sur le sol pour peindre · glisser du milieu pour tourner · clic droit pour déplacer · molette pour zoomer",
      brush_count: "Coups de pinceau sur cette carte : {n}",
      brush_note: "Enregistré dans le mod. « Tester en jeu » l'intègre à la carte.", brush_ramp: "Rampe",
      ramp_help: "Cliquez au début de la rampe, puis à sa fin. Échap annule.", brush_clear: "Tout effacer",
      really_clear: "Supprimer les {n} coups de pinceau de cette carte ?", remove_all: "Les supprimer",
      all_values: "les {n}", each_value: "régler chacun",
      price_dates: "Un prix par mode de jeu, dans l'ordre du jeu : 1945, 1942, 1939, Guerre totale, Nucléaire (chaque case est nommée). L'hôte choisit le mode en préparant la partie.",
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
      keys_head: "Touches : ", keys_move: "{k} ou flèches pour déplacer", keys_turn: "{k} tourner", keys_zoom: "{k} zoom", keys_fast: "Maj plus vite", keys_brushes: "1-9 0 pinceaux", keys_brush: "{k} pinceau", keys_place: "{k} placer", keys_look: "Échap regarder", keys_undo: "Ctrl+Z annuler, Ctrl+Y rétablir", keys_size: "{k} taille", keys_strength: "{k} force ou rotation", keys_change: "Changer les touches…", tip_keys_change: "Choisissez vos propres touches pour la vue carte.", keys_press: "Appuyez sur une touche…", keys_reset: "Par défaut", keys_fixed: "Cliquez sur une touche et appuyez sur une autre. Les flèches, Échap, Ctrl+Z et les chiffres ne changent pas.", key_forward: "Avancer", key_back: "Reculer", key_left: "Gauche", key_right: "Droite", key_turn_left: "Tourner à gauche", key_turn_right: "Tourner à droite", key_zoom_in: "Zoom avant", key_zoom_out: "Zoom arrière", key_brush: "Pinceau", key_place: "Placer", key_size_down: "Plus petit", key_size_up: "Plus grand", key_strength_down: "Moins fort, ou tourner à gauche", key_strength_up: "Plus fort, ou tourner à droite",
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
      place_path: "Tracé", tip_place_path: "Cliquez le long du trajet, puis double-cliquez, appuyez sur Entrée ou Terminer : l'objet choisi suit une courbe douce passant par vos clics (une haie, une rangée d'arbres). Avec une largeur, une bande d'objets ; des arbres avec Couvert cachent les unités.", place_path_help: "Cliquez le long du trajet ; un double-clic, Entrée ou Terminer le place. Échap abandonne un tracé commencé.", place_path_next: "Continuez à cliquer le long du trajet ; double-clic, Entrée ou Terminer quand c'est fini.", place_width: "Largeur {m} m", place_width_line: "Largeur : une seule ligne", tip_place_width: "0 : une seule ligne d'objets le long du tracé. Plus large que l'écart : une bande d'objets dispersés le long, à l'écart choisi (un rideau d'arbres, une lisière).", place_cover: "Couvert (les unités s'y cachent)", tip_place_cover: "Un tracé d'arbres donne du couvert le long de lui, comme les bois du pinceau Forêt (des arbres placés seuls n'en donnent pas) : des traits de Couvert sur la moitié de sa largeur de chaque côté, 10 m au moins. L'Annuler du panneau les retire avec les arbres.", tip_place_finish: "Placer le tracé cliqué jusqu'ici (ou double-clic, ou Entrée).", place_again: "Le long du dernier tracé", tip_place_again: "Poser l'objet choisi le long du dernier tracé placé, à son écart et sa largeur : d'abord les buissons d'une haie, puis choisissez un arbre et ajoutez ses arbres.", place_placed_cover: "{n} arbres placés avec leur couvert et enregistrés dans le mod. Ctrl+Z les retire d'un coup.", place_cover_left: "Les arbres sont retirés ; leur couvert reste, car des traits de pinceau ont été faits après (l'Annuler de Couvert et mouvement les retire d'abord).",
      place_line_count: "{n} objets sur {m} m", place_grid: "Grille", tip_place_grid: "Des rangées d'objets, comme dans Cities: Skylines : cliquez où commence la première rangée et où elle finit, puis écartez les rangées et cliquez. Près d'une route (Face aux routes), la première rangée la suit.", place_grid_help: "Cliquez où commence la première rangée, puis où elle finit ; écartez les rangées et cliquez pour les placer. Échap abandonne une grille commencée.", place_grid_next: "Cliquez maintenant où la première rangée finit.", place_grid_rows: "Écartez maintenant les rangées, puis cliquez pour les placer.", place_grid_count: "{n} objets : {per} par rangée × {rows} rangées", place_box: "Cadre", tip_place_box: "Tracez un cadre sur le sol : il se remplit de l'objet choisi en rangées, à l'écart le long d'une rangée et à l'espace entre les rangées.", place_box_help: "Tracez un cadre sur le sol et relâchez : il se remplit de l'objet choisi.", place_box_count: "{n} objets : {cols} × {rows}, {w} × {h} m", place_rows: "Entre rangées {m} m", tip_place_rows: "La distance entre les rangées d'une grille ou d'un cadre, de centre à centre.", place_roads: "Face aux routes", tip_place_roads: "Près d'une route, un objet se met à côté et se tourne vers elle, et une rangée la suit ; une grille ou un cadre laisse les routes libres. Le curseur d'orientation le tourne toujours (essayez 180° si une maison montre son dos).",
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
      all_values: "全部 {n} 个", each_value: "逐个设置", price_dates: "每个游戏模式一个价格，按游戏的顺序：1945、1942、1939、全面战争、核战争（每个框都有名称）。房主在创建游戏时选择模式。",
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
      keys_head: "按键：", keys_move: "{k} 或方向键移动", keys_turn: "{k} 旋转", keys_zoom: "{k} 缩放", keys_fast: "Shift 加速", keys_brushes: "1-9 0 选笔刷", keys_brush: "{k} 笔刷", keys_place: "{k} 放置", keys_look: "Esc 查看", keys_undo: "Ctrl+Z 撤销，Ctrl+Y 重做", keys_size: "{k} 大小", keys_strength: "{k} 强度或旋转", keys_change: "更改按键…", tip_keys_change: "为地图视图选择自己的按键。", keys_press: "按下一个键…", keys_reset: "默认", keys_fixed: "点击一个按键再按下新键。方向键、Esc、Ctrl+Z 和数字键保持不变。", key_forward: "前进", key_back: "后退", key_left: "左", key_right: "右", key_turn_left: "向左旋转", key_turn_right: "向右旋转", key_zoom_in: "放大", key_zoom_out: "缩小", key_brush: "笔刷", key_place: "放置", key_size_down: "变小", key_size_up: "变大", key_strength_down: "减弱，或向左旋转", key_strength_up: "增强，或向右旋转",
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
      tip_place_undo: "从地图上移除最后放置的物体（Ctrl+Z）。", brush_redo: "重做",
      place_path: "路径", tip_place_path: "沿路线点击，然后双击、按 Enter 或“完成”：所选物体沿经过各点的平滑曲线排列（树篱、一排树）。设置宽度则成一条带；带掩护的树木可隐藏部队。", place_path_help: "沿路线点击；双击、按 Enter 或“完成”放置。按 Esc 取消未完成的路径。", place_path_next: "继续沿路线点击；完成后双击、按 Enter 或“完成”。", place_width: "宽度 {m} 米", place_width_line: "宽度：单行", tip_place_width: "0：沿路径单行排列。宽于间距：沿路径按间距散布成带（林带、林缘）。", place_cover: "掩护（部队可隐藏其中）", tip_place_cover: "树木路径沿线提供掩护，如同森林笔刷的树林（单独放置的树没有掩护）：两侧各覆盖宽度的一半，至少 10 米。面板的撤销会连同树木一起撤回。", tip_place_finish: "放置目前点击的路径（也可双击或按 Enter）。", place_again: "沿上一条路径", tip_place_again: "将所选物体沿上一条放置的路径按其间距和宽度排列：先放树篱的灌木，再选一种树加上树木。", place_placed_cover: "已放置 {n} 棵树及其掩护并保存到模组。Ctrl+Z 可一次撤回。", place_cover_left: "树木已撤回；其后有笔刷操作，所以掩护保留（请先用“掩护与移动”的撤销撤回那些操作）。",
      place_line_count: "{m} 米内 {n} 个物体", place_grid: "网格", tip_place_grid: "像《城市：天际线》一样成排放置：点击第一排的起点和终点，再拉出更多排并点击。靠近道路时（面向道路），第一排会沿着道路。", place_grid_help: "点击第一排的起点，再点击终点；拉出更多排后点击放置。按 Esc 取消未完成的网格。", place_grid_next: "现在点击第一排的终点。", place_grid_rows: "现在拉出更多排，然后点击放置。", place_grid_count: "{n} 个物体：每排 {per} 个 × {rows} 排", place_box: "矩形", tip_place_box: "在地面上拖出一个矩形：按排内间距和排距，用所选物体成排填满。", place_box_help: "在地面上拖出矩形后松开：用所选物体填满。", place_box_count: "{n} 个物体：{cols} × {rows}，{w} × {h} 米", place_rows: "排距 {m} 米", tip_place_rows: "网格或矩形中各排之间的距离（中心到中心）。", place_roads: "面向道路", tip_place_roads: "靠近道路时，物体放在路边并朝向道路，一排会沿着道路；网格或矩形会避开道路。旋转滑块仍然有效（房子背对道路时试试 180°）。",
      tip_place_redo: "把“撤销”最后移除的物体放回地图（Ctrl+Y）。",
      tip_road_redo: "重新绘制被“撤销”的最后一条道路（Ctrl+Y）。",
      tip_bridges_redo: "放回被“撤销”移除的最后一座桥（Ctrl+Y）。",
      tip_brush_redo: "重做最后撤销的一笔（Ctrl+Y）。",
      tip_erase_redo: "重做最后撤销的圆圈（Ctrl+Y）。",
      format_older: "{name} 使用较旧的模组格式（{have}；此 Studio 写入 {now}）。“更新此模组”会让其文件跟上新格式；会先保留整个模组的备份。",
      format_newer: "{name} 是由较新的 RUSE Studio 保存的（模组格式 {have}；此版本只认识 {now}）。请先更新 Studio 再修改它：此版本可能会丢失它不认识的内容。",
      format_update: "更新此模组", tip_format_update: "按此 Studio 读取的方式重写此模组的文件，含义保持不变。会先把整个模组的 zip 放入 Studio 的 mod-backups 文件夹。",
      format_updated: "{name} 已是最新。其备份：{backup}",
      format_newer_ask: "{name} 是由较新的 RUSE Studio 保存的。此版本保存时可能会丢失它不认识的内容。仍要打开吗？",
      unsaved_title: "关闭 RUSE Studio？", unsaved_text: "还有内容尚未保存：",
      unsaved_close: "仍要关闭吗？“是”将关闭并丢失这些内容；“否”保持 Studio 打开。",
      unsaved_script: "AI 标签页的脚本有未保存的更改", unsaved_typed: "某个输入框中有尚未确认的文字（按 Enter 或点击别处）",
      unsaved_music: "音乐编辑器中有已剪辑但尚未使用的声音", unsaved_saving: "仍有更改正在保存",
      unsaved_test: "“在游戏中测试”仍在构建副本",
      place_select: "选择",
      tip_place_select: "选择地图上的物体（本模组放置的或地图原有的）：单击选中，Shift+单击添加，或拖出方框。然后拖动可移动，可调旋转和大小，或删除。",
      sel_help: "单击选择 · Shift+单击添加 · 拖出方框选多个 · 拖动已选物体以移动 · Delete 删除 · Esc 取消选择",
      sel_hint: "单击建筑、物件或树木以选中，或拖出方框选中多个。",
      sel_one: "{name}（{whose}）", sel_whose_map: "地图原有", sel_whose_mod: "本模组放置",
      sel_many: "已选 {n} 个：地图原有 {own} 个，本模组放置 {placed} 个",
      sel_delete: "删除", tip_sel_delete: "从地图上移除所选物体（Delete 键）。地图原有物体在构建模组时移除；“撤销”可放回。",
      sel_restore: "恢复为地图原样", tip_sel_restore: "所选的地图原有物体恢复到地图上的原位和原样。",
      sel_clear: "取消选择", tip_sel_clear: "取消全部选择（Esc）。", sel_nothing: "那里没有可选的物体。",
      sel_more: "方框内超过 2,000 个：已选中离中心最近的 2,000 个。",
      sel_box_ground: "请只在地面上拖出方框。",
      tip_sel_undo: "撤销最后一次移动、旋转、缩放或删除（Ctrl+Z）。",
      tip_sel_redo: "重做最后撤销的移动、旋转、缩放或删除（Ctrl+Y）。",
      place_one: "单个", place_area: "区域", place_line: "直线", tip_place_one: "每次点击地面放置一个物体。", tip_place_area: "在地面上拖动以填满区域：树林、村庄。物体之间至少保持所设间距。", tip_place_line: "先点击直线起点，再点击终点：按间距放置物体，并沿直线方向摆放（树篱、一排房屋）。", place_spacing: "间距 {m} 米", tip_place_spacing: "区域或直线中物体之间的距离（针对此类物体）。", place_area_size: "区域 {m} 米", tip_place_area_size: "区域笔刷的半径：一笔填充的宽度。", place_area_help: "在地面上拖动，用所选物体填满。中键拖动旋转视角，右键拖动平移。", place_line_help: "点击直线起点，再点击终点。按 Esc 取消未完成的直线。", place_line_next: "现在点击直线的终点。", place_none_room: "此处没有空间：间距范围内已都有物体。", place_placed: "已放置 {n} 个物体并保存到mod。Ctrl+Z 可一次撤销。", place_most: "一笔最多放置这么多；如需更多请再画一次。" },
  };
  // the troubleshooter's words (words.toml doc_*)
  Object.assign(words.us, { doc_button: "Troubleshoot", doc_title: "Troubleshooter", doc_intro: "What can stop a test or Play, checked in one go.", doc_checking: "Checking…", doc_again: "Check again", doc_copy: "Copy report", doc_copied: "Report copied: paste it into your bug report or on Discord.", doc_close: "Close", doc_fix_close_game: "Close R.U.S.E.", doc_fix_clear_leftovers: "Clear them", doc_fix_choose_game: "Choose folder…", doc_fixed: "Done ({done}).", doc_fix_left: "Not everything could be done: {left}", doc_game_ok: "R.U.S.E. found: {path}", doc_game_missing: "R.U.S.E. wasn't found. Choose its folder (the one with RUSE.exe).", doc_steam_ok: "Steam is running.", doc_steam_off: "Steam isn't running. It's started for you when you play.", doc_running_none: "No R.U.S.E. left running.", doc_running_copy: "R.U.S.E. is still running from a modded copy: {names}. Close it before the next test or Play.", doc_running_game: "R.U.S.E. is running (the Steam game): {names}. Close it before testing mods.", doc_drive_ok: "Modded copies go to {path} ({fs}).", doc_drive_other: "Modded copies go to {path}, on a {fs} drive: each copy is a full copy, and Windows may refuse to delete one while R.U.S.E. runs. An NTFS drive is best.", doc_space_ok: "{gb} GB free for modded copies.", doc_space_low: "Only {gb} GB free where modded copies go: a copy may need {need} GB.", doc_left_none: "No leftover copies.", doc_left: "Leftover copies: {names}. They only take up space; you can clear them now.", doc_left_held: "Leftover copies: {names}, held by {held}. Close that program, then clear them.", doc_readonly: "{n} of the game's files are marked read-only. That's fine: modded copies never keep the mark.", doc_write_ok: "The app can write where modded copies go.", doc_write_fail: "The app can't write to {path} ({why}). Check that folder's permissions, or whether an antivirus blocks it, or choose another folder for modded copies in Settings.", set_copies_title: "Where modded copies go", set_copies_help: "Test in game builds the modded copy of the game in this folder (the Launcher's Play too: one copy for the whole PC). The recommended place is RUSE-Instances on the game's drive: there the copy shares the game's files and is ready in seconds. On another drive it is a full copy of the game, slower and bigger. The game's clean backup goes beside it, in RUSE-Backup. After a change, the next Test in game builds in the new place; the old folder only takes up space and can be deleted by hand.", set_copies_none: "R.U.S.E. wasn't found yet, so the recommended place isn't known. Pick the game folder first.", set_copies_change: "Choose folder…", set_copies_default: "Use the recommended place", set_copies_changed: "Modded copies now go to {path}. The next Test in game builds there; the old folder only takes up space and can be deleted by hand.", set_copies_fixed: "Modded copies go to {path}, the folder given when the app started.", tip_copies_change: "Pick the folder the modded copies of the game are built in; the old folder stays until you delete it.", tip_copies_default: "Build the modded copies in RUSE-Instances on the game's drive again, the recommended place.", tip_copies_default_off: "Modded copies already go to the recommended place.", tip_copies_fixed: "The folder was given when the app started, so it can't be changed here.", doc_copies_recommended: "Modded copies go to {path}, the recommended place.", doc_copies_chosen: "Modded copies go to {path}, the folder chosen in Settings.", doc_copies_env: "Modded copies go to {path}, set by the RUSE_INSTANCES environment variable.", doc_copies_other_drive: "{path} is on another drive than the game ({drive}): each modded copy is a full copy of the game, slower to build and as big as the game. The recommended place is {recommended}.", doc_troubleshoot_link: "Troubleshoot" });
  Object.assign(words.fr, { doc_button: "Dépannage", doc_title: "Dépannage", doc_intro: "Ce qui peut bloquer un test ou « Jouer », vérifié en une fois.", doc_checking: "Vérification…", doc_again: "Vérifier à nouveau", doc_copy: "Copier le rapport", doc_copied: "Rapport copié : collez-le dans votre rapport de bug ou sur Discord.", doc_close: "Fermer", doc_fix_close_game: "Fermer R.U.S.E.", doc_fix_clear_leftovers: "Les supprimer", doc_fix_choose_game: "Choisir le dossier…", doc_fixed: "Fait ({done}).", doc_fix_left: "Tout n'a pas pu être fait : {left}", doc_game_ok: "R.U.S.E. trouvé : {path}", doc_game_missing: "R.U.S.E. est introuvable. Choisissez son dossier (celui qui contient RUSE.exe).", doc_steam_ok: "Steam est lancé.", doc_steam_off: "Steam n'est pas lancé. Il est démarré pour vous quand vous jouez.", doc_running_none: "Aucun R.U.S.E. resté ouvert.", doc_running_copy: "R.U.S.E. tourne encore depuis une copie avec mods : {names}. Fermez-le avant le prochain test ou « Jouer ».", doc_running_game: "R.U.S.E. est lancé (le jeu Steam) : {names}. Fermez-le avant de tester des mods.", doc_drive_ok: "Les copies avec mods vont dans {path} ({fs}).", doc_drive_other: "Les copies avec mods vont dans {path}, sur un disque {fs} : chaque copie est complète, et Windows peut refuser d'en supprimer une pendant que R.U.S.E. tourne. Un disque NTFS est préférable.", doc_space_ok: "{gb} Go libres pour les copies avec mods.", doc_space_low: "Seulement {gb} Go libres là où vont les copies avec mods : une copie peut demander {need} Go.", doc_left_none: "Aucune copie restante.", doc_left: "Copies restantes : {names}. Elles ne font qu'occuper de la place ; vous pouvez les supprimer dès maintenant.", doc_left_held: "Copies restantes : {names}, bloquées par {held}. Fermez ce programme, puis supprimez-les.", doc_readonly: "{n} fichiers du jeu sont en lecture seule. Ce n'est pas un problème : les copies avec mods ne gardent jamais cet attribut.", doc_write_ok: "L'application peut écrire là où vont les copies avec mods.", doc_write_fail: "L'application ne peut pas écrire dans {path} ({why}). Vérifiez les autorisations de ce dossier, ou si un antivirus le bloque, ou choisissez un autre dossier pour les copies avec les mods dans les Réglages.", doc_troubleshoot_link: "Dépannage" });
  Object.assign(words.sc, { doc_button: "故障排查", doc_title: "故障排查", doc_intro: "一次检查所有可能阻止测试或“开始游戏”的问题。", doc_checking: "正在检查…", doc_again: "重新检查", doc_copy: "复制报告", doc_copied: "报告已复制：请粘贴到你的错误报告或 Discord 中。", doc_close: "关闭", doc_fix_close_game: "关闭 R.U.S.E.", doc_fix_clear_leftovers: "清除", doc_fix_choose_game: "选择文件夹…", doc_fixed: "已完成（{done}）。", doc_fix_left: "部分操作未能完成：{left}", doc_game_ok: "已找到 R.U.S.E.：{path}", doc_game_missing: "未找到 R.U.S.E.。请选择其文件夹（包含 RUSE.exe 的那个）。", doc_steam_ok: "Steam 正在运行。", doc_steam_off: "Steam 未运行。开始游戏时会自动为你启动。", doc_running_none: "没有仍在运行的 R.U.S.E.。", doc_running_copy: "R.U.S.E. 仍在从模组版副本运行：{names}。请在下次测试或“开始游戏”前关闭它。", doc_running_game: "R.U.S.E.（Steam 游戏）正在运行：{names}。测试模组前请先关闭它。", doc_drive_ok: "模组版副本保存在 {path}（{fs}）。", doc_drive_other: "模组版副本保存在 {fs} 驱动器上的 {path}：每份都是完整副本，且 R.U.S.E. 运行时 Windows 可能拒绝删除它。最好使用 NTFS 驱动器。", doc_space_ok: "模组版副本可用空间：{gb} GB。", doc_space_low: "模组版副本所在位置仅剩 {gb} GB 可用空间：一份副本可能需要 {need} GB。", doc_left_none: "没有残留的副本。", doc_left: "残留的副本：{names}。它们只占用空间；你可以现在就清除。", doc_left_held: "残留的副本：{names}，被 {held} 占用。请关闭该程序，然后清除它们。", doc_readonly: "游戏有 {n} 个文件被标记为只读。这没有问题：模组版副本不会保留此标记。", doc_write_ok: "应用可以写入模组版副本所在的位置。", doc_write_fail: "应用无法写入 {path}（{why}）。请检查该文件夹的权限，或是否被杀毒软件拦截，或者在设置中为模组版副本选择另一个文件夹。", doc_troubleshoot_link: "故障排查" });
  // the clean game backup's words (words.toml backup_*, set_backup_*)
  Object.assign(words.us, { set_backup_title: "Clean game backup", set_backup_help: "RUSE Launcher and RUSE Studio never change the game's own folder, but other mod managers and hand edits can. Make a backup while the game is clean, right after Steam installs or verifies it. Check game files then shows what has changed since, and Restore clean files puts the game's files back.", backup_none: "No backup yet. It takes {need} GB; {free} GB is free on {drive}.", backup_have: "Backup of build {build}, made {date} ({size} GB): {path}", backup_other: "The backup is of build {build} (made {date}), but Steam has updated the game since (build {now}), so it can't be used. Verify with Steam, then make a new backup.", backup_make: "Make backup", backup_make_again: "Make backup again", backup_replace_ask: "This replaces the backup made {date}. Do it only if the game is clean now (use Verify with Steam first). Replace it?", backup_replace_yes: "Replace", backup_check: "Check game files", backup_deep: "Compare every byte (slower)", backup_restore: "Restore clean files", backup_restore_ask: "{n} file(s) will be copied back from the backup, and {m} file(s) that aren't the game's will be moved into a folder in {path}. Nothing is deleted. Restore?", backup_restore_yes: "Restore", backup_verify: "Verify with Steam", backup_verify_tip: "Steam's own repair: it checks every file and downloads the ones that changed. No backup needed.", backup_verify_opened: "Steam is checking the game's files and downloads any that changed; Steam shows how far it is.", backup_making: "Making the backup… {pct}", backup_checking: "Checking the game's files… {pct}", backup_restoring: "Restoring the game's files… {pct}", backup_made: "Backup made: {files} files, {size} GB.", backup_clean: "The game's files match the backup: nothing has changed.", backup_differs: "{n} file(s) differ from the backup:", backup_changed: "Changed ({n})", backup_missing: "Missing ({n})", backup_added: "Not the game's ({n})", backup_more: "…and {n} more", backup_nothing: "Nothing to restore: the game's files match the backup.", backup_restored: "Done: {n} file(s) restored.", backup_set_aside: "{m} file(s) that weren't the game's are now in {path}.", backup_kept: "The {k} changed file(s) that were replaced are kept in {path}." });
  Object.assign(words.fr, { set_backup_title: "Sauvegarde propre du jeu", set_backup_help: "RUSE Launcher et RUSE Studio ne modifient jamais le dossier du jeu, mais d'autres gestionnaires de mods et des modifications à la main peuvent le faire. Faites une sauvegarde pendant que le jeu est propre, juste après que Steam l'a installé ou vérifié. « Vérifier les fichiers du jeu » montre ensuite ce qui a changé depuis, et « Restaurer les fichiers propres » remet les fichiers du jeu en place.", backup_none: "Pas encore de sauvegarde. Elle demande {need} Go ; {free} Go sont libres sur {drive}.", backup_have: "Sauvegarde de la version {build}, faite le {date} ({size} Go) : {path}", backup_other: "La sauvegarde est de la version {build} (faite le {date}), mais Steam a mis le jeu à jour depuis (version {now}) : elle ne peut pas servir. Vérifiez avec Steam, puis faites une nouvelle sauvegarde.", backup_make: "Faire une sauvegarde", backup_make_again: "Refaire la sauvegarde", backup_replace_ask: "Ceci remplace la sauvegarde faite le {date}. Ne le faites que si le jeu est propre maintenant (utilisez d'abord « Vérifier avec Steam »). La remplacer ?", backup_replace_yes: "Remplacer", backup_check: "Vérifier les fichiers du jeu", backup_deep: "Comparer chaque octet (plus lent)", backup_restore: "Restaurer les fichiers propres", backup_restore_ask: "{n} fichier(s) seront recopiés depuis la sauvegarde, et {m} fichier(s) qui ne sont pas ceux du jeu seront déplacés dans un dossier de {path}. Rien n'est supprimé. Restaurer ?", backup_restore_yes: "Restaurer", backup_verify: "Vérifier avec Steam", backup_verify_tip: "La réparation de Steam : il vérifie chaque fichier et retélécharge ceux qui ont changé. Aucune sauvegarde nécessaire.", backup_verify_opened: "Steam vérifie les fichiers du jeu et retélécharge ceux qui ont changé ; Steam affiche sa progression.", backup_making: "Sauvegarde en cours… {pct}", backup_checking: "Vérification des fichiers du jeu… {pct}", backup_restoring: "Restauration des fichiers du jeu… {pct}", backup_made: "Sauvegarde faite : {files} fichiers, {size} Go.", backup_clean: "Les fichiers du jeu correspondent à la sauvegarde : rien n'a changé.", backup_differs: "{n} fichier(s) diffèrent de la sauvegarde :", backup_changed: "Modifiés ({n})", backup_missing: "Manquants ({n})", backup_added: "Pas du jeu ({n})", backup_more: "…et {n} de plus", backup_nothing: "Rien à restaurer : les fichiers du jeu correspondent à la sauvegarde.", backup_restored: "Terminé : {n} fichier(s) restauré(s).", backup_set_aside: "{m} fichier(s) qui n'étaient pas ceux du jeu sont maintenant dans {path}.", backup_kept: "Les {k} fichier(s) modifié(s) qui ont été remplacés sont conservés dans {path}." });
  Object.assign(words.sc, { set_backup_title: "游戏的干净备份", set_backup_help: "RUSE Launcher 和 RUSE Studio 从不修改游戏本身的文件夹，但其他模组管理器和手动修改可能会。请在游戏干净时（Steam 刚安装或验证完之后）创建备份。之后，“检查游戏文件”会显示自那以后改变了什么，“恢复干净文件”会把游戏文件还原。", backup_none: "还没有备份。需要 {need} GB；{drive} 上有 {free} GB 可用。", backup_have: "版本 {build} 的备份，创建于 {date}（{size} GB）：{path}", backup_other: "备份来自版本 {build}（创建于 {date}），但 Steam 之后更新了游戏（版本 {now}），因此无法使用。请先通过 Steam 验证，然后创建新的备份。", backup_make: "创建备份", backup_make_again: "重新创建备份", backup_replace_ask: "这将替换创建于 {date} 的备份。只有在游戏现在是干净的时候才这样做（请先使用“通过 Steam 验证”）。要替换吗？", backup_replace_yes: "替换", backup_check: "检查游戏文件", backup_deep: "逐字节比较（较慢）", backup_restore: "恢复干净文件", backup_restore_ask: "将从备份复制回 {n} 个文件，并把 {m} 个不属于游戏的文件移到 {path} 中的一个文件夹。不会删除任何东西。要恢复吗？", backup_restore_yes: "恢复", backup_verify: "通过 Steam 验证", backup_verify_tip: "Steam 自带的修复：检查每个文件并重新下载有变化的文件。不需要备份。", backup_verify_opened: "Steam 正在检查游戏文件，并重新下载有变化的文件；进度显示在 Steam 中。", backup_making: "正在创建备份… {pct}", backup_checking: "正在检查游戏文件… {pct}", backup_restoring: "正在恢复游戏文件… {pct}", backup_made: "备份已创建：{files} 个文件，{size} GB。", backup_clean: "游戏文件与备份一致：没有任何变化。", backup_differs: "与备份不同的文件：{n} 个", backup_changed: "已更改（{n}）", backup_missing: "缺失（{n}）", backup_added: "不属于游戏（{n}）", backup_more: "…还有 {n} 个", backup_nothing: "无需恢复：游戏文件与备份一致。", backup_restored: "完成：已恢复 {n} 个文件。", backup_set_aside: "{m} 个不属于游戏的文件现在位于 {path}。", backup_kept: "被替换的 {k} 个已更改文件保存在 {path}。" });
  // a panel's size handle (words.toml tip_panel_size)
  Object.assign(words.us, { armour_title: "Armour", armour_help: "How hard this unit is to hurt, as one of the game's own levels. The fights use it, and its card and build menu show its picture: tanks have levels 1 to 5, the number on the shield.", armour_level: "Level", tip_armour_pick: "Pick one of the game's armour levels: the unit fights with it, and its card and build menu show it.", tip_armour_undo: "Give it the game's armour level again.", armour_tank: "Armour {n}", armour_light: "Light vehicles (transports)", armour_infantry: "Infantry", armour_aircraft: "Aircraft", armour_para: "Paratroopers coming down", armour_trucks: "Construction trucks", armour_building: "Buildings and fortifications", armour_old_way: "This unit's armour was changed inside its armour part: it fights with the new value, but its card and build menu still show the old one. Pick its level here to fix that.", armour_on_unit: "Armour is changed on the unit's own page, under Armour: each level of the game has its own picture on the card, so a number changed here would fight differently from what the card shows.", model_propellers: "Its propellers spin as the game's do ({n} discs).", model_propellers_none: "{n} propeller discs left out: the unit it copies has no propellers to spin them.", model_propellers_far: "{n} propeller discs left out: they aren't where the copied plane's propellers are." });
  Object.assign(words.us, { role_title: "Role", role_help: "What kind of plane it is: how it flies and attacks. A bomber drops its bombs on a straight run from a bomb bay; a fighter-bomber dives at its target. Changing it also changes its build menu words and how the computer players use it.", role_fighter: "Fighter", role_fighter_bomber: "Fighter-bomber", role_bomber: "Bomber", role_scout: "Scout", role_paratroop: "Paratroop plane", role_paratroop_why: "A paratroop plane carries paratroopers, which no other plane has: its role stays.", role_not_tried: "{role} (not tried in the game yet)", role_bombs_moved: "As a bomber, its bombs drop from a bomb bay (copied from a game bomber's), the only way a bomber's run drops them.", tip_role_pick: "Pick what kind of plane it is. A plane needs a weapon firing bombs to be a bomber.", tip_role_undo: "Give it back the game's role, its bombs back where they were.", hits: "Hits", hits_ground: "The ground", hits_planes: "Planes", hits_both: "The ground and planes", tip_hits: "What this weapon can hit. Planes: its ammo gets a copy that hits planes and does nothing to the ground. Both: it keeps its ammo and gets a second weapon beside it for the other, the way the game's AA guns do.", hits_not_tried: "Tank rounds and AA guns shooting planes were seen in the game (2026-10-14); a plane's guns made to hit the ground, not yet." });
  Object.assign(words.us, { role_scout_armed: "Scout, keeping its attacks", ground_role_help: "Recon: the game's recon cars' sight (much further than a tank's), how the computer players use them, their build menu words, and it can go into woods. It stays as tough and armed as it is.", ground_role_game: "As the game has it", ground_role_recon: "Recon", tip_ground_role: "Make this vehicle a recon unit, or keep it as the game has it.", ground_role_recon_already: "This is one of the game's own recon units." });
  Object.assign(words.us, { tip_panel_size:"Size {n}%: drag down to make this panel smaller, up to make it bigger (the mouse wheel works too). Double-click: normal size." });
  Object.assign(words.fr, { tip_panel_size: "Taille {n} % : glissez vers le bas pour réduire ce panneau, vers le haut pour l'agrandir (la molette marche aussi). Double-clic : taille normale." });
  // Map Paint's Texture panel, palette and brush patterns (words.toml tex_*, tip_tex_*, pal_*, gtex_*, paint_*, stamp_*, mask_*)
  Object.assign(words.us, {"tip_paint_swatch_now": "The colour you paint with.", "tip_paint_hex": "The colour as #rrggbb (red, green, blue in hex): type one and press Enter.", "tip_paint_wheel": "Drag round the ring to pick the colour, and in the square to make it stronger or paler, lighter or darker.", "paint_eyedropper": "Eyedropper", "tip_paint_eyedropper": "Take a colour to match: press this, then click the ground, or a building, prop or tree to match its own colour (without the light on it). Alt+click with the Colour brush does the same.", "paint_took_object": "Colour taken from {name}: {hex}", "tip_paint_swatch": "Paint with this colour", "paint_map_colours": "The map's own colours", "tip_paint_map_colours": "The colours this map's ground is painted in most (grass, fields, sand, rock, roads), so new paint matches it.", "paint_recent": "Recent", "stamp_pick": "Pick the spot to copy from", "tip_stamp_pick": "Press this, then click the ground the texture should come from (Alt+click does the same). Your first stroke after it sets the distance: the copy follows your brush.", "stamp_pick_help": "Click the ground the texture should come from.", "stamp_from": "Copying from the spot you picked: the second ring shows where. Pick again for another spot.", "stamp_from_none": "Pick the spot to copy from first: press the button above, or Alt+click the ground.", "stamp_picked": "Spot picked: now paint where its ground should go.", "stamp_same": "That's the spot you copy from: paint somewhere else.", "paint_note": "Shown here on the map's picture; the build paints every level of the game's ground tiles (seen in the game).", "paint_clear": "Clear the ground under it", "tip_paint_clear": "Up close the game draws the map's grass, crops, stones and ground stickers over its picture, so paint shows only from afar. With this on, the build takes those off where the paint is at least half strength, so it shows at every height (seen in the game). Trees, buildings, cover and movement stay.", "paint_took": "Colour taken: {hex}", "paint_pick_help": "Click the ground to take its colour.", "paint_hex_bad": "A colour is # and six hex digits, like #8a7a4e.", "tex_from_game": "Game textures", "tip_tex_from_game": "The ground textures the game's own maps are made with (grass, fields, sand, snow, rock, roads...). They are read from your game: nothing of them goes in your mod.", "tex_from_map": "From a map", "tip_tex_from_map": "Take the ground of any of the game's maps: pick the map, then click the spot (a 320 m square of it becomes your texture).", "tex_from_own": "Your pictures", "tip_tex_from_own": "Paint with a picture of your own (a photo of grass, sand, rock...): it's kept in your mod.", "tex_from_spot": "This map", "tip_tex_from_spot": "Copy this map's own ground from another spot: pick the spot, then paint where it should go.", "tex_search": "Find a texture…", "tip_tex_search": "Type part of a texture's name (grass, sand, cobbles...) or a theatre (Italy, Ardennes...).", "tex_group_all": "All", "tip_tex_group_all": "Show every texture.", "tip_tex_group": "Show only these textures: {group}.", "tip_tex_item": "{name} ({where}): repeats every {m} m in the game. Click it, then paint.", "tip_tex_item_see": "{name} ({where}): repeats every {m} m in the game; see-through, it lays over what's there. Click it, then paint.", "tex_none_found": "No texture has that name.", "tex_loading": "Reading the game's ground textures… {progress}", "tex_cant_read": "That texture can't be read: {error}", "tex_picked_note": "Painting with: {name}. Drag on the ground.", "tex_none_picked": "Pick a texture first: click one in the list.", "tip_tex_own_item": "{name}: your own picture. Click it, then paint.", "tex_own_none": "No pictures yet: add one (a photo of grass, sand, rock...).", "tex_own_add": "Add a picture…", "tip_tex_own_add": "Pick a picture on your PC (PNG, JPG...). Its middle square is kept in your mod (files/ground) to paint with.", "tex_own_added": "Added {name}. Drag on the ground to paint with it.", "tex_map_choose": "Pick a map…", "tip_tex_map_list": "The map to take ground from (any of the game's maps).", "tex_map_first": "Pick a map to take its ground.", "tex_map_click": "Click the spot whose ground you want.", "tip_tex_map_pic": "Click where the ground you want is: a 320 m square of it becomes your texture.", "tex_map_taking": "Taking that ground…", "tex_map_taken": "Took ground from {map}: drag on the ground to paint with it.", "tex_from_map_name": "Ground of {map}", "tip_tex_now": "The texture you paint with.", "tex_size": "Size: repeats every {m} m", "tip_tex_size": "How big the texture is laid on the ground: it starts at the game's own size; right makes it bigger (up to 16 times), left smaller.", "tex_used": "Used lately", "tip_tex_used": "The textures you painted with lately: click one to paint with it again.", "tex_note": "Painted on every level of the ground's picture, as the build does. The game's own textures are read from your game when the mod is built (none of them goes in your mod). Not yet seen in the game.", "tex_from_palette": "Palette", "tip_tex_from_palette": "Ground materials measured on the game's own maps (wheat, ploughed earth, grass, sand, mud, rock…): each laid repeating, its repeats mirrored here and there so no grid shows. Read from your game when the mod is built.", "tex_palette_loading": "Making the palette's pictures from your game… {progress}", "tip_tex_palette": "{name}: repeats every {m} m, mirrored here and there so no grid shows. Click it, then paint.", "tip_tex_palette_rows": "{name}: a field's rows, repeating every {m} m. Turn sets the way they run. Click it, then paint.", "tex_turn": "Turn: {deg}°", "tex_turn_rows": "Turn (the rows): {deg}°", "tip_tex_turn": "Turns the texture on the ground: a field's rows run the way it's turned. 0 lays it as it is.", "pal_wheat": "Wheat", "pal_ploughed": "Ploughed earth", "pal_green_crop": "Green crop", "pal_grass": "Grass", "pal_dark_grass": "Dark grass", "pal_light_grass": "Light grass", "pal_earth": "Earth", "pal_dark_earth": "Dark earth", "pal_sand": "Sand", "pal_mud": "Mud", "pal_forest_floor": "Forest floor", "pal_rock": "Rock", "paint_mask": "Brush pattern", "tip_paint_mask": "How the brush lays its paint: plain (its soft or hard edge alone), or through a pattern, so a patch doesn't look stamped on. The build lays the same pattern.", "tip_paint_mask_one": "Paint with this pattern: {name}.", "mask_none": "Plain", "mask_noise": "Mottled", "mask_splatter": "Splatter", "mask_ragged": "Ragged edge", "mask_tufts": "Tufts", "mask_ridge": "Lines", "paint_dither": "Speckled edge", "tip_paint_dither": "Where the stroke fades, each pixel of the ground's finest picture takes it whole or not at all, more of them nearer its middle: a speckled edge, as real ground meets, instead of a blend. From afar it blends as before. Not yet seen in the game.", "paint_building": "Holding still: this dab is laid at {pct}%.", "brush_repaint": "Paint by shape", "tip_brush_repaint": "Click: inside it, the ground your other brushes moved is painted by its new shape with D-Day's own materials: rock where it's steep, mud under a new lake, sand round its shore with Sandy shore on, grass elsewhere. Your own paint lies over it.", "repaint_beach": "Sandy shore", "tip_repaint_beach": "For the Paint by shape strokes made from now on: sand round the water of the lakes you dug, its first 3 m above the surface, as D-Day's beaches. Off: grass down to the water, as D-Day's rivers and marshes; paint sand by hand (Texture, the palette's Sand) where you want a beach.", "repaint_working": "Paint by shape: working out what moved… {progress}", "repaint_done": "Paint by shape, as the build lays it: {said}.", "repaint_cant": "Paint by shape can't be shown: {error}", "tex_from_online": "Online (free)", "tip_tex_from_online": "Free ground pictures from the internet (Poly Haven, ambientCG, US aerial photos): click one to download just that picture into your mod.", "tex_online_polyhaven": "Poly Haven", "tip_tex_online_polyhaven": "Poly Haven's ground textures (CC0: free for any use): the aerial ones, photographed from above at the size a map is seen at, come first.", "tex_online_ambientcg": "ambientCG", "tip_tex_online_ambientcg": "ambientCG's materials (CC0: free for any use), found by the words you type: most are close-ups a metre or two across.", "tex_online_usgs": "US aerial photos", "tip_tex_online_usgs": "Real ground photographed from the air anywhere in the 48 US states (public domain: USGS National Map, NAIP imagery): pick a place, or type a latitude and longitude.", "tex_online_search": "Find (grass, sand, rock…)", "tip_tex_online_search": "Type part of a texture's name or what it shows, in English (grass, sand, rock, snow...).", "tip_tex_online_search_site": "Type what you're after, in English (grass, gravel, rock, snow...): ambientCG's site is searched once you stop typing.", "tex_online_find_place": "Find a place…", "tip_tex_online_find_place": "Type part of a place's name (fields, forest, dunes, Kansas...) to show only those.", "tex_online_listing": "Loading {source}'s list…", "tex_online_cant_list": "{source}'s list couldn't be loaded: {error}", "tex_online_none": "Nothing found: try another word.", "tip_tex_online_item": "{name}: {m} m across, by {author} ({licence}). Click to download just this picture into your mod and paint with it.", "tip_tex_online_item_nosize": "{name}: by {author} ({licence}); its real size isn't given, so it's laid 32 m a repeat (change it with Size). Click to download just this picture into your mod and paint with it.", "tex_online_getting": "Downloading {name}…", "tex_online_added": "Downloaded {name} from {source} into your mod: drag on the ground to paint with it.", "tex_online_cant": "That picture couldn't be downloaded: {error}", "tex_online_metres": "Photo size", "tip_tex_online_metres": "How much ground one photo covers: up to 640 m it's about 0.6 m a pixel, as sharp as the photos are; 1,280 m takes in more ground, half as sharp.", "tex_online_m": "{m} m", "tex_online_where": "Latitude, longitude (38.2, -98.4)", "tip_tex_online_where": "Any spot in the 48 US states: type or paste its latitude and longitude (from any online map), then press Enter.", "tex_online_take": "Photo of this spot", "tip_tex_online_take": "Download a photo of the ground at that latitude and longitude, the size picked, into your mod.", "tex_online_where_first": "Type a latitude and a longitude first, like 38.2, -98.4.", "tip_tex_place": "{place} ({lat}, {lon}): click to download a {m} m photo of it into your mod. Picked by eye: it may land a little off.", "tex_online_note_polyhaven": "CC0: free for any use, no credit needed (the Studio keeps the credit with the picture anyway). Only the picture you click is downloaded.", "tex_online_note_ambientcg": "CC0: free for any use, no credit needed (the Studio keeps the credit with the picture anyway). ambientCG sends a material as a zip of several pictures (about 10 MB): only its colour picture is kept.", "tex_online_note_usgs": "Public domain (USGS National Map, NAIP imagery). The photos are flown in summer, so snow shows only where it stays all year. Only the photo you ask for is downloaded.", "tip_tex_own_item_credit": "{name}: repeats every {m} m; from {source}, by {author} ({licence}). Click it, then paint.", "tip_tex_now_credit": "The texture you paint with: from {source}, by {author} ({licence}).", "tex_place_wheat_kansas": "Wheat fields (Kansas)", "tex_place_corn_iowa": "Cornfields (Iowa)", "tex_place_pivots_kansas": "Round irrigated fields (Kansas)", "tex_place_farms_pennsylvania": "Small farms (Pennsylvania)", "tex_place_wheat_hills_washington": "Rolling wheat hills (Washington)", "tex_place_cotton_mississippi": "Cotton fields (Mississippi)", "tex_place_rice_california": "Rice paddies (California)", "tex_place_orchards_california": "Orchards (California)", "tex_place_vineyards_california": "Vineyards (California)", "tex_place_prairie_kansas": "Tall grass prairie (Kansas)", "tex_place_forest_pennsylvania": "Leafy forest (Pennsylvania)", "tex_place_woods_wisconsin": "Woods and fields (Wisconsin)", "tex_place_pines_arizona": "Pine forest (Arizona)", "tex_place_oaks_california": "Oak grassland (California)", "tex_place_swamp_louisiana": "Cypress swamp (Louisiana)", "tex_place_desert_california": "Desert scrub (California)", "tex_place_dunes_california": "Sand dunes (California)", "tex_place_white_dunes_new_mexico": "White sand dunes (New Mexico)", "tex_place_red_rock_arizona": "Red rock (Arizona)", "tex_place_badlands_south_dakota": "Badlands (South Dakota)", "tex_place_salt_flats_utah": "Salt flats (Utah)", "tex_place_lava_idaho": "Lava fields (Idaho)", "tex_place_marsh_florida": "Marsh (Florida)", "tex_place_sandbars_nebraska": "River sand bars (Nebraska)", "tex_place_beach_north_carolina": "Beach (North Carolina)", "tex_place_rocky_coast_maine": "Rocky coast (Maine)", "tex_place_glacier_washington": "Glacier snow (Washington)", "tex_place_tundra_colorado": "Mountain tundra (Colorado)", "tex_place_mine_utah": "Open pit mine (Utah)", "tex_place_town_kansas": "Small town streets (Kansas)", "tex_place_old_town_georgia": "Old town squares (Georgia)", "tex_place_rail_yard_nebraska": "Rail yard (Nebraska)", "gtex_group_grass": "Grass", "gtex_group_fields": "Fields", "gtex_group_earth": "Earth", "gtex_group_sand": "Sand", "gtex_group_rock": "Rock", "gtex_group_snow": "Snow and frost", "gtex_group_water": "Wet ground", "gtex_group_roads": "Roads and tracks", "gtex_group_town": "Town ground", "gtex_group_damage": "Battle damage", "gtex_group_marks": "Markings and emblems", "gtex_group_other": "Other", "gtex_theatre_france": "France", "gtex_theatre_allemagne": "Germany", "gtex_theatre_hollande": "Holland", "gtex_theatre_italie": "Italy", "gtex_theatre_ardennes": "Ardennes (winter)", "gtex_theatre_afrique": "North Africa", "gtex_theatre_communs": "All theatres", "gtex_light_green": "light green", "gtex_bright_green": "bright green", "gtex_pale_green": "pale green", "gtex_green": "green", "gtex_grassy": "grassy", "gtex_grass": "grass", "gtex_daisies": "daisies", "gtex_red": "red", "gtex_dry": "dry", "gtex_dark": "dark", "gtex_light": "light", "gtex_ploughed": "ploughed", "gtex_straw": "straw", "gtex_crops": "crops", "gtex_grain": "grain", "gtex_fallow": "fallow", "gtex_earth": "earth", "gtex_ochre": "ochre", "gtex_details": "detailed", "gtex_pebbles": "pebbles", "gtex_dark_tracks": "dark tracks", "gtex_wet": "wet", "gtex_sand": "sand", "gtex_dunes": "dunes", "gtex_ripples": "ripples", "gtex_frost": "frost", "gtex_snow": "snow", "gtex_marsh": "marsh", "gtex_river": "riverside", "gtex_seashore": "seashore", "gtex_turquoise": "turquoise", "gtex_rock": "rock", "gtex_stony": "stony", "gtex_rubble": "rubble", "gtex_crater": "crater", "gtex_burnt": "burnt", "gtex_tank_tracks": "tank tracks", "gtex_tyre_tracks": "tyre tracks", "gtex_stain": "stains", "gtex_forest_floor": "forest floor", "gtex_scrub": "scrub", "gtex_plants": "plants", "gtex_palms": "palm trees", "gtex_asphalt": "asphalt", "gtex_tarmac": "tarmac", "gtex_alley": "alley", "gtex_worn": "worn", "gtex_road": "road", "gtex_track": "track", "gtex_edges": "edges", "gtex_crossing": "crossing", "gtex_bend": "bend", "gtex_junction": "junction", "gtex_half": "half", "gtex_wide": "wide", "gtex_cobbles": "cobbles", "gtex_yard": "yard", "gtex_pavement": "pavement", "gtex_brick": "brick", "gtex_slabs": "slabs", "gtex_rails": "rails", "gtex_tree_ring": "around a tree", "gtex_house_edge": "around a house", "gtex_mud": "mud", "gtex_wooden_floor": "wooden floor", "gtex_planks": "planks", "gtex_trench": "trench", "gtex_layout": "town layout", "gtex_town": "town", "gtex_village": "village", "gtex_emblem": "emblem", "gtex_white_markings": "white markings", "gtex_yellow_markings": "yellow markings", "gtex_line": "line", "gtex_ground": "ground", "gtex_tracks": "tracks", "paint_decals": "Game detail up close", "tip_paint_decals": "Up close the game shows its ground's detail with decals. With this on, the build lays the game's own decals of this texture over the ground you paint, as many as the map has room for. Not yet seen in the game."});
  // the map screen's two sides (words.toml mode_*, tip_mode_*, tip_scen_locked, locked_*)
  Object.assign(words.us, { mode_map: "Map", mode_label: "Tools for the map or for the scenario", tip_mode_map: "Map tools: ground, water, cover, roads, buildings, trees, paint and sectors. The scenario's units, HQs and names show faded and can't be picked, so nothing of theirs moves by accident.", tip_mode_scenario: "Scenario tools: move things, add units and buildings, starting points, names and zones. The map's buildings, trees and roads show faded and can't be picked, so nothing of theirs moves by accident.", tip_scen_locked: "Pick a scenario first, in the map panel: each scenario has its own units, HQs and names.", locked_scenario: "switch to Scenario to change it", locked_map: "switch to Map to change it" });
  Object.assign(words.fr, { mode_map: "Carte", mode_label: "Outils pour la carte ou pour le scénario", tip_mode_map: "Outils de la carte : terrain, eau, couvert, routes, bâtiments, arbres, peinture et secteurs. Les unités, QG et noms du scénario sont estompés et ne peuvent pas être pris, pour que rien ne bouge par erreur.", tip_mode_scenario: "Outils du scénario : déplacer, ajouter unités et bâtiments, points de départ, noms et zones. Les bâtiments, arbres et routes de la carte sont estompés et ne peuvent pas être pris, pour que rien ne bouge par erreur.", tip_scen_locked: "Choisissez d'abord un scénario, dans le panneau de la carte : chaque scénario a ses propres unités, QG et noms.", locked_scenario: "passez en Scénario pour le changer", locked_map: "passez en Carte pour le changer" });
  // what's selected on the map (words.toml scen_sel_*)
  Object.assign(words.us, { scen_sel_count: "{n} selected", scen_sel_ground: "vehicles", scen_sel_infantry: "infantry", scen_sel_air: "aircraft", scen_sel_buildings: "buildings", scen_sel_other: "others", scen_sel_only: "Click to keep only these selected.", scen_sel_hint: "Drag a box on the ground to select several · Shift+click adds or takes one off · Esc clears", scen_sel_clear: "Clear" });
  Object.assign(words.fr, { scen_sel_count: "{n} sélectionnés", scen_sel_ground: "véhicules", scen_sel_infantry: "infanterie", scen_sel_air: "avions", scen_sel_buildings: "bâtiments", scen_sel_other: "autres", scen_sel_only: "Cliquez pour ne garder que ceux-ci.", scen_sel_hint: "Tracez un cadre sur le sol pour en sélectionner plusieurs · Maj+clic en ajoute ou en retire un · Échap efface", scen_sel_clear: "Effacer" });
  // a test the build stopped (words.toml test_problems_title, test_fix_*, tip_copy_log, tip_status_close)
  Object.assign(words.us, {"test_problems_title": "The test stopped on {n} mistake(s) in your mods. Nothing in the game was changed. Fix each one here, then press Test in game again.", "test_in_mod": "(in {mod})", "test_no_fix": "No one-click fix: change it in the mod as the message says.", "test_fix_neutral": "Make it neutral", "tip_test_fix_neutral": "BATTLES maps place only neutral spawns: this keeps the unit and makes it neutral (camp -1).", "test_fix_remove_spawn": "Remove this spawn", "tip_test_fix_remove_spawn": "Takes this unit out of the map's scenario.toml in your mod.", "test_fix_remove_road": "Remove road {n}", "tip_test_fix_remove_road": "Takes this new road out of the map's roads.toml in your mod. Draw it again with both ends on a road if you want it back.", "test_fixed": "Fixed ({done}). Press Test in game again.", "tip_copy_log": "Copy the whole log and the message, to paste into a bug report or on Discord.", "test_copy_failed": "The log couldn't be copied: select it with the mouse and press Ctrl+C.", "tip_status_close": "Hide this message."});
  Object.assign(words.fr, {"test_problems_title": "Le test s'est arrêté sur {n} erreur(s) dans vos mods. Rien n'a été changé dans le jeu. Corrigez-les ici, puis relancez Tester en jeu.", "test_in_mod": "(dans {mod})", "test_no_fix": "Pas de correction en un clic : modifiez le mod comme le message l'indique.", "test_fix_neutral": "La rendre neutre", "tip_test_fix_neutral": "Les cartes BATAILLES ne placent que les apparitions neutres : l'unité reste, mais neutre (camp -1).", "test_fix_remove_spawn": "Retirer cette apparition", "tip_test_fix_remove_spawn": "Retire cette unité du scenario.toml de la carte dans votre mod.", "test_fix_remove_road": "Retirer la route {n}", "tip_test_fix_remove_road": "Retire cette nouvelle route du roads.toml de la carte dans votre mod. Redessinez-la avec les deux bouts sur une route pour la remettre.", "test_fixed": "Corrigé ({done}). Relancez Tester en jeu.", "tip_copy_log": "Copie tout le journal et le message, à coller dans un rapport de bug ou sur Discord.", "test_copy_failed": "Le journal n'a pas pu être copié : sélectionnez-le à la souris et appuyez sur Ctrl+C.", "tip_status_close": "Masquer ce message."});
  Object.assign(words.sc, {"test_problems_title": "测试因模组中的 {n} 个错误而停止。游戏没有任何改动。请在这里逐个修正，然后再次点击“在游戏中测试”。", "test_in_mod": "（在 {mod} 中）", "test_no_fix": "没有一键修正：请按消息所说修改模组。", "test_fix_neutral": "设为中立", "tip_test_fix_neutral": "“战斗”地图只放置中立的出生单位：保留该单位并设为中立（阵营 -1）。", "test_fix_remove_spawn": "删除这个出生单位", "tip_test_fix_remove_spawn": "从你的模组中该地图的 scenario.toml 里删除这个单位。", "test_fix_remove_road": "删除道路 {n}", "tip_test_fix_remove_road": "从你的模组中该地图的 roads.toml 里删除这条新道路。如需恢复，请重新绘制并让两端都连到道路上。", "test_fixed": "已修正（{done}）。请再次点击“在游戏中测试”。", "tip_copy_log": "复制完整日志和消息，可粘贴到错误报告或 Discord。", "test_copy_failed": "无法复制日志：请用鼠标选中后按 Ctrl+C。", "tip_status_close": "隐藏这条消息。"});
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
  // the Sectors tool (words.toml sectors_*, tip_sectors_*, scen_sectors_tool)
  Object.assign(words.us, {"scen_names_tool": "Names", "scen_sectors_tool": "Sectors", "tip_scen_sectors_locked": "Pick a scenario first: each scenario has its own sectors.", "sectors_n": "Sector {n}", "tip_sectors_pick": "Paint more ground into this sector.", "sectors_new": "New sector", "tip_sectors_new": "Paint a sector the scenario doesn't have yet. A new sector was seen in the game: on D-Day, a ruse card lit it up on its own.", "tip_sectors_new_full": "No more sectors can be added: this scenario has the most it can hold here.", "sectors_none": "No sector", "tip_sectors_none": "The eraser: the ground you paint goes out of every sector.", "tip_sectors_none_shapes": "Drag a box on the ground: the ground in it belongs to no sector. Its edges get corner dots like any border, so you can reshape it.", "sectors_round": "Round", "sectors_square": "Square", "tip_sectors_shape": "The brush's shape: a round spot or a square one.", "sectors_size": "Size {pct} %", "tip_sectors_size": "How big the brush is, as a share of the map's width.", "sectors_undo": "Undo", "tip_sectors_undo": "Take back the last thing you painted on this scenario's sectors.", "tip_sectors_undo_none": "Nothing is painted on this scenario's sectors yet.", "sectors_clear": "Take out all painting", "tip_sectors_clear": "Take back everything painted on this scenario's sectors at once.", "sectors_start_none": "Start from no sectors", "tip_sectors_start_none": "Clear the map's own sectors from this scenario, so only the sectors you paint are there. Your painting stays.", "sectors_start_map": "Start from the map's sectors", "tip_sectors_start_map": "Bring the map's own sectors back under your painting.", "sectors_outlines": "Show outlines", "tip_sectors_outlines": "Draw each sector's border the way the game will get it.", "sectors_busy": "Working out the sectors…", "sectors_help": "Pick a sector, then drag on the ground to paint it. “No sector” takes ground out of every sector.", "sectors_empty": "This scenario has no sector yet: paint at least one sector. A map with no sectors has never been tried in the game, so Check this map and Test in game stop until there is one.", "sectors_pieces": "Sector {n} is in {pieces} pieces: a sector must be one piece of ground. Join the pieces, or erase all but one.", "sectors_hole": "Sector {n} has a hole in it: a sector can't have a hole. Paint the hole into sector {n}, or open it to the sector's edge.", "sectors_untried": "Sectors made here show in the game (tried on a blank map and on D-Day). Ground in no sector shows as a gap in the sectors, and a ruse card held over it lights up nothing.", "sectors_mode_shapes": "Shapes", "tip_sectors_mode_shapes": "Change sectors by their corners: drag a corner dot, and every sector that shares it moves with it.", "sectors_mode_paint": "Paint", "tip_sectors_mode_paint": "Touch up with a brush: paint ground into the picked sector, or take it out of every sector with No sector.", "sectors_shapes_help": "Drag a corner dot to move a border: the sectors that share it move together. Double-click a border to add a dot; right-click a dot to remove it. New sector: drag a box on the ground. No sector: drag a box where no sector should be.", "sectors_delete": "Delete sector", "tip_sectors_delete": "Take out the picked sector: its ground goes to the sectors around it.", "tip_sectors_delete_n": "Take out sector {n}: its ground goes to the sectors around it (Undo brings it back).", "tip_sectors_delete_none": "Pick a sector first (its button above).", "sectors_tidy_pieces": "{bits} small bit(s) of Sector {n} joined Sector {to}: a sector is one piece of ground.", "sectors_tidy_pieces_none": "{bits} small bit(s) of Sector {n} became no sector: they touched no other sector.", "sectors_tidy_line": "A thin line joins Sector {n} to the edge of Sector {around}: a sector can't go all the way round another.", "sectors_tidy_gap": "A thin gap of no sector runs from inside Sector {around} to its edge: a sector can't go all the way round anything.", "sectors_tidy_untried": "These tidy-ups (bits joining a neighbour, thin lines) haven't been tried in the game yet."});
  Object.assign(words.fr, {"scen_names_tool": "Noms", "scen_sectors_tool": "Secteurs", "tip_scen_sectors_locked": "Choisissez d'abord un scénario : chaque scénario a ses propres secteurs.", "sectors_n": "Secteur {n}", "tip_sectors_pick": "Peindre plus de terrain dans ce secteur.", "sectors_new": "Nouveau secteur", "tip_sectors_new": "Peindre un secteur que le scénario n'a pas encore. Un nouveau secteur a été vu en jeu : sur D-Day, une carte de ruse l'a éclairé seul.", "tip_sectors_new_full": "Plus aucun secteur ne peut être ajouté : ce scénario en a le maximum possible ici.", "sectors_none": "Aucun secteur", "tip_sectors_none": "La gomme : le terrain peint sort de tous les secteurs.", "tip_sectors_none_shapes": "Tracez un rectangle sur le terrain : le terrain dedans n'appartient à aucun secteur. Ses bords reçoivent des points de coin comme toute frontière, pour le remodeler.", "sectors_round": "Rond", "sectors_square": "Carré", "tip_sectors_shape": "La forme du pinceau : une tache ronde ou carrée.", "sectors_size": "Taille {pct} %", "tip_sectors_size": "La taille du pinceau, en part de la largeur de la carte.", "sectors_undo": "Annuler", "tip_sectors_undo": "Retirer la dernière chose peinte sur les secteurs de ce scénario.", "tip_sectors_undo_none": "Rien n'est encore peint sur les secteurs de ce scénario.", "sectors_clear": "Retirer toute la peinture", "tip_sectors_clear": "Retirer d'un coup tout ce qui est peint sur les secteurs de ce scénario.", "sectors_start_none": "Partir de zéro secteur", "tip_sectors_start_none": "Enlever les secteurs propres à la carte de ce scénario : seuls ceux que vous peignez restent. Votre peinture reste.", "sectors_start_map": "Partir des secteurs de la carte", "tip_sectors_start_map": "Remettre les secteurs propres à la carte sous votre peinture.", "sectors_outlines": "Montrer les contours", "tip_sectors_outlines": "Dessiner la bordure de chaque secteur telle que le jeu la recevra.", "sectors_busy": "Calcul des secteurs…", "sectors_help": "Choisissez un secteur, puis faites glisser sur le terrain pour le peindre. « Aucun secteur » retire le terrain de tous les secteurs.", "sectors_empty": "Ce scénario n'a encore aucun secteur : peignez-en au moins un. Une carte sans secteur n'a jamais été essayée en jeu, donc Vérifier cette carte et Tester en jeu s'arrêtent tant qu'il n'y en a pas.", "sectors_pieces": "Le secteur {n} est en {pieces} morceaux : un secteur doit être d'un seul tenant. Reliez les morceaux, ou effacez-les sauf un.", "sectors_hole": "Le secteur {n} a un trou : un secteur ne peut pas avoir de trou. Peignez le trou dans le secteur {n}, ou ouvrez-le jusqu'au bord du secteur.", "sectors_untried": "Les secteurs faits ici s'affichent en jeu (essayé sur une carte vierge et sur D-Day). Un terrain sans secteur apparaît comme un trou entre les secteurs, et une carte de ruse tenue dessus n'éclaire rien.", "sectors_mode_shapes": "Formes", "tip_sectors_mode_shapes": "Modifier les secteurs par leurs coins : faites glisser un point de coin, et chaque secteur qui le partage suit.", "sectors_mode_paint": "Peindre", "tip_sectors_mode_paint": "Retoucher au pinceau : peignez du terrain dans le secteur choisi, ou retirez-le de tout secteur avec Aucun secteur.", "sectors_shapes_help": "Faites glisser un point de coin pour déplacer une frontière : les secteurs qui la partagent bougent ensemble. Double-cliquez sur une frontière pour ajouter un point ; clic droit sur un point pour l'enlever. Nouveau secteur : tracez un rectangle sur le terrain. Aucun secteur : tracez un rectangle là où il ne doit y avoir aucun secteur.", "sectors_delete": "Supprimer le secteur", "tip_sectors_delete": "Retirer le secteur choisi : son terrain va aux secteurs autour.", "tip_sectors_delete_n": "Retirer le secteur {n} : son terrain va aux secteurs autour (Annuler le remet).", "tip_sectors_delete_none": "Choisissez d'abord un secteur (son bouton ci-dessus).", "sectors_tidy_pieces": "{bits} petit(s) morceau(x) du secteur {n} ont rejoint le secteur {to} : un secteur est d'un seul tenant.", "sectors_tidy_pieces_none": "{bits} petit(s) morceau(x) du secteur {n} ne sont plus dans aucun secteur : ils ne touchaient aucun autre secteur.", "sectors_tidy_line": "Une fine ligne relie le secteur {n} au bord du secteur {around} : un secteur ne peut pas entourer complètement un autre.", "sectors_tidy_gap": "Une fine bande sans secteur va de l'intérieur du secteur {around} jusqu'à son bord : un secteur ne peut rien entourer complètement.", "sectors_tidy_untried": "Ces retouches (morceaux rattachés à un voisin, fines lignes) n'ont pas encore été essayées en jeu."});
  Object.assign(words.sc, {"scen_names_tool": "地名", "scen_sectors_tool": "扇区", "tip_scen_sectors_locked": "请先选择一个场景：每个场景都有自己的扇区。", "sectors_n": "扇区 {n}", "tip_sectors_pick": "把更多地面绘制进这个扇区。", "sectors_new": "新扇区", "tip_sectors_new": "绘制场景中还没有的扇区。新扇区已在游戏中试过：在D-Day上，计谋卡只点亮了它。", "tip_sectors_new_full": "无法再添加扇区：此场景在这里已达到上限。", "sectors_none": "无扇区", "tip_sectors_none": "橡皮擦：绘制的地面不再属于任何扇区。", "tip_sectors_none_shapes": "在地面上拖出一个方框：框内的地面不属于任何扇区。它的边和其他边界一样有角点，可以改变形状。", "sectors_round": "圆形", "sectors_square": "方形", "tip_sectors_shape": "画笔形状：圆形或方形。", "sectors_size": "大小 {pct} %", "tip_sectors_size": "画笔大小，占地图宽度的比例。", "sectors_undo": "撤销", "tip_sectors_undo": "撤回在此场景扇区上最后绘制的内容。", "tip_sectors_undo_none": "此场景的扇区上还没有绘制任何内容。", "sectors_clear": "清除全部绘制", "tip_sectors_clear": "一次撤回此场景扇区上绘制的全部内容。", "sectors_start_none": "从无扇区开始", "tip_sectors_start_none": "从此场景清除地图自带的扇区，只保留你绘制的扇区。你的绘制会保留。", "sectors_start_map": "从地图的扇区开始", "tip_sectors_start_map": "把地图自带的扇区恢复到你的绘制之下。", "sectors_outlines": "显示轮廓", "tip_sectors_outlines": "按游戏将得到的样子绘制每个扇区的边界。", "sectors_busy": "正在计算扇区…", "sectors_help": "选择一个扇区，然后在地面上拖动来绘制。“无扇区”会把地面移出所有扇区。", "sectors_empty": "此场景还没有扇区：请至少绘制一个扇区。没有扇区的地图从未在游戏中试过，所以在有扇区之前，检查地图和游戏内测试都会停止。", "sectors_pieces": "扇区 {n} 分成了 {pieces} 块：一个扇区必须是一整块地面。请把它们连起来，或只保留一块。", "sectors_hole": "扇区 {n} 中间有洞：扇区不能有洞。请用扇区 {n} 填满这个洞，或把它打通到扇区边缘。", "sectors_untried": "在这里做的扇区会在游戏中显示（在空白地图和D-Day上试过）。无扇区的地面显示为扇区之间的空缺，把计谋卡放在上面不会点亮任何东西。", "sectors_mode_shapes": "形状", "tip_sectors_mode_shapes": "通过角点修改扇区：拖动一个角点，共用它的每个扇区都会跟着移动。", "sectors_mode_paint": "绘制", "tip_sectors_mode_paint": "用画笔修整：把地面画进所选扇区，或用“无扇区”把它移出所有扇区。", "sectors_shapes_help": "拖动角点来移动边界：共用这条边界的扇区会一起移动。双击边界可添加一个点；右键点击一个点可删除它。新扇区：在地面上拖出一个方框。无扇区：在不需要扇区的地方拖出一个方框。", "sectors_delete": "删除扇区", "tip_sectors_delete": "移除所选扇区：它的地面归周围的扇区。", "tip_sectors_delete_n": "移除扇区 {n}：它的地面归周围的扇区（撤销可恢复）。", "tip_sectors_delete_none": "请先选择一个扇区（上面的按钮）。", "sectors_tidy_pieces": "扇区 {n} 的 {bits} 小块并入了扇区 {to}：一个扇区是一整块地面。", "sectors_tidy_pieces_none": "扇区 {n} 的 {bits} 小块变成了无扇区：它们没有接触其他扇区。", "sectors_tidy_line": "一条细线把扇区 {n} 连到扇区 {around} 的边缘：一个扇区不能完全包围另一个扇区。", "sectors_tidy_gap": "一条无扇区的细缝从扇区 {around} 内部通到它的边缘：一个扇区不能完全包围任何东西。", "sectors_tidy_untried": "这些整理（小块并入邻居、细线）尚未在游戏中试过。"});
  // the scenario's depots and HQs panel (words.toml scen_depots_*, scen_hqs_title, tip_scen_hqs)
  Object.assign(words.us, {"scen_depots_apply": "Apply", "scen_depots_back": "Back to the game's", "scen_depots_each": "trucks each", "scen_depots_label": "Every depot here ({n}):", "scen_depots_times": "times their trucks", "scen_hqs_title": "Each player's HQ", "tip_scen_depots": "Change every supply depot of this scenario at once, the map's and yours: multiply each one's trucks, or give them all the same number. More trucks, more money in every depot. Saved in your map changes at once.", "tip_scen_depots_back": "Put every depot of this scenario back to the trucks the game gives it (the ones you added: 25).", "tip_scen_hqs": "A blank map starts with no HQs: place one for every player. Test in game waits until they're all placed. Fewer players need fewer HQs (Players, in the panel)."});
  Object.assign(words.fr, {"scen_depots_apply": "Appliquer", "scen_depots_back": "Revenir à ceux du jeu", "scen_depots_each": "camions chacun", "scen_depots_label": "Tous les dépôts ici ({n}) :", "scen_depots_times": "fois leurs camions", "scen_hqs_title": "Le QG de chaque joueur", "tip_scen_depots": "Change tous les dépôts de ravitaillement de ce scénario d'un coup, ceux de la carte et les vôtres : multipliez les camions de chacun, ou donnez-leur à tous le même nombre. Plus de camions, plus d'argent dans chaque dépôt. Enregistré tout de suite dans vos changements de carte.", "tip_scen_depots_back": "Remet chaque dépôt de ce scénario aux camions que le jeu lui donne (ceux que vous avez ajoutés : 25).", "tip_scen_hqs": "Une carte vierge commence sans QG : placez-en un pour chaque joueur. Tester en jeu attend qu'ils soient tous placés. Moins de joueurs demandent moins de QG (Joueurs, dans le panneau)."});
  Object.assign(words.sc, {"scen_depots_apply": "应用", "scen_depots_back": "恢复为游戏的数值", "scen_depots_each": "辆（每个）", "scen_depots_label": "这里的所有补给站（{n}）：", "scen_depots_times": "倍的卡车", "scen_hqs_title": "每位玩家的指挥部", "tip_scen_depots": "一次更改此场景的所有补给站（地图自带的和你添加的）：把每个站的卡车乘以一个倍数，或全部设为同一数量。卡车越多，每个站里的钱越多。立即保存到你的地图更改中。", "tip_scen_depots_back": "把此场景的每个补给站恢复为游戏给的卡车数量（你添加的：25）。", "tip_scen_hqs": "空白地图开始时没有指挥部：为每位玩家放置一个。全部放好之前，“在游戏中测试”会等待。玩家越少，需要的指挥部越少（面板中的“玩家”）。"});
  // Map size and Make sectors (words.toml map_size_btn, size_*, tip_size_*, sectors_auto*, tip_sectors_auto*)
  Object.assign(words.us, {"size_why_shipped": "One of the game's own maps keeps its size. Make a new map from scratch to choose its size.", "size_why_copy": "This map is a copy: it keeps the copied map's ground, and its size with it. A new map started from scratch (Blank Terrain or Blank Ocean) can change size."});
  Object.assign(words.fr, {"size_why_shipped": "Une carte du jeu garde sa taille. Créez une nouvelle carte de zéro pour choisir sa taille.", "size_why_copy": "Cette carte est une copie : elle garde le terrain de la carte copiée, et sa taille avec. Une nouvelle carte partie de zéro (Terrain vierge ou Océan vierge) peut changer de taille."});
  Object.assign(words.sc, {"size_why_shipped": "游戏自带的地图保持原有大小。要选择大小，请从零开始制作新地图。", "size_why_copy": "这张地图是副本：它保留所复制地图的地面，大小也随之保留。从零开始的新地图（空白地形或空白海洋）可以改变大小。"});
  Object.assign(words.us, {"map_size_btn": "Map size", "tip_map_size_btn": "Make this new map bigger or smaller, a strip at a time on any side.", "size_title": "Map size", "size_lead": "Your map is a grid of squares, each {km} km across. Press + on a side to add a strip of ground {strip} km wide along it, or − to take one off. Nothing changes until you press Make it this size.", "size_how": "A strip added on the left or at the top moves everything you placed with it, so it all stays on the same ground. Whatever stood on a strip you take off ends up off the map: move it back on. Big maps take longer to build and to load. A map bigger than the one it copies gets no clouds and no room around the table, as both look wrong on a big map.", "tip_size_add": "Add a strip {km} km wide on this side.", "tip_size_cut": "Take a strip {km} km wide off this side.", "tip_size_most": "A side can be at most {most} squares long.", "tip_size_least": "A side can't be shorter than {tile} squares.", "size_all_add": "+ Every side", "tip_size_all_add": "Add a strip on all four sides at once: the map grows the same all round.", "size_all_cut": "− Every side", "tip_size_all_cut": "Take a strip off all four sides at once.", "size_back": "As it is now", "tip_size_back": "Forget the strips added or taken off here.", "size_reading": "Reading the map's size…", "size_now": "{a} × {b} squares ({x} × {y} km)", "size_change": "{now} → {then}", "size_apply": "Make it this size", "tip_size_apply": "Save the new size in your mod. The map is then shown again at its new size.", "size_making": "Making the map {a} × {b} squares…", "size_made": "Done: the map is {a} × {b} squares now. Test your mod to try it in the game.", "sectors_auto": "Sectors about", "tip_sectors_auto": "How wide each sector is, roughly. The game's own maps have sectors 1 to 3 km across; a scenario can have at most 255.", "sectors_auto_make": "Make sectors", "tip_sectors_auto_make": "Cut the whole map into sectors about this wide, with wandering borders. What you painted before stays underneath: Undo brings it back. Then drag corners or paint to reshape them.", "sectors_auto_again": "Another layout", "tip_sectors_auto_again": "The same size of sectors, cut another way.", "tip_sectors_auto_again_none": "Make sectors first.", "sectors_auto_made": "Made {n} sectors about {km} km across (layout {seed})."});
  Object.assign(words.fr, {"map_size_btn": "Taille de la carte", "tip_map_size_btn": "Agrandir ou réduire cette nouvelle carte, une bande à la fois, de n'importe quel côté.", "size_title": "Taille de la carte", "size_lead": "Votre carte est une grille de carrés de {km} km de côté. Appuyez sur + d'un côté pour y ajouter une bande de terrain de {strip} km de large, ou sur − pour en retirer une. Rien ne change tant que vous n'appuyez pas sur Donner cette taille.", "size_how": "Une bande ajoutée à gauche ou en haut déplace avec elle tout ce que vous avez placé, qui reste ainsi sur le même terrain. Ce qui se trouvait sur une bande retirée se retrouve hors de la carte : remettez-le dessus. Les grandes cartes sont plus longues à construire et à charger. Une carte plus grande que celle qu'elle copie n'a ni nuages ni salle autour de la table, car les deux rendent mal sur une grande carte.", "tip_size_add": "Ajouter une bande de {km} km de large de ce côté.", "tip_size_cut": "Retirer une bande de {km} km de large de ce côté.", "tip_size_most": "Un côté peut faire au plus {most} carrés.", "tip_size_least": "Un côté ne peut pas faire moins de {tile} carrés.", "size_all_add": "+ Tous les côtés", "tip_size_all_add": "Ajouter une bande sur les quatre côtés à la fois : la carte grandit pareil tout autour.", "size_all_cut": "− Tous les côtés", "tip_size_all_cut": "Retirer une bande des quatre côtés à la fois.", "size_back": "Comme maintenant", "tip_size_back": "Oublier les bandes ajoutées ou retirées ici.", "size_reading": "Lecture de la taille de la carte…", "size_now": "{a} × {b} carrés ({x} × {y} km)", "size_change": "{now} → {then}", "size_apply": "Donner cette taille", "tip_size_apply": "Enregistrer la nouvelle taille dans votre mod. La carte s'affiche ensuite à sa nouvelle taille.", "size_making": "Passage de la carte à {a} × {b} carrés…", "size_made": "C'est fait : la carte fait maintenant {a} × {b} carrés. Testez votre mod pour l'essayer dans le jeu.", "sectors_auto": "Secteurs d'environ", "tip_sectors_auto": "La largeur approximative de chaque secteur. Les cartes du jeu ont des secteurs de 1 à 3 km ; un scénario peut en avoir au plus 255.", "sectors_auto_make": "Créer les secteurs", "tip_sectors_auto_make": "Découper toute la carte en secteurs de cette largeur environ, aux frontières sinueuses. Ce que vous aviez peint reste dessous : Annuler le fait revenir. Ensuite, déplacez les coins ou peignez pour les remodeler.", "sectors_auto_again": "Autre découpage", "tip_sectors_auto_again": "Des secteurs de même taille, découpés autrement.", "tip_sectors_auto_again_none": "Créez d'abord les secteurs.", "sectors_auto_made": "{n} secteurs créés, d'environ {km} km (découpage {seed})."});
  Object.assign(words.sc, {"map_size_btn": "地图大小", "tip_map_size_btn": "将这张新地图变大或变小，每次在任意一边增减一条。", "size_title": "地图大小", "size_lead": "地图由边长 {km} 公里的方格组成。按某一边的 + 在该边增加一条 {strip} 公里宽的地面，按 − 去掉一条。按下“应用此大小”之前不会有任何改变。", "size_how": "在左边或上边增加一条时，你放置的所有东西都会跟着移动，因此仍在同一块地面上。被去掉的那条上的东西会落到地图外：请把它移回来。大地图的构建和加载需要更长时间。比所复制地图更大的地图没有云，也没有桌子周围的房间，因为两者在大地图上看起来都不对。", "tip_size_add": "在这一边增加一条 {km} 公里宽的地面。", "tip_size_cut": "从这一边去掉一条 {km} 公里宽的地面。", "tip_size_most": "每边最多 {most} 格。", "tip_size_least": "每边不能少于 {tile} 格。", "size_all_add": "+ 所有边", "tip_size_all_add": "同时在四边各增加一条：地图向四周均匀扩大。", "size_all_cut": "− 所有边", "tip_size_all_cut": "同时从四边各去掉一条。", "size_back": "保持现状", "tip_size_back": "撤销在这里增减的条。", "size_reading": "正在读取地图大小…", "size_now": "{a} × {b} 格（{x} × {y} 公里）", "size_change": "{now} → {then}", "size_apply": "应用此大小", "tip_size_apply": "将新大小保存到你的模组中。之后地图会以新大小重新显示。", "size_making": "正在将地图改为 {a} × {b} 格…", "size_made": "完成：地图现在是 {a} × {b} 格。测试你的模组，在游戏中试试。", "sectors_auto": "扇区宽约", "tip_sectors_auto": "每个扇区的大致宽度。游戏自带地图的扇区宽 1 到 3 公里；一个场景最多 255 个。", "sectors_auto_make": "生成扇区", "tip_sectors_auto_make": "把整张地图切成大约这个宽度、边界曲折的扇区。之前画的内容保留在下面：撤销即可恢复。之后拖动角点或绘制来调整形状。", "sectors_auto_again": "换一种布局", "tip_sectors_auto_again": "同样大小的扇区，换一种切法。", "tip_sectors_auto_again_none": "请先生成扇区。", "sectors_auto_made": "已生成 {n} 个约 {km} 公里宽的扇区（布局 {seed}）。"});
  // number rows (words.toml step_less, step_more, tip_step_*)
  Object.assign(words.us, {"step_less": "Less", "step_more": "More", "tip_step_less": "One step down. Hold it to keep going.", "tip_step_more": "One step up. Hold it to keep going."});
  Object.assign(words.fr, {"step_less": "Moins", "step_more": "Plus", "tip_step_less": "Un cran de moins. Maintenez pour continuer.", "tip_step_more": "Un cran de plus. Maintenez pour continuer."});
  Object.assign(words.sc, {"step_less": "减少", "step_more": "增加", "tip_step_less": "减小一档。按住可连续减小。", "tip_step_more": "增大一档。按住可连续增大。"});
  // search with tags (words.toml tip_search_tags, search_tags, search_recent, tip_search_tag, tip_search_recent, tag_new)
  Object.assign(words.us, {"tip_search_tags": "Every word you type must match. #tags narrow it: #us, #germany, #air, #armor, #new (your mod's new units). Type # to see them all.", "search_tags": "Tags:", "search_recent": "Recent:", "tip_search_tag": "Add #{tag} to the search: {label}.", "tip_search_recent": "Search for this again.", "tag_new": "Your mod's new units"});
  Object.assign(words.fr, {"tip_search_tags": "Chaque mot tapé doit correspondre. Les #tags affinent : #us, #germany, #air, #armor, #new (les nouvelles unités de votre mod). Tapez # pour tous les voir.", "search_tags": "Tags :", "search_recent": "Récentes :", "tip_search_tag": "Ajouter #{tag} à la recherche : {label}.", "tip_search_recent": "Relancer cette recherche.", "tag_new": "Les nouvelles unités de votre mod"});
  Object.assign(words.sc, {"tip_search_tags": "输入的每个词都必须匹配。#标签可缩小范围：#us、#germany、#air、#armor、#new（你模组的新单位）。输入 # 查看全部。", "search_tags": "标签：", "search_recent": "最近：", "tip_search_tag": "将 #{tag} 加入搜索：{label}。", "tip_search_recent": "再次搜索此内容。", "tag_new": "你模组的新单位"});
  // pop-ups (words.toml test_running, toast_log, tip_toast_log)
  Object.assign(words.us, {"test_running": "Testing in the game: building the modded copy…", "toast_log": "Log", "tip_toast_log": "Show everything the build said, and the fixes it offers for what stopped it."});
  Object.assign(words.fr, {"test_running": "Test en jeu : construction de la copie moddée…", "toast_log": "Journal", "tip_toast_log": "Afficher tout ce qu'a dit la construction, et les corrections qu'elle propose pour ce qui l'a arrêtée."});
  Object.assign(words.sc, {"test_running": "在游戏中测试：正在构建模组副本…", "toast_log": "日志", "tip_toast_log": "显示构建输出的全部内容，以及针对导致其停止的问题的修复方法。"});
  // a key another action has (words.toml keys_clash, keys_swap, keys_take, tip_keys_*)
  Object.assign(words.us, {"keys_clash": "{key} is already used by {other}.", "keys_swap": "Swap", "tip_keys_swap": "{action} gets {key}, and {other} gets {old}.", "tip_keys_swap_none": "{action} gets {key}. {other} is left without a key, as {action} had none to give it.", "keys_take": "Take it", "tip_keys_take": "{action} gets {key}. {other} is left without a key until you give it one."});
  Object.assign(words.fr, {"keys_clash": "{key} sert déjà à : {other}.", "keys_swap": "Échanger", "tip_keys_swap": "{action} prend {key}, et {other} prend {old}.", "tip_keys_swap_none": "{action} prend {key}. {other} reste sans touche, car {action} n'en avait pas à lui donner.", "keys_take": "La prendre", "tip_keys_take": "{action} prend {key}. {other} reste sans touche jusqu'à ce que vous lui en donniez une."});
  Object.assign(words.sc, {"keys_clash": "{key} 已被“{other}”使用。", "keys_swap": "交换", "tip_keys_swap": "“{action}”改用 {key}，“{other}”改用 {old}。", "tip_keys_swap_none": "“{action}”改用 {key}。由于“{action}”原本没有按键，“{other}”将没有按键。", "keys_take": "占用", "tip_keys_take": "“{action}”改用 {key}。“{other}”将没有按键，直到你为它指定一个。"});
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
    const made = mine().find((n) => address === newAddress(n.id));
    if (/Building_/.test(made ? made.source : address)) {  // (the game's buildings: no model the Studio finds)
      return { models: [], textures: [], painted: [], download: "https://www.blender.org/download/", blender: "",
               opened: false, new_unit: Boolean(made), own_model: null, own_copy: false, soldiers: false };
    }
    return { models: ["ww2\\res3d\\units\\fake\\" + address.split("/").pop().toLowerCase() + "lod0.ase2ndfbin"],
             textures: [pic], painted: fakePainted.has(address) ? [pic] : [], download: "https://www.blender.org/download/",
             blender: mode === "noblender" ? "" : "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe",
             opened: fakeLooks.has(address), new_unit: mine().some((n) => address === newAddress(n.id)),
             own_model: fakeModels.get(address) || null, own_copy: fakeModelCopies.has(address),
             soldiers: fakeSquad(address) };
  }
  // a building's look (building_look): a made-up factory look's pieces, biggest first; a new building's own model
  const fakeBuildingModels = new Map();
  function fakeBuildingLook(address) {
    const made = mine().find((n) => address === newAddress(n.id));
    if (!/Building_/.test(made ? made.source : address)) {
      return { building: false, card: null, new_unit: false, symbol: null, pieces: [], own: null };
    }
    return { building: true, card: fakeCard(address), new_unit: Boolean(made), symbol: "US_Prototype_Factory",
      pieces: [["Prototype_building", 1, 33.4, 29.2, 12.8], ["US_Research_Center", 1, 16.5, 17.8, 18.6],
        ["Maintenance_Hangar_simple_ouvert", 2, 22.2, 8.3, 5.3], ["Tour_radio", 2, 10.1, 10.1, 11.8]]
        .map(([name, count, w, d, h]) => ({ type: `TypeWarrior/${name}`, name, count, size: [w, d, h] })),
      own: fakeBuildingModels.get(address) || null };
  }
  // a squad (its look is its uniform: Default or Custom) and the truck it rides in (rides_in): the GI squad and its copies
  const fakeSquad = (address) => /Soldat/.test(address)
    || mine().some((n) => address === newAddress(n.id) && /Soldat/.test(n.source));
  const FAKE_TRUCKS = [["$/GFX/Everything/Descriptor_Unit_TransportSoldier", "TRUCK"],
    ["$/GFX/Everything/Descriptor_Unit_TransportSoldier_GER", "OPEL BLITZ"],
    ["$/GFX/Everything/Descriptor_Unit_TransportSoldier_UK", "BEDFORD"]];
  const fakeRides = new Map();  // squad -> the truck the mod has it ride in
  function fakeRidesIn(address) {
    if (!fakeSquad(address)) return {};
    const game = FAKE_TRUCKS[0][0];
    return { now: fakeRides.get(address) || game, game, choices: FAKE_TRUCKS.map(([a, name]) =>
      ({ address: a, name, code: a.split("/").pop(), new: false })) };
  }
  const fakeModelCopies = new Set();  // units with their own copy of the model (model_copy): a squad's custom uniform
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
  // two made-up problems as rusemod.plainproblems.explain gives them: a water stroke without its level (Studio 0.7.0
  // saved some), and a placed object with a setting the game doesn't know
  const fakeFile = "maps/SuperCrossRoads4/terrain.toml", fakeSceneryFile = "maps/SuperCrossRoads4/scenery.toml";
  const blitz = { us: "Blitz", fr: "Blitz" };
  let checkProblems = [
    { file: fakeFile, set_aside: true, problem: `${fakeFile}: stroke 1: the water brush needs level`,
      plain: { kind: "missing", file: fakeFile, map: "SuperCrossRoads4", table: "stroke", item: "stroke", n: 1, keys: ["level"], key: "level", map_titles: blitz },
      fixes: [{ fix: "fill", file: fakeFile, table: "stroke", n: 1, key: "level" }, { fix: "remove_item", file: fakeFile, table: "stroke", n: 1 },
        { fix: "set_aside", file: fakeFile }] },
    { file: fakeSceneryFile, set_aside: true, problem: `${fakeSceneryFile}: object 3: unknown key 'colr'`,
      plain: { kind: "unknown_key", file: fakeSceneryFile, map: "SuperCrossRoads4", table: "object", item: "object", n: 3, key: "colr", map_titles: blitz },
      fixes: [{ fix: "remove_key", file: fakeSceneryFile, table: "object", n: 3, key: "colr" }, { fix: "remove_item", file: fakeSceneryFile, table: "object", n: 3 },
        { fix: "set_aside", file: fakeSceneryFile }] }];
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
  const owned = new Map();     // `${mod}|${map pack}` -> the map's own objects it moves or takes away ([[own]] tables)
  const fakeFormats = new Map();  // a mod folder -> its mod format (rusemod.modformat; 1 = this Studio's)
  const fakeFormat = (path) => {
    let f = fakeFormats.get(path);
    if (f === undefined) f = mode === "oldmod" ? 0 : mode === "newmod" && path.endsWith("another-mod") ? 2 : 1;
    return { format: f, current: 1, state: f > 1 ? "newer" : f < 1 ? "older" : "same", steps: f < 1 ? 1 : 0 };
  };
  // The made-up village's objects as the real map_objects_at gives the map's own (every one, where the file has it)
  const fakeOwnObjects = (pack) => {
    const d = fakeScenery(pack), full = new Map(d.palette.map((row) => [row[7], row[0]])), out = [];
    for (const [group, flat] of Object.entries(d.items)) {
      for (let k = 0; k < flat.length; k += 5) {
        out.push({ type: full.get(flat[k]) || `TypeWarrior/${d.types[flat[k]][0]}`, group, x: flat[k + 1],
          y: flat[k + 2], turn: flat[k + 3] * 180 / Math.PI, size: flat[k + 4], lift: 0 });
      }
    }
    return out;
  };
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
  // the flag guide for the made-up flags (rusemod/flaginfo.toml), and its check: the truck flags crash on anything but a truck
  const FAKE_FLAG_GUIDE = {"1": {"group": "combat", "sure": "tried", "what": "Artillery (indirect fire)", "does": "The unit fires indirectly, at what other units spot, like the game's howitzers. Also tells the computer player to use it as artillery.", "use": "Works on any unit: DomesticNukes gave it to 410 units of all kinds and they all fired indirectly.", "danger": "", "danger_why": ""}, "10": {"group": "combat", "sure": "units", "what": "Can take damage", "does": "Explosions can hurt it: splash damage and the V2 look for units with it. 454 of the game's units have it.", "use": "Keep it on anything that should be hurt by explosions. Without it a unit may be immune to splash damage (not tried).", "danger": "", "danger_why": ""}, "11": {"group": "movement", "sure": "tried", "what": "Can't enter woods", "does": "The unit stays out of woods (its paths go round them) and never gets the woods' cover. Tanks and most vehicles have it.", "use": "To let a vehicle into woods, take 11, 21 and 55 off together (tried by DomesticNukes). 11 is the one that matters for woods.", "danger": "", "danger_why": ""}, "21": {"group": "combat", "sure": "tried", "what": "Fighting unit", "does": "A unit that fights: the game also adds it while a unit attacks. The computer player's danger estimate and the statistics count it.", "use": "Part of the woods trio: take 11, 21 and 55 off together to let a vehicle into woods.", "danger": "", "danger_why": ""}, "22": {"group": "player", "sure": "units", "what": "Takes the player's orders", "does": "The player can order it. Mission scripts take it off to lock a unit.", "use": "Keep it on anything the player should control.", "danger": "breaks", "danger_why": "Without it the player can't order the unit (the community lists it as essential)."}, "55": {"group": "kind", "sure": "tried", "what": "Tank", "does": "Counts as a tank in the end-of-game statistics and in the missions' 'tank' category. Nothing else: it has no effect of its own in a battle.", "use": "Part of the woods trio: take 11, 21 and 55 off together to let a vehicle into woods.", "danger": "", "danger_why": ""}, "62": {"group": "kind", "sure": "tried", "what": "Truck", "does": "A truck: driven by the game's truck logic (it has no thinking of its own), carries supplies. Every one of the game's 18 trucks has it.", "use": "Only on trucks (TTruckDescriptor units), and every truck needs it.", "danger": "crash", "danger_why": "On anything but a truck the game crashes when the match starts (DomesticNukes, on a Stuart). The Studio won't build it."}, "63": {"group": "kind", "sure": "tried", "what": "Construction truck", "does": "A truck that builds buildings.", "use": "Only on construction trucks.", "danger": "crash", "danger_why": "On anything but a truck the game crashes (ProLution). The Studio won't build it."}, "72": {"group": "sight", "sure": "units", "what": "Sees through obstacles", "does": "Its sight ignores hills and scenery. Planes have it.", "use": "Not tried on ground units yet.", "danger": "", "danger_why": ""}, "91": {"group": "state", "sure": "tried", "what": "Camouflaged (the ruse card)", "does": "The camouflage card sets and clears it. In a unit's list it does nothing (tried).", "use": "Leave it out.", "danger": "", "danger_why": ""}, "99": {"group": "kind", "sure": "tried", "what": "Recon plane", "does": "The plane behaves as a scout (unless it also has 100): a click on the map sends it to look, it doesn't count in its team's army and the recon panel shows it. A scout never attacks.", "use": "Use the Studio's Role box: Scout on an armed plane also sets 100 so its attacks keep working.", "danger": "crash", "danger_why": "A plane that has weapons and 99 without 100 crashes the game when it's sent to attack (T53-T56). The Studio won't build a plane you gave 99 that way: add 100 too, or take 99 off."}, "100": {"group": "kind", "sure": "units", "what": "Fighter", "does": "The plane behaves as a fighter (checked first, before 99, 101 and 13): on its own it only attacks planes in the air; clicking an enemy attacks it.", "use": "For fighters. With 99 too, it's an armed scout that can still attack.", "danger": "", "danger_why": ""}, "2": {"group": "kind", "sure": "units", "what": "Aircraft", "does": "The unit is a plane: built at the airfield's control tower, flies home to refuel, takes no ground orders. Every one of the game's 63 planes has it, and nothing else does.", "use": "Keep it on every plane. Never put it on a ground unit: the game would try to build it at an airfield's control tower.", "danger": "breaks", "danger_why": "On a unit that isn't a plane, building it is expected to stop the game with a script error (it looks for an airfield's control tower)."}, "43": {"group": "player", "sure": "expected", "what": "Counted by its team", "does": "The unit is filed in its team's lists and counts, and the missions' scripts see it. 459 of the game's units have it.", "use": "Never take it off.", "danger": "breaks", "danger_why": "Without it the unit is expected to be in none of its team's lists: missions and the computer player don't see it."}};
  // the number guide for the numbers the fake shows (rusemod/numberinfo.toml), and a made-up scale for each
  const FAKE_NUMBERS = { numbers: {"AttaqueTempsActivation": {"group": "computer", "unit": "s", "sure": "known", "what": "Seconds before it starts attacking", "does": "How many seconds into the battle it waits before it attacks at all; until then it also doesn't harass or send help to a threatened depot. Default 30; Easy 300 (5 minutes); Turtle 600 (10 minutes). Hard and Blitzkrieg don't list it, so they count 0: they attack from the first second."}, "OffensiveNbMissionMax": {"group": "computer", "unit": "count", "sure": "known", "what": "Most attacks at once", "does": "The most attacks (and retaliations) it runs at the same time. -1 means no limit, which every set of the game uses."}, "HarcelementActif": {"group": "computer", "unit": "yesno", "sure": "known", "what": "Harasses the enemy", "does": "1: it harasses (small raids, once its wait before attacking is over). 0: never. Easy and Turtle don't list it, so they count 0 and never harass."}, "PercentMoneyToReserveForBatimentAdmin": {"group": "computer", "unit": "pct", "sure": "name", "what": "% of money kept for admin buildings", "does": "The share of its money, in %, it keeps for admin buildings (which raise income). 20% in the game's sets; Hard 25%."}, "DeviseBonusIA": {"group": "computer", "unit": "money", "sure": "known", "what": "Extra money at the start (cheat)", "does": "Extra money it gets when the battle starts, in $. Only Hard has it: $150 on top of the $200 every player starts with."}, "IncomeBonusIA": {"group": "computer", "unit": "money", "sure": "known", "what": "Extra income each payment (cheat)", "does": "Extra money, in $, added to each of its income payments. Only Hard has it: $1."}, "NbProdIdleTank": {"group": "computer", "unit": "count", "sure": "known", "what": "Built when idle: tanks", "does": "When it has nothing else to do and may spend money idle, it builds tanks until it has this many. Regular and Prototype 3; Blitzkrieg 4."}, "BonusValue": {"group": "computer", "unit": "pts", "sure": "known", "what": "Extra preference for these units", "does": "Preference points added to the units listed, in a battle whose game mode, difficulty and personality are each in the lists (an empty list matches any). They add to the set's own preferences (Preference: planes...). The game's own entry: +400 for the nuclear guns in Nuclear mode, on every difficulty and personality."}, "UnitIDs": {"group": "computer", "unit": "id", "sure": "known", "what": "Units (by number)", "does": "The units the entry is for, by each unit's own number (its Id); the AI tab lets you pick them by name. An empty list would mean every unit."}, "WarModes": {"group": "computer", "unit": "choice", "sure": "known", "what": "Game modes (by number)", "does": "The game modes the entry works in, by the number the game gives them: 0 1945, 1 1942, 2 1939, 3 Total War mode, 4 Nuclear mode (the order of the game's own list)."}, "AIDifficulties": {"group": "computer", "unit": "choice", "sure": "known", "what": "Difficulties (by number)", "does": "The difficulties the entry works on: 0 Easy, 1 Medium, 2 Hard."}, "AIProfiles": {"group": "computer", "unit": "choice", "sure": "known", "what": "Profiles (by number)", "does": "The personalities the entry works with: 0 Regular, 1 Air Force, 2 Howitzer, 3 Prototype, 4 Blitzkrieg, 5 Turtle, 6 Random."}, "TBluffCardDescriptor.LifeDuration": {"group": "computer", "unit": "s", "sure": "name", "what": "How long it lasts", "does": "How long the ruse lasts once played, in seconds: 240 to 360 in the game (4 to 6 minutes)."}, "TBluffCardDescriptor.ShowInMenu": {"group": "computer", "unit": "yesno", "sure": "name", "what": "Shown in the ruse menu", "does": "1: the card is in the ruse menu, so players and the computer can play it."}, "TBluffCardDescriptor.PositionInMenu": {"group": "computer", "unit": "id", "sure": "name", "what": "Ruse menu slot", "does": "Where the card sits in the ruse menu: lower comes first."}, "ProductionPrice": {"group": "production", "unit": "money", "sure": "known", "what": "Price", "does": "What it costs to build, in $, in each of the game's five game modes, in its order: 1945, 1942, 1939, Total War, Nuclear (the game uses the one of the battle's mode)."}, "ProductionTime": {"group": "production", "unit": "s", "sure": "known", "what": "Build time", "does": "How many seconds it takes to build. With more than one factory of its kind building it, the time is divided between them, but never below the game's shortest build time (the Economy tab's Shortest build time)."}, "SeuilMort": {"group": "health", "unit": "pts", "sure": "known", "what": "Health", "does": "How much damage it takes to destroy it. Most of the game's tanks, cars, squads and guns have 400: what makes a Tiger tougher than a jeep is mostly its armour level (Armour), which cuts the damage of every shot that isn't strong enough for it. Buildings have from 50 to 4,500."}, "VitesseLineaire": {"group": "movement", "unit": "kmh", "sure": "known", "what": "Speed", "does": "How fast it moves when travelling, off roads. A Sherman has 4,550 (about 35 km/h), a jeep 6,110 (about 47 km/h), a rifle squad 3,120 (about 24 km/h)."}, "TAvionDescriptor.VitesseLineaire": {"group": "flight", "unit": "kmh_air", "sure": "known", "what": "Flying speed", "does": "How fast the plane flies: 13,000 to 46,800 in the game (about 225 to 810 km/h)."}, "DetectionBase": {"group": "sight", "unit": "m", "sure": "tried", "what": "Vision range", "does": "How far it sees ground units. A tank 104,000 (about 400 m); recon cars 234,000 (900 m); scout planes 195,000 (750 m). A Panzer IV given 234,000 alone didn't act as recon; the Role box gives the rest."}, "Factory": {"group": "menu", "unit": "choice", "sure": "known", "what": "Factory", "does": "Which build menu it's in (the Studio shows each menu by its name, and lets you move a unit to another nation's)."}, "PositionInMenu": {"group": "menu", "unit": "id", "sure": "known", "what": "Menu slot", "does": "Where it sits in its build menu: units of the same line share a slot, upgrades stack on it."}, "Nationalite": {"group": "identity", "unit": "choice", "sure": "known", "what": "Nation", "does": "Which country it belongs to: 0 USA, 1 Germany, 2 UK, 3 France, 4 Italy, 5 USSR, 6 Japan."}, "DescriptorId": {"group": "identity", "unit": "id", "sure": "known", "what": "Id", "does": "The unit's own number: each unit has a different one, and the game and saved games find it by it. The Studio gives a new unit a free one."}, "VitesseRotation": {"group": "turret", "unit": "degs", "sure": "name", "what": "Turret turning speed", "does": "How fast the turret or gun turns to aim: 15 to 200 degrees a second. Slower turrets take longer to bring their gun onto a new target."}, "TirEnMouvement": {"group": "combat", "unit": "yesno", "sure": "name", "what": "Fires on the move", "does": "1: this weapon can fire while the unit moves."}, "Puissance": {"group": "ammo", "unit": "pts", "sure": "known", "what": "Damage", "does": "The damage one hit does, before armour. Small arms 2-10, tank guns tens to hundreds, bombs and the V2 far more (up to 2,000,000 for the atom bomb). A unit is destroyed when the damage it took reaches its Health."}}, plain: {"m": [260.0, "unit_m"], "kmh": [130.0, "unit_kmh"], "kmh_air": [57.78, "unit_kmh"], "deg": [0.017453292519943295, "unit_deg"], "degs": [0.017453292519943295, "unit_degs"], "s": [1.0, "unit_s"], "money": [1.0, "unit_money"], "share": [0.01, "unit_pct"], "pct": [1.0, "unit_pct"], "min": [1.0, "unit_min"]}, amounts: ["accel", "count", "deg", "degs", "kmh", "kmh_air", "level", "m", "money", "pts", "raw", "s", "share", "times", "pct", "min"], modes: ["1945 era", "1942 era", "1939 era", "Total War mode", "Nuclear mode"] };
  // some of the Economy tab's values (rusemod/numberinfo.toml, the economy's part)
  Object.assign(FAKE_NUMBERS.numbers, {"QteDeviseInitiale": {"group": "production", "unit": "money", "sure": "tried", "what": "Starting money", "does": "The money every player starts a battle with, in $. 200 in the game: ten Shermans at $20."}, "QteDeviseParCamion": {"group": "production", "unit": "money", "sure": "known", "what": "Money per truckload", "does": "What one supply truck brings from a depot, in $. The game's usual modes 3, the Nuclear mode 6. A depot's money left is its truckloads left times this."}, "TempsGenAutoDevises": {"group": "production", "unit": "s", "sure": "known", "what": "Seconds between automatic payments", "does": "How often, in seconds, the buildings that make money by themselves pay out (the game's automatic money); the computer players' income cheat is paid on the same beat. 4 in the game."}, "NbInitialCardsInPoolForAllianceTaille_1": {"group": "production", "unit": "count", "sure": "tried", "what": "Ruse cards at the start (1 player a side)", "does": "How many ruse cards a side starts with when it has 1 player. The game's usual modes 2, the Nuclear mode 4."}, "PaliersTempsToChooseNewCardForAllianceTaille_1": {"group": "production", "unit": "s", "sure": "name", "what": "When new ruse cards come (1 player a side)", "does": "The battle times, in seconds, at which a side with 1 player gets a new ruse card to pick. The game's usual modes 105, 210, 315 (every 1 3/4 minutes); the Nuclear mode 80, 160, 240."}, "MinProductionTime": {"group": "production", "unit": "s", "sure": "known", "what": "Shortest build time", "does": "No unit takes less time to build than this, in seconds, however many factories of its kind build it. 1 in the game."}, "RatioForDepotNearlyDepleted": {"group": "production", "unit": "share", "sure": "known", "what": "Depot nearly empty at", "does": "A depot counts as nearly empty when the truckloads it has left are this share of what it started with or less (the computer players then look for another). 0.25 (25%) in the game."}, "CheckAndCancelWaitingRequest": {"group": "computer", "unit": "yesno", "sure": "known", "what": "Cancel waiting orders", "does": "1: a computer player cancels production orders that waited longer than the longest wait. 1 in the game."}});
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
  const mapSizes = new Map();
  function fakeMapSize(pack) {
    const cells = (current && mapSizes.get(`${current}|${pack}`)) || [4, 4], k = 327680 / 260 / 1000;
    return { cells, copied: [4, 4], km: cells.map((c) => Math.round(c * k * 10) / 10), can: true,
      why: "", most: 128, tile: 2,
      clouds: null, room: null };
  }
  // search with tags (StudioApi.search_terms, units "tags"): every word must match, every #tag start one of its tags
  const NATION_TAGS = ["us", "germany", "uk", "france", "italy", "ussr", "japan"];
  function fakeTagsOf(u) {
    const g = u.group === "fake" ? "decoy" : u.group;
    return [u.kind === "buildings" ? "building" : u.kind, g, NATION_TAGS[u.nation], ...(u.new ? ["new"] : [])].filter(Boolean);
  }
  function fakeFinds(search, said, tags) {
    const terms = (search || "").toLowerCase().split(/\s+/).filter(Boolean), text = said.join(" ").toLowerCase();
    return terms.every((t) => (t.startsWith("#") ? t.length < 2 || tags.some((o) => o.startsWith(t.slice(1))) : text.includes(t)));
  }
  function fakeTagList(list, lang) {
    const names = nations[lang] || nations.us, out = new Map();
    for (const u of list) {
      out.set(NATION_TAGS[u.nation], names[u.nation]);
      out.set(u.kind === "buildings" ? "building" : u.kind, u.kind);
      out.set(u.group === "fake" ? "decoy" : u.group, u.group);
      if (u.new) out.set("new", "new");
    }
    return [...out].filter(([k]) => k).sort().map(([tag, label]) => ({ tag, label }));
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
  // the Sectors brush's fake: strokes per map and scenario, cells worked out on a small grid (no checks)
  const sectorPaints = new Map();
  function fakeSectors(pack, file) {
    const key = `${current}|${pack}|${file}`;
    if (!sectorPaints.has(key)) sectorPaints.set(key, { strokes: [], empty: false });
    return sectorPaints.get(key);
  }
  function fakeSectorView(pack, file, outlines) {
    const f = fakeSectors(pack, file), n = 64, size = 1310720, step = size / n, cells = new Array(n * n);
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) cells[i * n + j] = f.empty ? 0 : (j < n / 2 ? 1 : 2);
    const inside = (pts, x, y) => {   // the even-odd test (rusemod.sectors.polygon_mask)
      let c = false;
      for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
        const [xi, yi] = pts[i], [xj, yj] = pts[j];
        if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c;
      }
      return c;
    };
    for (const s of f.strokes) {
      if (s.auto) {   // Make sectors (StudioApi.sector_auto): a grid of sectors about that wide, its lines bent a little
        const k = Math.max(1, Math.round(size / (s.auto * 260))), wob = (u) => Math.sin(u * 0.37 + s.seed * 1.7) * 0.18;
        for (let i = 0; i < n; i++) {
          for (let j = 0; j < n; j++) {
            const col = Math.min(k - 1, Math.max(0, Math.floor((j / n + wob(i) / k) * k)));
            const row = Math.min(k - 1, Math.max(0, Math.floor((i / n + wob(j + 9) / k) * k)));
            cells[i * n + j] = row * k + col + 1;
          }
        }
        continue;
      }
      if (s.area) {   // a sector's new shape (StudioApi.sector_area): what it gave up goes to no sector here, a
        // sector taken out gives its ground to the nearest other sector in its row (sector -1: a No sector box)
        const own = s.sector + 1, freed = [];
        if (own > 0) for (let k = 0; k < cells.length; k++) if (cells[k] === own) { cells[k] = 0; freed.push(k); }
        for (let i = 0; i < n; i++) {
          for (let j = 0; j < n; j++) if (s.area.length >= 3 && inside(s.area, (j + 0.5) * step, (i + 0.5) * step)) cells[i * n + j] = own;
        }
        if (!s.area.length) {
          for (const k of freed) {
            const row = k - (k % n);
            for (let d = 1; d < n; d++) {
              const near = [k - d, k + d].find((q) => q >= row && q < row + n && cells[q] > 0 && cells[q] !== own);
              if (near !== undefined) { cells[k] = cells[near]; break; }
            }
          }
        }
        continue;
      }
      for (const [x, y] of s.points) {
        for (let i = 0; i < n; i++) {
          for (let j = 0; j < n; j++) {
            const dx = (j + 0.5) * step - x, dy = (i + 0.5) * step - y;
            const t = s.shape === "square" ? Math.max(Math.abs(dx), Math.abs(dy)) / s.radius : Math.hypot(dx, dy) / s.radius;
            if (t < 1) cells[i * n + j] = s.sector + 1;
          }
        }
      }
    }
    const runs = [];
    for (const v of cells) {
      if (runs.length && runs[runs.length - 2] === v) runs[runs.length - 1] += 1;
      else runs.push(v, 1);
    }
    const numbers = [...new Set(cells)].filter((v) => v > 0).map((v) => v - 1).sort((a, b) => a - b);
    const sectors = numbers.map((num) => {
      const at = cells.indexOf(num + 1);
      return { number: num, cells: cells.filter((v) => v === num + 1).length * 16,
        x: ((at % n) + 0.5) * step, y: (Math.floor(at / n) + 0.5) * step };
    });
    const lines = outlines ? Object.fromEntries(sectors.map((s) => [String(s.number),
      [s.x - step, s.y - step, s.x + step, s.y - step, s.x + step, s.y + step, s.x - step, s.y + step]])) : null;
    const free = [...Array(255).keys()].find((k) => !numbers.includes(k));
    const made = f.strokes.filter((s) => s.auto).pop();
    return { file, nx: n, ny: n, box: [0, 0, size, size], runs, sectors, problems: [], empty: !numbers.length,
      starts_empty: f.empty, whole_map: false, strokes: f.strokes.length, auto: made ? { metres: made.auto, seed: made.seed } : null,
      next: free === undefined ? null : free, tidied: [], outlines: lines };
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
        if (sp.file !== s.file) return;
        const it = { kind: "Spawn", x: sp.x, y: sp.y, turn: sp.rotation || 0, name: "", camp: sp.camp, what: sp.what,
          mine: true, spawn: n, item: s.items.length };
        if (sp.what === "DalleBatimentDepot") Object.assign(it, { trucks: sp.trucks ?? 25, group: "depot", icon: "depot" });
        s.items.push(it);
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
  // the zone brushes' marks and counts, Town's preview, and the place list's pictures (2026-10-15)
  Object.assign(words.us, { legend_cover_taken: "Cover taken away (Uncover, trees erased): units are seen here (striped)",
    legend_move_opened: "Opened with an Open brush: units can go here (striped)",
    legend_move_changed: "Striped colours: changed with a Block or Open brush",
    town_preview: "Click: cover around these {n} buildings.", town_point: "Point at a town's buildings: they get rings first.",
    zone_cover_done: "Units hide here now: {m2} m² of new cover.",
    zone_cover_none: "This ground already had cover: nothing changed for units ({m2} m² marked).",
    zone_uncover_done: "Cover taken away from {m2} m²: units are seen there now.",
    zone_uncover_none: "No cover here to take away: this ground had none ({m2} m² marked, striped).",
    zone_block_done: "Closed {m2} m² to these units.",
    zone_block_none: "Already closed to these units: nothing changed ({m2} m² marked, striped).",
    zone_open_done: "Opened {m2} m²: units can go there now.",
    zone_open_none: "Units could already go here: nothing changed ({m2} m² marked, striped blue).",
    place_used: "{n} on this map", place_no_picture: "No picture: the Studio can't show this one's model yet. It's placed all the same." });
  Object.assign(words.fr, { legend_cover_taken: "Couvert retiré (Découvrir, arbres effacés) : les unités y sont vues (rayé)",
    legend_move_opened: "Ouvert au pinceau Ouvrir : les unités passent (rayé)",
    legend_move_changed: "Couleurs rayées : changées au pinceau Bloquer ou Ouvrir",
    town_preview: "Cliquez : du couvert autour de ces {n} bâtiments.",
    town_point: "Pointez les bâtiments d'une ville : ils s'entourent d'abord d'anneaux.",
    zone_cover_done: "Les unités s'y cachent maintenant : {m2} m² de nouveau couvert.",
    zone_cover_none: "Ce terrain avait déjà du couvert : rien ne change pour les unités ({m2} m² marqués).",
    zone_uncover_done: "Couvert retiré sur {m2} m² : les unités y sont vues maintenant.",
    zone_uncover_none: "Pas de couvert à retirer ici : ce terrain n'en avait pas ({m2} m² marqués, rayés).",
    zone_block_done: "{m2} m² fermés à ces unités.",
    zone_block_none: "Déjà fermé à ces unités : rien ne change ({m2} m² marqués, rayés).",
    zone_open_done: "{m2} m² ouverts : les unités peuvent y aller maintenant.",
    zone_open_none: "Les unités passaient déjà ici : rien ne change ({m2} m² marqués, rayés de bleu).",
    place_used: "{n} sur cette carte",
    place_no_picture: "Pas d'image : le Studio ne sait pas encore montrer son modèle. Il est placé quand même." });
  Object.assign(words.sc, { legend_cover_taken: "掩护已移除（移除掩护、擦除的树）：单位在此可被看到（条纹）",
    legend_move_opened: "用“开放”画笔开放：单位可以进入（条纹）", legend_move_changed: "条纹颜色：用“封锁”或“开放”画笔改过的地方",
    town_preview: "点击：在这 {n} 栋建筑周围加掩护。", town_point: "指向城镇的建筑：会先出现圆圈。",
    zone_cover_done: "单位现在可以在此隐藏：新增掩护 {m2} 平方米。",
    zone_cover_none: "这里原本就有掩护：对单位没有变化（已标记 {m2} 平方米）。",
    zone_uncover_done: "已移除 {m2} 平方米的掩护：单位现在在那里可被看到。",
    zone_uncover_none: "这里没有可移除的掩护：原本就没有（已用条纹标记 {m2} 平方米）。",
    zone_block_done: "已对这些单位封锁 {m2} 平方米。", zone_block_none: "已对这些单位封锁：没有变化（已用条纹标记 {m2} 平方米）。",
    zone_open_done: "已开放 {m2} 平方米：单位现在可以去那里。",
    zone_open_none: "单位本来就能到这里：没有变化（已用蓝色条纹标记 {m2} 平方米）。",
    place_used: "本地图上有 {n} 个", place_no_picture: "无图片：Studio 暂时无法显示它的模型。仍会照常放置。" });
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
      can_upgrade: !address.includes(":") && cls !== "TAmmunition", in_game: true,
      has_armour: !address.includes(":") && cls !== "TAmmunition" };
  }
  // the Armour box (StudioApi.armour): the game's levels, every made-up unit armour 2 (BaseBlindage 6) in the game
  const armourEdits = new Map();  // address -> the mod's level (BaseBlindage)
  const ARMOUR_LEVELS = [[5, "armour_tank", 1], [6, "armour_tank", 2], [7, "armour_tank", 3], [8, "armour_tank", 4],
    [9, "armour_tank", 5], [4, "armour_light", 0], [3, "armour_infantry", 0], [1, "armour_aircraft", 0],
    [2, "armour_para", 0], [10, "armour_trucks", 0]].map(([value, word, n]) => ({ value, word, n }));
  function armourOf(address) {
    return { levels: ARMOUR_LEVELS, game: 6, value: armourEdits.has(address) ? armourEdits.get(address) : null,
      old: null, editable: true };
  }
  // the Upgrade box (StudioApi.upgrade): every made-up unit may be an upgrade of the first one, which has none
  const upgradeEdits = new Map();  // address -> the mod's parent (null: a unit of its own)
  const researchEdits = new Map();  // `${address}|${prop}` -> the mod's research price or time
  function upgradeOf(address, lang) {
    const all = units.map((u) => ({ address: E + u.id, name: lang === "base" ? u.id : u.names[lang] || u.names.us }))
      .concat(mine().map((n) => ({ address: newAddress(n.id), name: n.name })));  // the mod's new units chain too
    const gameParent = address === all[0].address ? null : all[0];
    const linked = upgradeEdits.get(address);
    // researched from a unit no longer in the mod (taken out after the warning): StudioApi.upgrade's parent_gone
    const parentGone = Boolean(linked) && !all.some((x) => x.address === linked);
    const parent = !upgradeEdits.has(address) ? gameParent : !linked ? null
      : all.find((x) => x.address === linked) || { address: linked, name: linked.slice(E.length) };
    const research = {};
    for (const [prop, labelText, game] of [["UpgradePrice", "Upgrade price", 25], ["UpgradeTime", "Upgrade time", 50]]) {
      const key = `${address}|${prop}`;
      research[prop] = { label: lang === "base" ? prop : labelText, game: gameParent ? game : null,
        value: researchEdits.has(key) ? researchEdits.get(key) : null };
    }
    const linkedHere = [...upgradeEdits.entries()].filter(([, p]) => p === address).map(([a]) => all.find((x) => x.address === a))
      .filter(Boolean);
    return { address, parent, game_parent: gameParent, parent_gone: parentGone,
      choices: all.filter((x) => x.address !== address && !linkedHere.includes(x)),
      children: [...(address === all[0].address ? all.slice(1, 3) : []), ...linkedHere], research };
  }

  // Before a new unit goes (StudioApi._research_gone): the units the mod researches from it, dealt with as the modder
  // chose in Settings > Research (prefs.research_gone; "anyway": the warning's go-ahead)
  function researchGone(address, researched) {
    const info = upgradeOf(address, "us");
    const children = info.children.filter((c) => upgradeEdits.get(c.address) === address);
    if (!children.length) return { relinked: [], left: [] };
    const how = ["warn", "refuse", "relink", "anyway"].includes(researched) ? researched
      : ["warn", "refuse", "relink"].includes(prefs.research_gone) ? prefs.research_gone : "warn";
    if (how === "anyway") return { relinked: [], left: children };
    if (how === "warn") return { ask: children };
    if (how === "refuse") {
      throw new Error(`${(mine().find((n) => newAddress(n.id) === address) || { name: address }).name} stays in the mod: `
        + `${children.map((c) => c.name).join(", ")} ${children.length === 1 ? "is" : "are"} researched from it. Pick another unit to `
        + `research ${children.length === 1 ? "it" : "them"} from in ${children.length === 1 ? "its" : "their"} Upgrade and research `
        + "box first, or choose in Settings > Research what taking it out does.");
    }
    const up = info.parent && !info.parent_gone ? info.parent : null;
    return { left: [], relinked: children.map((c) => {
      if (up) upgradeEdits.set(c.address, up.address); else upgradeEdits.set(c.address, null);
      return { address: c.address, name: c.name, to: up };
    }) };
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
      u.kind === "buildings" ? "TBatimentDescriptor" : "TUniteAuSolDescriptor", nameOf(u, lang), true, "", 0, [
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
      hits: hitsEdits.get(weapon) || "ground", game_hits: "ground",
      own_copy: myAmmo().some((n) => ammoAddress(n.id) === current_) && firing.length === 1 }], choices };
  }

  // What a weapon hits and a plane's role (api.set_weapon_hits, plane_role, set_plane_role): kept here as the choices
  // only; a made-up plane is a fighter-bomber in the game
  const hitsEdits = new Map();
  const roleEdits = new Map();
  function roleOf(address) {
    const game = "fighter_bomber";
    return { role: roleEdits.get(address) || game, game, editable: Boolean(current), why: current ? "" : "no_mod",
      bombs: true, armed: true,
      roles: ["fighter", "fighter_bomber", "bomber", "scout"].map((id) => ({ id, seen: id === "bomber" })) };
  }
  const groundRoleEdits = new Map();
  function groundRoleOf(address) {
    return { role: groundRoleEdits.get(address) || "game", game: "game", editable: Boolean(current),
      why: current ? "" : "no_mod" };
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

  // Map Paint's textures in the preview: [ref, group, words, colour], each drawn as a checker of its colour
  const fakeTextures = [["game:france/stickers01/herbe_verte", "grass", ["green", "grass"], "#4f6e2a"],
    ["game:france/stickers01/labourage", "fields", ["ploughed"], "#7a6040"],
    ["game:france/stickers01/terre", "earth", ["earth"], "#6a4a30"],
    ["game:italie/stickers/sable", "sand", ["sand"], "#b09060"],
    ["game:ardennes/stickers/plaque_neige", "snow", ["snow"], "#dcdcd8"],
    ["game:france/stickers01/cour_paves", "town", ["yard", "cobbles"], "#7a7068"]];
  const fakeOwnPictures = [];
  // the palette in the preview (groundtex.palette): [name, label, kind, metres, colour], each a checker of its colour
  const fakePalette = [["wheat", "Wheat", "rows", 38, "#8a732b"], ["ploughed", "Ploughed earth", "rows", 41, "#825b2a"],
    ["grass", "Grass", "plain", 40, "#405d10"], ["sand", "Sand", "plain", 20, "#7e572b"],
    ["mud", "Mud", "plain", 40, "#605719"], ["rock", "Rock", "plain", 30, "#51412b"]];
  // Online (free) in the preview: [id, name, metres, colour] per source, nothing downloaded (groundtex_online)
  const fakeOnline = {
    polyhaven: [["aerial_beach_01", "Aerial Beach 01", 30, "#c8b48a"], ["aerial_grass_rock", "Aerial Grass Rock", 30,
      "#5a7040"], ["snow_field_aerial", "Snow Field Aerial", 30, "#e4e8ec"], ["rocky_terrain", "Rocky Terrain", 8,
      "#80786c"]],
    ambientcg: [["Grass005", "Grass 005", null, "#4a6a2a"], ["Ground054", "Ground 054", 2, "#6a5a40"],
      ["Gravel022", "Gravel 022", null, "#8a8478"]],
  };
  const fakePlaces = [["wheat_kansas", "Wheat fields (Kansas)", 38.35, -98.6, "#c8b070"],
    ["pines_arizona", "Pine forest (Arizona)", 35.05, -111.65, "#3a5a30"],
    ["dunes_california", "Sand dunes (California)", 32.95, -115.1, "#d8c090"]];
  function fakeChecker(a, b) {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"><rect width="8" height="8" fill="${a}"/>`
      + `<rect width="4" height="4" fill="${b}"/><rect x="4" y="4" width="4" height="4" fill="${b}"/></svg>`;
    return "data:image/svg+xml;base64," + btoa(svg);
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
    // (the basket stands nowhere on the map: it's there to place, so it has a number too, as rusemod.scenery.view does)
    const types = [["MairieNormande", "building", "COC/Normandie/Batiments_Villes_Villages", ""],
      ["TownHouseB2_Haut", "building", "COC/Normandie/BatimentsMorceaux/TownHouseB/B2", ""],
      ["Charette_1", "prop", "Props/Ferme", ""], ["Chene_02", "vegetation", "Vegetation/Arbres", ""],
      ["Cotentin_PanierOsier1", "prop", "Props/Ville", ""]];
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
        { us: "town building", fr: "bâtiment de ville", ger: "Stadtgebäude" }, 0],
      ["TypeWarrior/TownHouseB2_Haut", "TownHouseB2_Haut", "building", "COC/Normandie/BatimentsMorceaux/TownHouseB/B2", 39,
        { us: "Town house B 2 high", fr: "Maison de ville B 2 haut", ger: "Stadthaus B 2 hoch" },
        { us: "building piece", fr: "élément de bâtiment", ger: "Gebäudeteil" }, 1],
      ["TypeWarrior/Charette_1", "Charette_1", "prop", "Props/Ferme", 30, { us: "Cart 1", fr: "Charrette 1", ger: "Karren 1" },
        { us: "farm prop", fr: "objet de ferme", ger: "Hofgegenstand" }, 2],
      ["TypeWarrior/Cotentin_PanierOsier1", "Cotentin_PanierOsier1", "prop", "Props/Ville", 4,
        { us: "Wicker basket 1 (Cotentin)", fr: "Panier en osier 1 (Cotentin)", ger: "Weidenkorb 1 (Cotentin)" },
        { us: "town prop", fr: "objet de ville", ger: "Stadtgegenstand" }, 4],
      ["TypeWarrior/Chene_02", "Chene_02", "vegetation", "Vegetation/Arbres", 12000, { us: "Oak 2", fr: "Chêne 2", ger: "Eiche 2" },
        { us: "tree", fr: "arbre", ger: "Baum" }, 3]];
    return { types, items, palette, groups: { building: { shown: 40, total: 40 }, prop: { shown: 30, total: 30 },
      vegetation: { shown: 900, total: 12000 } } };
  }

  // the map mod's own models (asset_import), per mod
  const fakeAssets = new Map();
  function fakeAssetList() { return { assets: current ? (fakeAssets.get(current) || []) : [], mod: current }; }

  // Made-up models for the made-up types (a town hall, a tall house, a cart, an oak, a basket), as map_models gives
  // them (an index and one buffer, map units, x east, y south, z up), so the preview draws models: the map's objects,
  // what's placed, the ghost at the pointer and the place list's pictures. No pictures: each draws in its kind's colour.
  let fakeMapModelsMade = null;
  function fakeMapModels() {
    if (fakeMapModelsMade) return fakeMapModelsMade;
    // convex solids in the scene's axes (x east, y up, z south) as triangles, each turned to face outwards
    const box = (w, h, d, y0 = 0, x = 0, z = 0) => {
      const c = [];
      for (const X of [x - w / 2, x + w / 2]) for (const Y of [y0, y0 + h]) for (const Z of [z - d / 2, z + d / 2]) c.push([X, Y, Z]);
      return [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
        .flatMap(([a, b, e, f]) => [[c[a], c[b], c[e]], [c[a], c[e], c[f]]]);
    };
    const peak = (w, h, d, y0) => {  // a roof: four slopes to a ridge point
      const top = [0, y0 + h, 0], k = [[-w / 2, -d / 2], [w / 2, -d / 2], [w / 2, d / 2], [-w / 2, d / 2]].map(([X, Z]) => [X, y0, Z]);
      return k.map((p, i) => [p, k[(i + 1) % 4], top]).concat([[k[0], k[1], k[2]], [k[0], k[2], k[3]]]);
    };
    const cone = (r, h, y0, n = 9) => {
      const top = [0, y0 + h, 0], base = [0, y0, 0], ring = [];
      for (let i = 0; i < n; i++) ring.push([r * Math.cos(2 * Math.PI * i / n), y0, r * Math.sin(2 * Math.PI * i / n)]);
      return ring.flatMap((p, i) => [[p, ring[(i + 1) % n], top], [p, base, ring[(i + 1) % n]]]);
    };
    const outward = (tris) => {
      const m = [0, 1, 2].map((k) => tris.reduce((s, t) => s + t[0][k] + t[1][k] + t[2][k], 0) / (3 * tris.length));
      return tris.map(([a, b, c]) => {
        const u = [0, 1, 2].map((k) => b[k] - a[k]), v = [0, 1, 2].map((k) => c[k] - a[k]);
        let n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]];
        const len = Math.hypot(...n) || 1, f = [0, 1, 2].map((k) => (a[k] + b[k] + c[k]) / 3 - m[k]);
        n = n.map((x) => x / len);
        return n[0] * f[0] + n[1] * f[1] + n[2] * f[2] < 0 ? [a, c, b, n.map((x) => -x)] : [a, b, c, n];
      });
    };
    const shapes = [
      [box(5200, 2600, 3600), peak(5600, 1600, 4000, 2600)],                           // the town hall
      [box(2400, 4200, 2400), peak(2700, 1300, 2700, 4200)],                           // the tall town house
      [box(1100, 300, 600, 350), box(160, 500, 700, 0, -380), box(160, 500, 700, 0, 380)],  // the cart
      [box(280, 1400, 280), cone(1500, 3600, 1100)],                                   // the oak
      [box(420, 380, 420), box(460, 60, 460, 380)],                                    // the basket
    ].map((solids) => solids.flatMap(outward));
    const sizes = shapes.map((t) => 3 * t.length);
    const total = sizes.reduce((s, n) => s + n * (12 + 4 + 8 + 4), 0);
    const buf = new ArrayBuffer(total), models = {};
    let at = 0;
    shapes.forEach((tris, t) => {
      const n = sizes[t], part = { texture: null, vertices: n, triangles: tris.length };
      const pos = new Float32Array(buf, (part.positions = at), 3 * n);
      const nrm = new Int8Array(buf, (part.normals = at += 12 * n), 4 * n);
      part.uvs = at += 4 * n;
      const idx = new Uint32Array(buf, (part.indices = at += 8 * n), n);
      at += 4 * n;
      tris.forEach(([a, b, c, nn], i) => [a, b, c].forEach((p, j) => {
        const v = 3 * i + j;
        pos.set([p[0], p[2], p[1]], 3 * v);  // the game's axes: x east, y south, z up
        nrm.set([Math.round(nn[0] * 127), Math.round(nn[2] * 127), Math.round(nn[1] * 127), 0], 4 * v);
        idx[v] = v;
      }));
      models[t] = [part];
    });
    fakeMapModelsMade = { base: "", index: { bin: URL.createObjectURL(new Blob([buf])), models, textures: {} } };
    return fakeMapModelsMade;
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
  // Duplicate map's start: as it is, Blank Terrain, Blank Ocean (words.toml dup_start_*)
  Object.assign(words.us, {"dup_start": "Start from", "dup_start_copy": "As it is", "dup_start_copy_what": "A full copy, with the changes made to {map} so far.", "dup_start_blank_terrain": "Blank Terrain", "dup_start_blank_terrain_what": "Flat land with no water and nothing on it: only the starting points. Add roads, buildings and the rest yourself.", "dup_start_blank_ocean": "Blank Ocean", "dup_start_blank_ocean_what": "The sea over the whole map, flat ground under it and nothing on it: only the starting points. Units go under the water, as on a navy map. That part isn't tested in the game yet.", "dup_start_blank_ocean_warn": "Warning: separate islands aren't ready for full-scale battles. When a land unit is ordered onto an island it can't reach (the computer's units too), the game crashes. Join the islands with land or an underwater road.", "dup_start_battles_only": "Blank Terrain and Blank Ocean start from a Battles map."});
  // New map from scratch (words.toml new_map_scratch, tip_new_map_scratch, scratch_what, dup_scratch_*, dup_base*)
  Object.assign(words.us, {"new_map_scratch": "New map: start from scratch…", "tip_new_map_scratch": "Make a new map that starts blank: flat land or open sea, with only the starting points. You pick which game map it's built on.", "scratch_what": "Blank Terrain or Blank Ocean, with nothing on it but the starting points.", "dup_scratch_title": "New map from scratch", "dup_scratch_lead": "Want to start from scratch? Pick Blank Terrain or Blank Ocean below. Every new map sits on one of the game's maps, because the game can't load a map made from nothing: that map gives yours its size, its player count and its starting points, and nothing else. Pick which one under Built on.", "dup_base": "Built on", "dup_base_what": "Only its size, its player count and its starting points are kept.", "dup_scratch_go": "Make the map", "dup_done_blank": "{name}: a new map, {start} built on {map}. Change it like any map; Test in game plays it."});
  // Duplicate map (words.toml duplicate_map, dup_*, map_copy_of)
  Object.assign(words.us, {"duplicate_map": "Duplicate map", "tip_duplicate_map": "Make a new map from this one: a full copy with a name of its own, as a Battles map, an Operation or a campaign chapter. You then change the copy like any map.", "dup_lead": "Makes a new map: a full copy of {map} with a name of its own, in the game's menus next to the original. Everything you change on the copy (ground, buildings, roads, starting points, players) is the copy's alone: {map} stays as it is.", "dup_how": "How it works", "dup_how_own": "The copy gets its own map file, its own place in the game's menus and its name in every language. Its ids come from its name, so every PC with your map changes gets the very same map, and players who have it can play it together online.", "dup_how_edits": "Your changes to {map} so far come along, so the copy starts as you see it now.", "dup_how_where": "It's saved in your map changes ({folder}); Test in game and Export… take it along like any other change. Ranked games don't offer it.", "dup_how_new": "No map changes is picked, so a new one is made for it, named after it; Test in game and Export… take it along like any other change. Ranked games don't offer it.", "dup_how_tested": "New in this version and still early: tried in the game with 101 new maps at once, each listed and playing its own ground.", "dup_name": "Name in the menus", "dup_file": "Its files and folder: {file}", "dup_long": "Names over 35 characters get cut off in the game's menus.", "dup_entry": "Which one to copy", "dup_go": "Duplicate", "dup_done": "{name}: a new map, a copy of {map}. Change it like any map; Test in game plays it.", "map_copy_of": "new map · copy of {map}"});
  // a new unit's own model (words.toml model_*, tip_model_*)
  Object.assign(words.us, {"model_title": "Its own model", "model_none": "The Studio can't find the 3D model of the unit this one copies, so it can't give this unit a model of its own here (a new model is fitted to the copied one). Everything else on this page still works. To change the model, make the new unit from another unit, and please tell us this unit's name so we can fix it.", "model_how":"It uses the model of the unit it copies. Import a 3D model (.3ds, or .glb from Blender and most 3D tools) to give it one of its own: it's fitted to that unit's length (times Size), its turret on that unit's turret, and turns and drives the same way.", "model_import": "Import model…", "model_import_again": "Import another…", "tip_model_import": "Pick a .3ds (with its pictures beside it, or in the folder above) or a .glb. It's fitted to the copied unit and saved in your mod; Test in game shows it.", "model_size": "Size", "tip_model_size": "Its length over the copied unit's: 1 is as long; an M1 Abrams over a Sherman is 1.36.", "model_importing": "Fitting the model to the unit…", "model_done": "{file} is now this unit's model. Click Test in game to see it.", "model_own": "From {file}: {points} points, {triangles} triangles.", "model_turret": "Turning with the turret: {parts}. The rest moves with the hull.", "model_missing": "Pictures not found: {names}. Those parts show one flat colour. Put the pictures beside the model (or the folder above it) and import it again.", "model_remove": "Use the copied unit's model", "tip_model_remove": "Take its own model out of the mod: it looks like the unit it copies again."});
  // the Units tab's two ways in (words.toml start_*, pick_unit_new, tip_start_from, new_unit_next, model_want*)
  Object.assign(words.us, {"start_change": "Change a unit", "tip_start_change": "Pick a unit to change its values, or open it in Blender to repaint it.", "start_new": "New unit (import a model)", "tip_start_new": "Start a new unit from a game unit: it copies its values and moves the same way. Then import your own 3D model and change the rest.", "start_new_help": "Pick the unit to start from: your new unit copies its values, and your model turns and drives the way its model does. Tested with tanks so far.", "pick_unit_new": "Pick the unit your new one starts from, on the left.", "tip_start_from": "Start a new unit from this one.", "new_unit_next": "Your new unit starts as a copy of {name}. Give it a name, a price and a build menu, then Create: its page opens at Import model.", "model_want": "A model of your own goes on a new unit: make one from this unit, then Import model on its page. This unit stays as it is.", "model_want_button": "New unit from this one…", "tip_model_want": "Opens New unit on this page: a name, a price and a build menu. The new unit's page has Import model."});
  // the Economy tab (words.toml economy_*, tip_tab_economy, tip_economy_reset)
  Object.assign(words.us, {
    economy_help: "A change here is saved in the current mod at once. The game keeps these values twice, once for its usual modes and once for the Nuclear mode: where the two differ, each has its own boxes (Normal and Nuclear); elsewhere one change sets both. Hover a value's name, or read the line under it, for what it does. LittleGroove's RUSE Mod Manager had it first. Tried in the game: the starting money and the ruse cards at the start; the rest not yet.",
    economy_buildings: "Supply depots and administration buildings are buildings: change their price, build time and strength on the Units tab, under Buildings.",
    economy_none: "The game index has none of the economy's values. Build it again in Settings.",
    economy_normal: "Normal", economy_nuclear: "Nuclear",
    tip_economy_normal: "The value in the game's usual modes. The Nuclear mode has its own, in the boxes below.",
    tip_economy_nuclear: "The value in the Nuclear mode only. The game keeps it apart from its usual modes' value.",
    tip_economy_reset_one: "Put this mode's value back as the game has it.",
    tip_economy_reset: "Put the value back as the game has it, in every game mode.",
    economy_group_money: "Money and income", economy_group_supply: "Supply depots", economy_group_production: "Production",
    economy_group_cards: "Ruse cards", economy_group_computer: "Computer players", economy_group_decoys: "Decoys" });
  Object.assign(words.fr, { economy_group_money: "Argent et revenus",
    economy_group_supply: "Dépôts de ravitaillement", economy_group_cards: "Cartes de ruse",
    economy_normal: "Normal", economy_nuclear: "Nucléaire" });
  Object.assign(words.sc, { economy_group_money: "资金与收入",
    economy_group_supply: "补给站", economy_group_cards: "计谋卡", economy_normal: "普通", economy_nuclear: "核战争" });
  // the Nations tab (words.toml nations_*, tip_tab_nations, tip_nations_*)
  Object.assign(words.us, { nations_tab: "Nations", tip_tab_nations: "Give one of the game's seven nations a new name and flag: China in Italy's place, say.", nations_title: "Nations", nations_help: "Give one of the game's seven nations a new name and flag, to make it another nation: China in Italy's place, say. The game keeps seven nations: the one you change keeps its place in the lobby, its build menus, and its campaign chapters and Operations. Its units are changed on the Units tab, and what they say on each unit's page. Seen in the game: the new name in the lobby, the new flag in a match.", nations_lobby_note: "The lobby's own nation button draws its flags inside the game's menu file, so it shows the game's flag for now. The new flag shows beside the players' names in a match (seen in the game); on the loading screen and in replays it isn't seen yet.", nations_flag_of: "{nation}'s flag", nations_was: "(was {nation})", nations_units_count: "{n} units and buildings", nations_change: "Change…", nations_close: "Close", tip_nations_change: "Give {nation} a new name and flag.", nations_name_head: "Name in the lobby", tip_nations_name_head: "What the lobby's nation list calls it, in every language.", nations_name_help: "What the lobby's nation list calls it. A language left as it is keeps the game's name.", nations_army_head: "Army name", tip_nations_army_head: "Its army's name where an Operation asks which army to take.", nations_army_help: "Its army's name where an Operation asks which army to take.", nations_flag_head: "Flag", tip_nations_flag_head: "The small round flag the game shows for this nation.", nations_flag_help: "Choose any picture of the flag, or drop one here: it's fitted to the game's flag, and the round shape stays the game's.", nations_flag_game: "The game's", nations_flag_mine: "Yours", nations_shine: "Shine like the game's flags", tip_nations_shine: "Light the top half and shade the bottom half, as the game's own flags are.", nations_flag_pick: "Choose a picture…", tip_nations_flag_pick: "Pick a picture of the new flag: PNG, JPG or any picture.", nations_flag_back: "Game's flag", tip_nations_flag_back: "Take your flag out: the game's comes back.", nations_flag_backed: "{nation} has the game's flag again.", nations_flag_none: "The Studio can't read this nation's flag in the game's files.", nations_flag_unreadable: "That picture couldn't be read. Try a PNG or JPG.", nations_flag_saved: "{nation}'s new flag is in your mod. Click Test in game to see it.", nations_units_head: "Units and what they say", nations_units_help: "Its units are changed on the Units tab: New unit… puts a copy of any unit in its build menus. What a unit says is on its page, under Voice.", nations_units: "{nation}'s units", tip_nations_units: "Open the Units tab with this nation picked.", nations_reset: "Put it all back", tip_nations_reset: "Give this nation back the game's name, army name and flag.", nations_reset_done: "{nation} is the game's again." });
  // era units in the Units tab (words.toml era_*, eras_*, tip_era_*, tip_eras_*)
  Object.assign(words.us, {"eras_note": "These are all the free (CC0 and CC BY) models we could include. There are plenty more out there, and you can add your own with Import model.", "eras_not_downloaded": "The {era} units aren't on this PC yet: {n} units, {size} to download.", "eras_download": "Download the {era} units", "tip_eras_download": "Downloads this era's units (their models and pictures) from RUSE 2.0's GitHub. Every file is checked before it's used. Once they're here, they update themselves when new ones come out.", "eras_downloading": "Downloading: {done} of {total}…", "eras_unpacking": "Unpacking…", "eras_download_done": "The {era} units are ready.", "eras_updating": "Updating the {era} units: newer ones are out…", "eras_none_yet": "No {era} units are out yet: they come as they're finished.", "eras_no_list": "The list of era units couldn't be loaded ({why}).", "eras_era_ww1": "WWI", "eras_era_ww2": "WWII+", "eras_era_cold": "Cold War", "eras_era_modern": "Modern", "eras_nation_usa": "USA", "eras_nation_germany": "Germany", "eras_nation_uk": "United Kingdom", "eras_nation_france": "France", "eras_nation_italy": "Italy", "eras_nation_ussr": "USSR", "eras_nation_russia": "Russia", "eras_nation_japan": "Japan", "eras_nation_china": "China", "tip_eras_nation": "The nation whose build menu the unit goes in.", "tip_eras_factory": "The build menu (building) the unit goes in.", "eras_model_by": "Model by {author} ({licence}):", "tip_eras_credit": "The model's page, where its maker shared it.", "eras_in_place_of": "in place of {name}", "eras_game_model": "No model yet: it shows the copied unit's model.", "eras_no_fit": "The importer can't fit this kind of unit yet (towed guns): it shows the copied unit's model for now.", "eras_added": "{name} is in your mod.", "eras_removed": "{name} is out of your mod.", "era_vanilla": "Vanilla", "tip_era_chip": "Vanilla: the game's own units. WWI, WWII+, Cold War, Modern: RUSE 2.0's units for that era, each with another maker's free 3D model; add any of them to your mod.", "eras_in_mod_badge": "in your mod", "eras_start_from": "Start from", "tip_eras_start_from": "The game unit whose values it starts with: speed, armour, weapons, how it plays. Any unit of its kind; the first is the suggested one.", "eras_start_help": "It starts with that unit's values. Once it's in your mod, change any of them on its page, like any unit.", "eras_suggested": "Suggested", "eras_start_same": "Same type", "eras_start_other": "Other units", "eras_add": "Add to my mod", "tip_eras_add": "Makes it a new unit of your mod: its model, its maker's credit, the values of the unit it starts from, in the build menu picked.", "tip_eras_name": "Its name in the game, in every language.", "tip_eras_price": "What it costs to build, at every battle date.", "eras_in_mod_as": "It's in your mod: change its values, model and card on its page, like any unit.", "eras_open_page": "Open its page", "tip_eras_open_page": "Its page in your mod, where every value can be changed.", "eras_take_out": "Take it out of my mod", "tip_eras_take_out": "Deletes its unit from your mod, with every change made to it, its model and its credit."});
  // an era unit's size and the unit it's researched from (words.toml eras_size*, eras_research_*, tip_eras_size,
  // tip_eras_research_*)
  Object.assign(words.us, {"eras_size": "Size", "tip_eras_size": "How big its model is: 1 is as long as the unit it starts from. The suggestion gives it its real size beside the game's own units (its real width; a plane's, its wingspan).", "eras_size_help": "1 = as long as the start unit; the suggestion is its real size.", "eras_size_real_width": "Suggested: its real width, {m} m.", "eras_size_real_span": "Suggested: its real wingspan, {m} m.", "eras_size_clamped": "Its real size would need {raw}, but sizes go from 0.05 to 20: {size} is the nearest.", "eras_size_unknown": "Its real size isn't in the library yet, so 1: as long as the start unit.", "eras_size_unread": "Its real size couldn't be worked out, so 1: as long as the start unit.", "eras_research_from": "Researched from", "tip_eras_research_from": "The unit it's researched from: it can be built only after that research (a unit in the same nation's build menu; your mod's new units too). None: buyable from the start. Change it later in its page's Upgrade and research box.", "eras_research_none": "None: buyable from the start", "eras_research_why_start": "Suggested: the unit it starts from.", "eras_research_why_in_place_of": "Suggested: the unit it stands in for.", "eras_research_why_dearest": "Suggested: the dearest unit of this build menu, so an advanced unit comes after research.", "eras_research_price": "Research price", "tip_eras_research_price": "What its research costs.", "eras_research_time": "Research time", "tip_eras_research_time": "How long its research takes, in the seconds or minutes picked beside it (50 seconds to start, as in the Upgrade and research box; that the game counts seconds isn't timed in the game yet).", "tip_eras_research_locked": "Nothing to research: it's buyable from the start. Pick a unit it's researched from first.", "tip_eras_research_off": "Units of this kind have no research in the game's files."});
  // research: what taking out a unit others are researched from does, seconds or minutes (words.toml research_*, set_research_*, upgrade_parent_gone, upgrade_gone_option, check_open_unit)
  Object.assign(words.us, {"set_research_title": "Research", "set_research_help": "What happens to the units researched from a unit you take out of your mod, and whether research times are typed in seconds or minutes.", "research_gone_label": "When you take out a unit that others are researched from:", "tip_research_gone": "What the Studio does when you delete a unit of your mod (or take an era unit out) while other units are researched from it.", "research_gone_warn": "Warn me first", "research_gone_refuse": "Refuse", "research_gone_relink": "Re-link them", "tip_research_gone_warn": "The Studio asks first. If you go ahead, the units researched from it are left researched from a unit that's gone: the check bar lists them, and the game can't be tested until each gets another unit, or none, in its Upgrade and research box.", "tip_research_gone_refuse": "The unit stays in your mod while any unit is researched from it: pick another unit for them in their Upgrade and research box first.", "tip_research_gone_relink": "The units researched from it are researched from the unit it was researched from instead, at the same price and time. If it wasn't researched from any, they become buyable from the start.", "research_time_unit": "Research time in", "tip_research_time_unit": "Type research times in seconds or minutes: minutes are turned into whole seconds, the unit the times are kept in (that the game counts them in seconds isn't timed in the game yet).", "research_seconds": "seconds", "research_minutes": "minutes", "research_gone_ask": "Researched from {name}: {names}. If you take it out, they're left researched from a unit that's gone, and the game can't be tested until each gets another unit, or none, in its Upgrade and research box.", "research_gone_anyway": "Take it out anyway", "tip_research_gone_anyway": "Takes it out now. The units researched from it wait for you to pick another unit for them; the check bar lists them.", "research_gone_settings": "Change this in Settings", "tip_research_gone_settings": "Opens Settings, where you choose what taking out such a unit does: warn first, refuse, or re-link them.", "research_relinked": "{name} is now researched from {to}.", "research_relinked_none": "{name} is now buyable from the start.", "research_left": "Researched from a unit that's gone: {names}. Pick another unit for each in its Upgrade and research box (the check bar lists them).", "upgrade_parent_gone": "It's researched from a unit that's no longer in your mod, so the build stops on it. Pick another unit below, or none.", "upgrade_gone_option": "{name} (no longer in your mod)", "check_open_unit": "Open its page", "tip_check_open_unit": "Shows this unit's page, where its Upgrade and research box picks another unit to research it from."});
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
  const depotRules = new Map();  // "all" or a map pack, lower case -> its rule (StudioApi.economy_depots_set)
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
  Object.assign(words.us, { ai_tab: "AI and player settings", ai_title: "AI and player settings",
    tip_tab_ai: "What every player gets (money, income, supply trucks, production limits, ruse cards), and how the computer players play, what they like to build and their ruse cards, for every battle with this mod.",
    ai_help: "A change here is saved in the current mod at once. LittleGroove's RUSE Mod Manager had it first. Tried in the game: a ruse card taken out of the menu, a card moved in it, a card's length and when Easy starts attacking; the rest not yet.",
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
    ai_scripts_help: "The scripts the game runs on its maps: the campaign's chapters, challenges, Operations and its own tests (IA_Common.dat), shown as Python. A big one takes a few seconds to open. Change this script lets you change one in your mod. Shown and compiled with LittleGroove's script tools.",
    ai_scripts_pick: "Pick a script…", ai_scripts_opening: "Opening {name}… (a big script takes a few seconds)",
    ai_scripts_shown: "{name}: {n} lines ({file})", ai_scripts_missing: "This copy of the Studio can't show the scripts: {why}",
    ai_scripts_copy: "Copy", tip_ai_scripts_copy: "Copy the whole script.", ai_scripts_copied: "Script copied.",
    upgrade_title: "Upgrade and research",
    upgrade_help: "The unit this one is an upgrade of, as in the game: heavy infantry of light infantry, the Jackson of the Wolverine. An upgrade is researched for its price and time before it can be built. LittleGroove's RUSE Mod Manager had it first. Not tried in the game yet.",
    upgrade_from: "Upgrade of", upgrade_none: "None: a unit of its own", upgrade_children: "Its upgrades: {names}",
    tip_upgrade_from: "Pick the unit this one is an upgrade of (the same nation's, in the same build menu), or none.",
    tip_upgrade_undo: "Put it back as the game has it." });
  Object.assign(words.fr, { ai_tab: "Réglages de l'IA et des joueurs", ai_title: "Réglages de l'IA et des joueurs", ai_default: "Défaut",
    ai_group_attack: "Attaque", ai_group_money: "Argent", ai_not_in_menu: "Pas dans le menu des ruses" });
  Object.assign(words.sc, { ai_tab: "AI 与玩家设置", ai_title: "AI 与玩家设置", ai_default: "默认", ai_group_attack: "进攻",
    ai_group_money: "资金", ai_not_in_menu: "不在计谋菜单中" });
  // AI and player settings (words.toml ai_intro, play_*, ai_all_*, ai_unlisted, tip_ai_unlisted)
  Object.assign(words.us, {"ai_intro": "First what every player gets in a battle, then the computer players: how they play, what they like to build and their ruse cards.", "play_players_title": "Player settings", "play_ai_title": "Computer players", "ai_all_title": "For every computer player", "ai_all_help": "These hold for every computer player in every battle, whatever its difficulty and profile.", "ai_unlisted": "not set in the game: 0", "tip_ai_unlisted": "The game doesn't set this value for this set, so it counts as 0 here. Give it a number and your mod adds it; Undo takes it out again."});
  Object.assign(words.fr, {"ai_intro": "D'abord ce que reçoit chaque joueur dans une bataille, puis les joueurs ordinateur : comment ils jouent, ce qu'ils aiment construire et leurs cartes de ruse.", "play_players_title": "Réglages des joueurs", "play_ai_title": "Joueurs ordinateur", "ai_all_title": "Pour tous les joueurs ordinateur", "ai_all_help": "Ces valeurs valent pour tous les joueurs ordinateur dans chaque bataille, quels que soient leur difficulté et leur profil.", "ai_unlisted": "non réglée dans le jeu : 0", "tip_ai_unlisted": "Le jeu ne règle pas cette valeur pour ce jeu de valeurs : elle compte donc pour 0 ici. Donnez-lui un nombre et votre mod l'ajoute ; Annuler la retire."});
  Object.assign(words.sc, {"ai_intro": "先是每位玩家在战斗中得到的东西，然后是电脑玩家：他们的打法、喜欢建造的东西和他们的计谋卡。", "play_players_title": "玩家设置", "play_ai_title": "电脑玩家", "ai_all_title": "所有电脑玩家通用", "ai_all_help": "适用于每场战斗中的每个电脑玩家，无论其难度和档案如何。", "ai_unlisted": "游戏中未设置：0", "tip_ai_unlisted": "游戏没有为这一组设置这个数值，所以这里按 0 计算。给它一个数字，你的模组就会加上它；撤销会再把它拿掉。"});
  // the Maps tab's Import model (words.toml asset_*, tip_asset_*)
  Object.assign(words.us, {"asset_import": "Import model…", "tip_asset_import": "Make a 3D model (.glb, .gltf or .3ds) one of your map mod's own rocks, props, plants or trees. It's placed like the game's own; Test in game shows it.", "asset_edit": "Your model…", "tip_asset_edit": "The picked model is one of your own: see or change its size and where it's from, replace its file, or remove it.", "asset_tag": "Yours", "asset_what": "Your own model · {kind}", "asset_kind_rock": "Rock or cliff", "asset_kind_prop": "Prop", "asset_kind_plant": "Bush or plant", "asset_kind_tree": "Tree", "tip_asset_kind_rock": "Stands like the game's rocks: big ones can be cliffs and walls of stone.", "tip_asset_kind_prop": "Stands like the game's props: crates, carts, fences, anything small that isn't a building.", "tip_asset_kind_plant": "Stands like the game's bushes: low plants, drawn close up and thinned out further away.", "tip_asset_kind_tree": "Stands like the game's trees: its see-through pictures (leaves) and the rest (trunk) are kept apart, as the game's are.", "asset_title_new": "Import a model", "asset_title_edit": "Your model {name}", "asset_lead": "The model is saved in your map mod, with smaller versions for the middle and far distances made for it. The game gets it on every map of the mod, placed like its own.", "asset_name": "Name", "asset_name_from_file": "From the file's name", "tip_asset_name": "Letters and digits; spaces and other signs join the words (rock face 01 becomes RockFace01). A name your mod has already is asked about before it's replaced.", "asset_size": "Size", "tip_asset_size": "1 is as the model was made, a unit in the file a metre. Placing it can still make each one bigger or smaller.", "asset_two_sided": "Seen from both sides", "tip_asset_two_sided": "For a model with no back, such as a scanned rock face: its faces show from behind too (twice the triangles).", "asset_credit": "Where it's from", "asset_licence": "Licence", "tip_asset_licence": "A model someone else made can go in a mod under CC0 or CC-BY only. With CC-BY, give its author and where you found it.", "asset_licence_own": "My own model", "asset_licence_free": "CC0 (free for anyone)", "asset_licence_credit": "CC-BY (its author credited)", "asset_source": "Found at", "tip_asset_source": "The web page you took the model from (kept with it in your mod).", "asset_author": "Author", "tip_asset_author": "Who made the model (kept with it in your mod; give it for CC-BY).", "asset_files": "A .glb or .gltf brings its pictures inside it or beside it; a .3ds needs its pictures (PNG, TGA or JPG) in the same folder.", "asset_info": "{file}: {triangles} triangles; middle distance {middle}, far {far}.", "asset_credit_line": "From {source} by {author} ({licence}).", "asset_pick": "Choose the model file…", "asset_pick_again": "Replace with another file…", "tip_asset_pick": "Pick the model file. It's saved in your mod at once, with its middle and far versions; Test in game shows it.", "asset_save": "Save changes", "asset_saved": "Saved. Test in game shows it.", "asset_remove": "Remove this model", "tip_asset_remove": "Its folder goes to the Recycle Bin. Where it's placed, you're asked before those go too.", "asset_remove_sure": "Remove {name} from your mod?", "asset_placed": "Placed on your maps: {n} ({maps}). Remove those too?", "asset_remove_yes": "Remove", "asset_exists": "Your mod already has a model called {name}. Replace it with this file?", "asset_replace": "Replace it", "asset_keep": "Keep it", "asset_importing": "Importing the model and making its middle and far versions…", "asset_done": "{name} is in your mod and picked in the list: click the map to place it. Test in game shows it."});
  Object.assign(words.fr, {"asset_import": "Importer un modèle…", "tip_asset_import": "Faites d'un modèle 3D (.glb, .gltf ou .3ds) un rocher, un objet, une plante ou un arbre de votre mod de carte. Il se place comme ceux du jeu ; Tester en jeu l'affiche.", "asset_edit": "Votre modèle…", "tip_asset_edit": "Le modèle choisi est l'un des vôtres : voyez ou changez sa taille et sa provenance, remplacez son fichier ou retirez-le.", "asset_tag": "À vous", "asset_what": "Votre propre modèle · {kind}", "asset_kind_rock": "Rocher ou falaise", "asset_kind_prop": "Objet", "asset_kind_plant": "Buisson ou plante", "asset_kind_tree": "Arbre", "tip_asset_kind_rock": "Se comporte comme les rochers du jeu : les grands peuvent faire des falaises et des murs de pierre.", "tip_asset_kind_prop": "Se comporte comme les objets du jeu : caisses, charrettes, clôtures, tout ce qui est petit et n'est pas un bâtiment.", "tip_asset_kind_plant": "Se comporte comme les buissons du jeu : plantes basses, détaillées de près et simplifiées plus loin.", "tip_asset_kind_tree": "Se comporte comme les arbres du jeu : ses images transparentes (feuilles) et le reste (tronc) sont séparés, comme ceux du jeu.", "asset_title_new": "Importer un modèle", "asset_title_edit": "Votre modèle {name}", "asset_lead": "Le modèle est enregistré dans votre mod de carte, avec des versions plus légères faites pour la moyenne et la longue distance. Le jeu le reçoit sur chaque carte du mod, placé comme les siens.", "asset_name": "Nom", "asset_name_from_file": "D'après le nom du fichier", "tip_asset_name": "Lettres et chiffres ; espaces et autres signes joignent les mots (rock face 01 devient RockFace01). Un nom que votre mod a déjà est demandé avant d'être remplacé.", "asset_size": "Taille", "tip_asset_size": "1 : tel que le modèle a été fait, une unité du fichier valant un mètre. En le plaçant, chacun peut encore être agrandi ou réduit.", "asset_two_sided": "Visible des deux côtés", "tip_asset_two_sided": "Pour un modèle sans dos, comme une paroi rocheuse scannée : ses faces se voient aussi de derrière (deux fois plus de triangles).", "asset_credit": "Provenance", "asset_licence": "Licence", "tip_asset_licence": "Un modèle fait par quelqu'un d'autre ne peut aller dans un mod que sous CC0 ou CC-BY. Avec CC-BY, indiquez son auteur et où vous l'avez trouvé.", "asset_licence_own": "Mon propre modèle", "asset_licence_free": "CC0 (libre pour tous)", "asset_licence_credit": "CC-BY (auteur crédité)", "asset_source": "Trouvé sur", "tip_asset_source": "La page web d'où vient le modèle (gardée avec lui dans votre mod).", "asset_author": "Auteur", "tip_asset_author": "Qui a fait le modèle (gardé avec lui dans votre mod ; à indiquer pour CC-BY).", "asset_files": "Un .glb ou .gltf a ses images à l'intérieur ou à côté ; un .3ds a besoin de ses images (PNG, TGA ou JPG) dans le même dossier.", "asset_info": "{file} : {triangles} triangles ; moyenne distance {middle}, loin {far}.", "asset_credit_line": "De {source}, par {author} ({licence}).", "asset_pick": "Choisir le fichier du modèle…", "asset_pick_again": "Remplacer par un autre fichier…", "tip_asset_pick": "Choisissez le fichier du modèle. Il est aussitôt enregistré dans votre mod, avec ses versions moyenne et lointaine ; Tester en jeu l'affiche.", "asset_save": "Enregistrer les changements", "asset_saved": "Enregistré. Tester en jeu l'affiche.", "asset_remove": "Retirer ce modèle", "tip_asset_remove": "Son dossier va à la Corbeille. S'il est placé sur des cartes, on vous demande avant de les retirer aussi.", "asset_remove_sure": "Retirer {name} de votre mod ?", "asset_placed": "Placés sur vos cartes : {n} ({maps}). Les retirer aussi ?", "asset_remove_yes": "Retirer", "asset_exists": "Votre mod a déjà un modèle appelé {name}. Le remplacer par ce fichier ?", "asset_replace": "Le remplacer", "asset_keep": "Le garder", "asset_importing": "Import du modèle et création de ses versions moyenne et lointaine…", "asset_done": "{name} est dans votre mod et choisi dans la liste : cliquez sur la carte pour le placer. Tester en jeu l'affiche."});
  Object.assign(words.sc, {"asset_import": "导入模型…", "tip_asset_import": "把一个3D模型（.glb、.gltf或.3ds）变成你地图模组自己的岩石、物件、植物或树木。它像游戏自带的一样放置；游戏内测试即可看到。", "asset_edit": "你的模型…", "tip_asset_edit": "所选模型是你自己的：查看或更改它的大小和来源、替换文件，或将其移除。", "asset_tag": "自制", "asset_what": "你自己的模型 · {kind}", "asset_kind_rock": "岩石或悬崖", "asset_kind_prop": "物件", "asset_kind_plant": "灌木或植物", "asset_kind_tree": "树木", "tip_asset_kind_rock": "像游戏中的岩石一样摆放：大的可以做悬崖和石墙。", "tip_asset_kind_prop": "像游戏中的物件一样摆放：箱子、推车、栅栏等不是建筑的小东西。", "tip_asset_kind_plant": "像游戏中的灌木一样摆放：低矮植物，近处细致，远处简化。", "tip_asset_kind_tree": "像游戏中的树木一样摆放：透明图片（树叶）和其余部分（树干）像游戏的树一样分开。", "asset_title_new": "导入模型", "asset_title_edit": "你的模型 {name}", "asset_lead": "模型保存在你的地图模组中，并为中距离和远距离生成更简化的版本。模组的每张地图都能用它，像游戏自带的一样放置。", "asset_name": "名称", "asset_name_from_file": "取自文件名", "tip_asset_name": "字母和数字；空格和其他符号会把单词连起来（rock face 01 变成 RockFace01）。如果模组里已有同名模型，替换前会先询问。", "asset_size": "大小", "tip_asset_size": "1 表示按模型原样，文件中1个单位为1米。放置时每一个仍可放大或缩小。", "asset_two_sided": "双面可见", "tip_asset_two_sided": "适用于没有背面的模型，例如扫描的岩壁：从背后也能看到它的面（三角形数量翻倍）。", "asset_credit": "来源", "asset_licence": "许可", "tip_asset_licence": "别人制作的模型只有在 CC0 或 CC-BY 许可下才能放进模组。若为 CC-BY，请填写作者和获取地址。", "asset_licence_own": "我自己的模型", "asset_licence_free": "CC0（任何人可自由使用）", "asset_licence_credit": "CC-BY（需署名作者）", "asset_source": "获取地址", "tip_asset_source": "你获取该模型的网页（与模型一起保存在模组中）。", "asset_author": "作者", "tip_asset_author": "模型的制作者（与模型一起保存在模组中；CC-BY 必须填写）。", "asset_files": ".glb 或 .gltf 的图片在文件内或旁边；.3ds 需要它的图片（PNG、TGA 或 JPG）在同一文件夹中。", "asset_info": "{file}：{triangles} 个三角形；中距离 {middle}，远距离 {far}。", "asset_credit_line": "来自 {source}，作者 {author}（{licence}）。", "asset_pick": "选择模型文件…", "asset_pick_again": "换成另一个文件…", "tip_asset_pick": "选择模型文件。它会立即连同中、远距离版本保存到你的模组中；游戏内测试即可看到。", "asset_save": "保存更改", "asset_saved": "已保存。游戏内测试即可看到。", "asset_remove": "移除此模型", "tip_asset_remove": "它的文件夹会移到回收站。如果已放置在地图上，移除那些之前会先询问。", "asset_remove_sure": "要从模组中移除 {name} 吗？", "asset_placed": "已放置在你的地图上：{n}（{maps}）。也一起移除吗？", "asset_remove_yes": "移除", "asset_exists": "你的模组中已有名为 {name} 的模型。用这个文件替换它吗？", "asset_replace": "替换", "asset_keep": "保留", "asset_importing": "正在导入模型并生成中、远距离版本…", "asset_done": "{name} 已加入你的模组并在列表中选中：点击地图即可放置。游戏内测试即可看到。"});
  // a building's look on its Units page (words.toml building_*, tip_building_*)
  Object.assign(words.us, {"building_look_working": "Reading the building's look…", "building_look_title": "Look", "building_card_title": "Its picture in the build menu", "building_card_how": "Choose any picture (PNG or JPG): it's fitted to the menu's size, cut at the edges if it has to be. Test in game shows it in the build menu.", "building_model_title": "Its own 3D model", "building_model_want": "A model of your own goes on a new building: make one from this building, then Import model on its page. This building stays as it is.", "building_model_how": "A building's look is a layout of pieces: a main hall, hangars, trucks, walls. Your model takes the place of the piece you pick, sized to it and standing where it stands; the rest of the look stays. Its +x side (in Blender) faces the gate units come out of.", "building_piece": "In place of", "tip_building_piece": "The pieces of the look this building copies, biggest on the ground first: for a factory or a headquarters the first is its main building.", "building_piece_row": "{name}: {w} × {d} m, {h} m high (×{n})", "tip_building_size": "1 is as big as the piece it takes the place of (its longer side on the ground).", "tip_building_import": "Pick a .glb, .gltf or .3ds. It's saved in your mod with its middle and far versions; Test in game shows the building with it.", "building_importing": "Importing the building's model and making its middle and far versions…", "building_done": "The building has its own model now. Click Test in game to see it.", "building_own": "{file}: {triangles} triangles; middle distance {middle}, far {far}.", "tip_building_save": "Keep the size and where the model is from as set here (its model stays).", "building_remove": "Use the copied look", "tip_building_remove": "Its model goes to the Recycle Bin: the building looks like the one it copies again.", "building_removed": "The building looks like the one it copies again.", "building_no_pieces": "The Studio found no 3D pieces in this look to take the place of. Please tell us this building's name so we can fix it."});
  Object.assign(words.fr, {"building_look_working": "Lecture de l'apparence du bâtiment…", "building_look_title": "Apparence", "building_card_title": "Son image dans le menu de construction", "building_card_how": "Choisissez n'importe quelle image (PNG ou JPG) : elle est ajustée à la taille du menu, rognée sur les bords si besoin. Tester en jeu l'affiche dans le menu de construction.", "building_model_title": "Son propre modèle 3D", "building_model_want": "Un modèle à vous se met sur un nouveau bâtiment : créez-en un à partir de celui-ci, puis Importer un modèle sur sa page. Ce bâtiment reste tel quel.", "building_model_how": "L'apparence d'un bâtiment est un agencement de pièces : un bâtiment principal, des hangars, des camions, des murs. Votre modèle prend la place de la pièce choisie, à sa taille et à sa place ; le reste de l'apparence reste. Son côté +x (dans Blender) fait face à la sortie des unités.", "building_piece": "À la place de", "tip_building_piece": "Les pièces de l'apparence que ce bâtiment copie, la plus grande au sol d'abord : pour une usine ou un QG, la première est son bâtiment principal.", "building_piece_row": "{name} : {w} × {d} m, {h} m de haut (×{n})", "tip_building_size": "1 : aussi grand que la pièce remplacée (son plus grand côté au sol).", "tip_building_import": "Choisissez un .glb, .gltf ou .3ds. Il est enregistré dans votre mod avec ses versions moyenne et lointaine ; Tester en jeu montre le bâtiment avec.", "building_importing": "Import du modèle du bâtiment et création de ses versions moyenne et lointaine…", "building_done": "Le bâtiment a maintenant son propre modèle. Cliquez sur Tester en jeu pour le voir.", "building_own": "{file} : {triangles} triangles ; moyenne distance {middle}, loin {far}.", "tip_building_save": "Garder la taille et la provenance du modèle telles qu'indiquées ici (le modèle reste).", "building_remove": "Reprendre l'apparence copiée", "tip_building_remove": "Son modèle va à la Corbeille : le bâtiment ressemble de nouveau à celui qu'il copie.", "building_removed": "Le bâtiment ressemble de nouveau à celui qu'il copie.", "building_no_pieces": "Le Studio n'a trouvé aucune pièce 3D à remplacer dans cette apparence. Merci de nous donner le nom de ce bâtiment pour que nous corrigions cela."});
  Object.assign(words.sc, {"building_look_working": "正在读取建筑外观…", "building_look_title": "外观", "building_card_title": "它在建造菜单中的图片", "building_card_how": "选择任意图片（PNG 或 JPG）：会按菜单大小调整，必要时裁掉边缘。游戏内测试即可在建造菜单中看到。", "building_model_title": "自己的3D模型", "building_model_want": "自己的模型要放在新建筑上：先以此建筑创建一个新建筑，再在其页面上导入模型。此建筑保持不变。", "building_model_how": "建筑的外观是各部件的布置：主楼、机库、卡车、围墙。你的模型会以所选部件的大小、在它的位置上取代它；其余保持不变。模型的 +x 面（在 Blender 中）朝向单位出来的大门。", "building_piece": "取代", "tip_building_piece": "此建筑所复制外观的各部件，占地最大的在前：工厂或司令部的第一个就是主楼。", "building_piece_row": "{name}：{w} × {d} 米，高 {h} 米（×{n}）", "tip_building_size": "1 表示与被取代的部件一样大（其在地面上的长边）。", "tip_building_import": "选择 .glb、.gltf 或 .3ds。它会连同中、远距离版本保存到你的模组中；游戏内测试即可看到带它的建筑。", "building_importing": "正在导入建筑模型并生成中、远距离版本…", "building_done": "该建筑现在有了自己的模型。点击游戏内测试即可查看。", "building_own": "{file}：{triangles} 个三角形；中距离 {middle}，远距离 {far}。", "tip_building_save": "按此处设置保存大小和来源（模型不变）。", "building_remove": "使用复制的外观", "tip_building_remove": "其模型会移到回收站：建筑恢复为所复制建筑的外观。", "building_removed": "建筑已恢复为所复制建筑的外观。", "building_no_pieces": "Studio 在此外观中没有找到可取代的3D部件。请告诉我们这个建筑的名称，以便修复。"});
  // the model's size slider and Solid (10-18)
  Object.assign(words.us, {"tip_asset_size_slide": "Drag to make it smaller (left, down to a tenth) or bigger (right, up to 10 times). Letting go saves it, and the map shows the new size.", "asset_metres": "In the game: about {across} × {deep} m across and {high} m high", "asset_solid": "Solid: units go around it", "tip_asset_solid": "Ticked: wherever it's placed, units drive and walk around it (a circle as wide as the model, times its size), as around a building. Not ticked: as the game's own small rocks, props and trees, units drive through it and knock it over."});
  Object.assign(words.fr, {"tip_asset_size_slide": "Faites glisser pour le rendre plus petit (à gauche, jusqu'au dixième) ou plus grand (à droite, jusqu'à 10 fois). En relâchant, c'est enregistré et la carte montre la nouvelle taille.", "asset_metres": "Dans le jeu : environ {across} × {deep} m au sol et {high} m de haut", "asset_solid": "Solide : les unités le contournent", "tip_asset_solid": "Coché : partout où il est placé, les unités le contournent (un cercle aussi large que le modèle, fois sa taille), comme un bâtiment. Décoché : comme les petits rochers, objets et arbres du jeu, les unités passent au travers et le renversent."});
  Object.assign(words.sc, {"tip_asset_size_slide": "拖动可缩小（向左，最小到十分之一）或放大（向右，最大到 10 倍）。松开即保存，地图会显示新的大小。", "asset_metres": "游戏中：约 {across} × {deep} 米，高 {high} 米", "asset_solid": "实体：单位会绕开它", "tip_asset_solid": "勾选：无论放在哪里，单位都会像绕开建筑一样绕开它（与模型同宽的圆，乘以其大小）。不勾选：与游戏自带的小石头、道具和树木一样，单位会直接穿过并撞倒它。"});
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
  Object.assign(words.us, { ai_bonus_summary: "Game mode: {modes}. Difficulty: {difficulties}. Profile: {profiles}. Then {v} preference for: {units}.",
    ai_bonus_any_mode: "any", ai_bonus_any_difficulty: "any", ai_bonus_any_profile: "any", ai_bonus_any_unit: "every unit",
    ai_battle: "In a battle: {values}", ai_battle_wins: "whatever the difficulty: {list}",
    tip_ai_battle: "What this value comes to in a battle, with your mod's changes. The game takes the profile's value when it isn't Default's, else the difficulty's when it isn't Default's, else Default's; a value a set doesn't list counts as 0.",
    tip_ai_choice: "Pick it by name; the number in brackets is the one the game uses.",
    ai_sure_name: "Its meaning is read from its name and the game's values; not yet seen in the game's workings.",
    unit_min: "min", number_full_speed: "full speed in about {s} s", number_full_stop: "stops from full speed in about {s} s" });
  const AI_BONUS_ROWS = [["BonusValue", "Extra preference for these units", "int32", 400],
    ["UnitIDs", "Units (by number)", "int32", [3008, 3009]], ["WarModes", "Game modes (by number)", "int32", [4]],
    ["AIDifficulties", "Difficulties (by number)", "int32", [0, 1, 2]],
    ["AIProfiles", "Profiles (by number)", "int32", [0, 1, 2, 3, 4, 5, 6]]];
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
    if (address === AI_BONUS) return AI_BONUS_ROWS.find((r) => r[0] === prop);
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
    const cls = address === AI_BONUS ? "TAISpecificBonus" : AI_CARDS.some((c) => c[0] === address)
      ? "TBluffCardDescriptor" : "TIAProfil";
    return { prop, label: lang === "base" ? prop : label, type, list: Array.isArray(game), game, cls,
      value: aiEdits.has(key) ? aiEdits.get(key) : null, same_default: aiSame(address, prop) };
  };
  // what each value comes to in a battle (rusemod.ai.battle_values): each difficulty's (0 when it doesn't list it),
  // and the personalities whose own value isn't Default's
  const aiBattle = () => {
    const out = {};
    const props = new Set(AI.flatMap((s) => s[5].flatMap(([, rows]) => rows.map((r) => r[0]))));
    for (const prop of props) {
      const d = aiNow(AI[0][0], prop);
      out[prop] = { difficulties: AI.filter((s) => s[1] === "difficulty").map((s) => [s[3], aiNow(s[0], prop)]),
        personalities: AI.filter((s) => s[1] === "personality" && aiNow(s[0], prop) !== d).map((s) => [s[3], aiNow(s[0], prop)]) };
    }
    return out;
  };
  const AI_CHOICES = {
    AIDifficulties: [{ n: 0, name: "Easy" }, { n: 1, name: "Medium" }, { n: 2, name: "Hard" }],
    AIProfiles: ["Regular", "Air Force", "Howitzer", "Prototype", "Blitzkrieg", "Turtle", "Random"].map((name, n) => ({ n, name })),
    WarModes: ["1945 era", "1942 era", "1939 era", "Total War mode", "Nuclear mode"].map((name, n) => ({ n, name })),
    UnitIDs: [{ n: 3009, name: "NUCLEAR HOWITZER", nation: "UK" }, { n: 3008, name: "NUCLEAR LONG TOM", nation: "USA" },
      { n: 1001, name: "SHERMAN", nation: "USA" }],
  };
  const aiNames = (prop) => aiNow(AI_BONUS, prop).map((n) => (AI_CHOICES[prop].find((c) => c.n === n) || {}).name || String(n));
  // the All values tab's words (words.toml values_*, tip_values_*)
  Object.assign(words.us, {"values_tab": "All values", "tip_tab_values": "Every value of the game's units and other objects, even the ones the other tabs don't show. For when the other tabs don't have what you want to change.", "values_help": "Every value of the game's unit data, even the ones the other tabs don't show. 1. Pick a file or type a name on the left. 2. Click what you want. 3. Change a value: it's saved in the current mod at once. Hold the mouse over anything to see what it does. LittleGroove's RUSE Mod Manager had it first. Not tried in the game yet.", "values_file_label": "File", "tip_values_file": "Show only the objects of one file of the game's unit data, or of every file. Most units are in everything.cpp.gladndfbin.", "values_file_all": "Every file", "values_find_label": "Name or kind", "values_find_hint": "e.g. Sherman, Ammo, TAmmunition", "tip_values_find": "Type part of a name (Sherman) or of a kind of object (TAmmunition). The list updates as you type.", "values_by_title": "Look for a value", "tip_values_by": "Open this to find objects by a value they hold: every ammunition with a damage of 120, say.", "values_by_help": "Fill one box or both. The value's name is the game's own (Puissance is damage, PorteeMaximale is range).", "values_prop_label": "Value's name", "values_prop_hint": "e.g. Puissance", "tip_values_prop": "Part of the value's name, as the game spells it: Puissance (damage), PorteeMaximale (range), ProductionPrice (price).", "values_value_label": "Holds", "values_value_hint": "e.g. 120, or Sherman", "tip_values_value": "A number, or part of a text or of a linked object's name, that the value holds.", "values_go": "Look", "tip_values_go": "Look again with what's in the boxes (it also looks by itself as you type).", "values_start": "Type a name or pick a file to start.", "values_looking": "Looking…", "values_none": "Nothing found. Try fewer letters, or Every file.", "values_count": "Found: {n}", "values_some": "The first {shown} of {n}: type more to narrow it down.", "tip_values_object": "{kind}, in {file}. Click to see every value it has.", "values_pick": "Click something on the left to see every value it has.", "values_back": "← Back", "tip_values_back": "Go back to what you were looking at before.", "values_part_of": "↑ Part of {name}", "tip_values_part_of": "This is a part of another object: open that one.", "tip_values_copy": "Copy this object's address (its full name in the game's data) to paste it somewhere else.", "values_copied": "Address copied.", "tip_values_code_name": "Its name in the game's data.", "values_meta": "{kind} · {file} · object {n}", "tip_values_meta": "What kind of object this is, which of the game's files it's in, and its number in that file.", "values_why_outside": "This isn't in the game's unit data, so a mod can't change it. You can look, not change.", "values_why_not_stable": "Nothing with a name leads to this object, so a mod can't find it to change it. You can look, not change.", "values_how": "Change a value and press Enter (or click elsewhere): it's saved in the current mod at once. “Game's value” undoes it. Use Test in game to try it.", "values_shared": "{n} objects share this part: a change here changes it for all of them.", "values_users_warn": "{n} other objects use this one: a change here changes it for all of them.", "values_rows": "Its values ({n})", "values_used_by": "Used by ({n})", "tip_values_user": "This object uses the one shown: click to open it.", "values_users_more": "And {n} more.", "values_yes": "Yes", "values_no": "No", "values_link_none": "Nothing (empty)", "values_kind_number": "A number. Type a new one and press Enter: it's saved in the mod at once.", "values_kind_bool": "Yes or no. Tick the box for yes.", "values_kind_text": "A text. Type a new one and press Enter. If it's a file's name, only use a file the game has.", "values_kind_key": "Which of the game's texts is shown here, by its key (like N_UNI_137). The words it shows are under the box. Only type a key the game has.", "values_kind_vector": "Numbers that go together, one per box: a position, a size, a direction, or a colour (red, green, blue, see-through: 0 to 255).", "values_kind_guid": "A unique id. Leave it as it is unless you know why it should change.", "values_kind_numbers": "A list of numbers, with a comma between each (like 20, 20, 20). It may be made longer or shorter.", "values_kind_link": "A link to another object. Type part of a name and pick one from the list, or empty the box for nothing. Open shows the object it links to.", "values_kind_part": "A part of this object (its weapons, its look...). Click to open it and change its values.", "values_kind_written": "Several values together, written the way mod files write them: [ ] around a list, MAP [ ] for pairs. Only change it if you know that way of writing.", "values_kind_fixed": "Raw data: it can't be changed here.", "values_cant_row": "This value can't be changed here.", "tip_values_words": "The words the game shows for this key, in your language.", "values_words_none": "(no words for this key in this language)", "tip_values_swatch": "The colour these numbers make.", "values_items": "Items: {n}", "values_open_part": "Open this part", "tip_values_part": "Open this part to see and change its values.", "values_open": "Open", "tip_values_open": "Open the object this links to.", "values_reset": "Game's value", "tip_values_reset": "Put the value back as the game has it (takes your change out of the mod).", "values_removed": "Taken out by the mod.", "values_game": "The game has: {value}", "values_saved": "Saved in the mod: {name}.", "values_same": "{name} is the game's value again.", "values_open_all": "All values", "tip_values_open_all": "See and change every value this has, even the ones this page doesn't show (the All values tab)."});
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
  Object.assign(words.us, {"mission_open": "Menus, files and texts of this mission…", "tip_mission_open": "See where the game's menus list this mission, check every file the game needs to start it, and change its texts in every language (the files checked with LittleGroove's scenario chain).", "mission_title": "{name}: menus, files and texts", "mission_tab_menu": "In the menus", "tip_mission_tab_menu": "Whether the game lists this mission, where, and its values and texts there.", "mission_tab_files": "Files check", "tip_mission_tab_files": "Every file the game needs to start this mission, from its menu entry to the mission itself, each checked.", "mission_tab_texts": "Texts", "tip_mission_tab_texts": "Every text this mission owns: in the menu, and what its mission script shows during the game.", "mission_loading": "Reading the game's files…", "mission_new_map": "This map is new in your mod. Its missions are checked by Check this map, which builds your mod first.", "mission_unbound": "No menu of the game loads this one: it's a test or an unused setup.", "mission_listed": "The game lists it in {menu}: number {n} of {total}.", "mission_not_listed": "No menu lists this mission, so the game never shows it.", "mission_order_head": "The menu, as the player sees it", "tip_mission_order": "Every entry of this menu, in your mod's order (the game's when your mod gives none), in its groups. This mission is highlighted.", "mission_values_head": "Its values in the menu", "tip_mission_values": "What the game's menu entry for this mission says. Change them with the button below.", "mission_values_change": "Change these values…", "tip_mission_values_change": "Opens this menu entry in the All values tab, where each value is changed and saved in your mod.", "mission_values_cannot": "This menu entry can't be opened in the All values tab.", "mission_menu_texts_head": "Its texts in the menu", "tip_mission_menu_texts": "The name and briefing the player reads in the menu before pressing Start.", "mission_v_NbPlayers": "Players", "mission_v_GameType": "Game type", "mission_v_MapSize": "Map size", "mission_v_GameModeMulti": "Game mode", "mission_v_ChapterId": "Chapter number", "mission_v_CategoryId": "Group in the list", "mission_v_NbSecondaryObjectives": "Secondary objectives", "mission_v_PopCapPlayer": "Unit limit (player)", "mission_v_PopCapIA": "Unit limit (computer)", "mission_v_PrivilegeId": "Privilege number", "mission_t_Description": "Name in the menu", "mission_t_LongDescription": "Briefing", "mission_t_LongDescription1": "Briefing, part 1", "mission_t_LongDescription2": "Briefing, part 2", "mission_t_LongDescription3": "Briefing, part 3", "mission_t_LongDescription4": "Briefing, part 4", "mission_files_ok": "Everything the game needs to start this mission is there.", "mission_files_broken": "{n} missing or not matching: the game can't start this mission as it is.", "mission_files_note": "These are the game's own files. To check them with your mod's changes, use Check this map: it builds your mod first.", "mission_state_ok": "Fine", "mission_state_missing": "Missing", "mission_state_mismatch": "Doesn't match", "mission_state_optional": "Not needed here", "mission_state_unknown": "Can't tell", "mission_why_scenario_file_ok": "The mission's setup file is in the game's map data.", "mission_why_scenario_file_missing": "The mission's setup file isn't in the game's map data.", "mission_why_scenario_cluster_ok": "A loader on this map opens the mission.", "mission_why_scenario_cluster_missing": "Nothing on this map opens the mission, so the game can't load it.", "mission_why_cluster_scenario_ok": "The loader names the mission's setup file.", "mission_why_cluster_scenario_missing": "The loader names no setup file.", "mission_why_script_ok": "The mission script is where the game looks for it.", "mission_why_script_missing": "The mission script isn't where the game looks for it, so it never runs.", "mission_why_script_unknown": "The loader gives the game no place to look for a mission script.", "mission_why_dico_ok": "The mission's texts are there.", "mission_why_dico_missing": "The mission's texts are missing, so they show blank in the game.", "mission_why_optional": "Not needed by this mission: the game's own are the same.", "mission_why_dico_langs_ok": "In {n} languages.", "mission_why_terrain_cluster_ok": "The map's ground is found.", "mission_why_terrain_cluster_missing": "The map's ground isn't found.", "mission_why_terrain_cluster_unknown": "The loader names no ground.", "mission_why_terrain_subcluster_ok": "The ground has the part this mission asks for.", "mission_why_terrain_subcluster_mismatch": "The ground doesn't have the part this mission asks for.", "mission_why_terrain_dat_ok": "The ground names its map data.", "mission_why_terrain_dat_missing": "The ground names no map data.", "mission_why_mapload_ok": "A map slot starts this mission.", "mission_why_mapload_missing": "No map slot starts this mission, so nothing can launch it.", "mission_why_mapload_no_id": "The map slot has no id, so no menu entry can point at it.", "mission_why_cluster_entry_ok": "The map slot finds the part it asks for.", "mission_why_cluster_entry_mismatch": "The map slot asks for a part this mission doesn't have.", "mission_why_registration_ok": "A menu entry points at the map slot.", "mission_why_registration_missing": "No menu entry points at this map slot: it loads, but the menus never show it.", "mission_why_pack_ok": "The menu entry is in one of the menu's lists.", "mission_why_pack_missing": "The menu entry is in no list, so the menu never shows it.", "mission_texts_no_script": "The mission script's texts can't be read in this copy of the Studio (the script viewer is missing a part): only the menu's texts are shown.", "mission_texts_count": "{n} texts. Each one changes in every language at once, and is saved in your mod.", "mission_texts_line": "Mission script, line {line}", "mission_texts_script": "Mission script", "tip_mission_words": "Change these words in every language at once. Saved in your mod.", "mc_mission_link": "Mission {mission}: {why}", "mc_missions_unread": "The map's missions couldn't be checked: {why}"});
  // the start screen, a new mod's steps and the board (startflow.js, board.js)
  Object.assign(words.us, {"board_empty_own_row": "No units in it yet: click + to add some. Only the units put here are made in this building."});
  Object.assign(words.fr, {"board_empty_own_row": "Aucune unité pour l'instant : cliquez sur + pour en ajouter. Seules les unités mises ici sont produites dans ce bâtiment."});
  Object.assign(words.sc, {"board_empty_own_row": "这里还没有单位：点击 + 添加。此建筑只生产放在这里的单位。"});
  // the board's Add a building (board.js)
  Object.assign(words.us, {"board_add_building": "Add a building…", "tip_board_add_building": "Add a new building to {nation}: a copy of one of the game's buildings, making the same units as it or units of its own.", "board_own_left": "Buildings with units of their own: {n} more can be added.", "board_buildings_label": "Buildings:", "tip_board_building_remove": "Take {name} out of the mod.", "board_building_removed": "Took {name} out of the mod.", "board_own_tag": "Units of its own", "tip_board_own_tag": "This building makes only the units in its row, in a tab of its own on the build bar.", "board_building_title": "A new building for {nation}", "board_building_copy": "Copy of", "tip_board_building_copy": "The game's building it starts as a copy of: its look, its price and its place in the build menu.", "board_building_name": "Name", "tip_board_building_name": "The building's name in the game, in every language.", "board_building_same": "Makes the same units as the building it copies", "tip_board_building_same": "It joins that building's row and tab: either one builds those units.", "board_building_own": "Makes units of its own ({n} of 3 left)", "board_building_own_full": "This nation already has 3 buildings with units of their own.", "tip_board_building_own": "A row and a tab of its own on the build bar: put any units in it. A nation can have three.", "board_building_patch": "This one needs the game patch for more buildings. The Studio puts it only into your modded copy's RUSE.exe; the game itself stays as it is.", "board_building_add": "Add building", "tip_board_building_add": "Add the building to the mod, on this nation's board.", "board_building_cancel": "Cancel", "board_building_added": "Added {name}."});
  Object.assign(words.fr, {"board_add_building": "Ajouter un bâtiment…", "tip_board_add_building": "Ajouter un nouveau bâtiment à {nation} : une copie d'un bâtiment du jeu, qui produit les mêmes unités que lui ou ses propres unités.", "board_own_left": "Bâtiments avec leurs propres unités : encore {n} possible(s).", "board_buildings_label": "Bâtiments :", "tip_board_building_remove": "Retirer {name} du mod.", "board_building_removed": "{name} retiré du mod.", "board_own_tag": "Ses propres unités", "tip_board_own_tag": "Ce bâtiment ne produit que les unités de sa ligne, dans son propre onglet de la barre de construction.", "board_building_title": "Un nouveau bâtiment pour {nation}", "board_building_copy": "Copie de", "tip_board_building_copy": "Le bâtiment du jeu dont il est une copie au départ : son apparence, son prix et sa place dans le menu de construction.", "board_building_name": "Nom", "tip_board_building_name": "Le nom du bâtiment dans le jeu, dans toutes les langues.", "board_building_same": "Produit les mêmes unités que le bâtiment copié", "tip_board_building_same": "Il rejoint la ligne et l'onglet de ce bâtiment : l'un ou l'autre produit ces unités.", "board_building_own": "Produit ses propres unités ({n} sur 3 restants)", "board_building_own_full": "Cette nation a déjà 3 bâtiments avec leurs propres unités.", "tip_board_building_own": "Une ligne et un onglet à lui sur la barre de construction : mettez-y n'importe quelles unités. Une nation peut en avoir trois.", "board_building_patch": "Celui-ci a besoin du correctif du jeu pour plus de bâtiments. Le Studio ne l'applique qu'au RUSE.exe de votre copie moddée ; le jeu lui-même reste tel quel.", "board_building_add": "Ajouter le bâtiment", "tip_board_building_add": "Ajouter le bâtiment au mod, dans les bâtiments de cette nation.", "board_building_cancel": "Annuler", "board_building_added": "{name} ajouté."});
  Object.assign(words.sc, {"board_add_building": "添加建筑…", "tip_board_add_building": "为{nation}添加新建筑：游戏中某个建筑的副本，生产与其相同的单位，或生产自己的单位。", "board_own_left": "拥有自己单位的建筑：还可添加 {n} 个。", "board_buildings_label": "建筑：", "tip_board_building_remove": "从模组中移除{name}。", "board_building_removed": "已从模组中移除{name}。", "board_own_tag": "自有单位", "tip_board_own_tag": "此建筑只生产其行中的单位，在建造栏中有自己的标签页。", "board_building_title": "{nation}的新建筑", "board_building_copy": "复制自", "tip_board_building_copy": "作为起点复制的游戏建筑：其外观、价格和在建造菜单中的位置。", "board_building_name": "名称", "tip_board_building_name": "建筑在游戏中的名称，所有语言通用。", "board_building_same": "生产与被复制建筑相同的单位", "tip_board_building_same": "加入该建筑的行和标签页：两者都能生产这些单位。", "board_building_own": "生产自己的单位（还剩 {n}/3）", "board_building_own_full": "该国家已有 3 座拥有自己单位的建筑。", "tip_board_building_own": "在建造栏中有自己的行和标签页：可放入任何单位。每个国家最多三个。", "board_building_patch": "这需要用于更多建筑的游戏补丁。Studio 只会将其应用到你的模组副本的 RUSE.exe 中，游戏本身保持不变。", "board_building_add": "添加建筑", "tip_board_building_add": "将建筑添加到模组中，归入该国家的建筑。", "board_building_cancel": "取消", "board_building_added": "已添加{name}。"});
  Object.assign(words.us, {"board_where": "Built in the {building}: place {n} of {all}.", "board_where_out": "Made by the {building}, but in no build menu now.", "board_show": "Show on the board", "tip_board_show": "Open {nation}'s buildings in the Nations tab, at this unit's building."});
  Object.assign(words.fr, {"board_where": "Construite dans {building} : place {n} sur {all}.", "board_where_out": "Faite par {building}, mais dans aucun menu de construction pour l'instant.", "board_show": "Voir dans les bâtiments", "tip_board_show": "Ouvrir les bâtiments de {nation} dans l'onglet Nations, au bâtiment de cette unité."});
  Object.assign(words.sc, {"board_where": "在{building}中建造：第 {n} 个，共 {all} 个。", "board_where_out": "由{building}建造，但现在不在任何建造菜单中。", "board_show": "在建筑中显示", "tip_board_show": "在“国家”标签页打开{nation}的建筑，定位到该单位的建筑。"});
  Object.assign(words.us, {"ss_title": "What would you like to do?", "ss_carry": "Carry on with a mod", "tip_ss_carry": "Open one of your mods: the Studio opens on it, as you left it.", "ss_new": "Start a new mod", "tip_ss_new": "Name it, choose what each nation keeps, set up its buildings and research. Every step can be skipped.", "ss_skip": "Skip", "tip_ss_skip": "Go straight to the Studio, with all its tabs.", "ss_always": "Always skip this screen (I'm an experienced modder)", "tip_ss_always": "Ticked, the Studio opens straight on its tabs. Settings > Start screen brings this screen back.", "ss_carry_head": "Your mods", "ss_open": "Open", "tip_ss_open": "Open {name} in the Studio.", "ss_changed": "Last changed {when}", "ss_back": "Back", "tip_ss_back": "Back to the three choices.", "set_start_title": "Start screen", "set_start_help": "The screen the Studio opens on: carry on with a mod, start a new one, or skip it.", "set_start_show": "Show the start screen when the Studio opens", "tip_set_start_show": "Unticked, the Studio opens straight on its tabs, as the start screen's Always skip does.", "set_start_open": "Open the start screen now", "tip_set_start_open": "Show the start screen: carry on with a mod, or start a new one.", "flow_bar": "New mod, step {n} of {all}: {step}", "flow_step_name": "Name", "flow_step_nations": "Nations", "flow_step_research": "Research", "flow_step_board": "Buildings", "flow_step_change": "What else", "flow_step_done": "Done", "flow_back": "Back", "tip_flow_back": "The step before this one.", "flow_next": "Next", "tip_flow_next": "Keep what this step set and go on to the next one.", "flow_finish": "Finish", "tip_flow_finish": "Finish the steps and go to the Studio.", "flow_studio": "Go to the Studio now", "tip_flow_studio": "Leave the steps: everything set so far is saved in your mod.", "flow_name_head": "What's your mod called?", "flow_name_help": "The name players see in the Launcher.", "flow_name_placeholder": "My mod", "tip_flow_name": "Your mod's name. Press Enter or Next to make it.", "flow_name_needed": "Give your mod a name first.", "flow_made": "{name} is made: everything from here on is saved in it.", "flow_name_made": "{name} is made. Go on with Next.", "flow_help_nations": "For each nation: Keep its units (its build menus as in the game) or Start it empty (you fill its buildings on the Buildings step). Change gives it a new name and flag.", "flow_keep": "Keep its units", "tip_flow_keep": "{nation}'s build menus stay as they are in the game.", "flow_empty": "Start it empty", "tip_flow_empty": "Take all of {nation}'s units out of its build menus, at every battle date. Its HQ, factories and depots stay; you fill its buildings on the Buildings step.", "flow_research_head": "Research", "flow_research_help": "How units are unlocked in your mod.", "flow_research_keep": "Keep the game's research", "flow_research_keep_help": "Units are researched as in the game.", "flow_research_none": "No research", "flow_research_none_help": "Every unit can be built from the start: nothing is researched.", "flow_research_custom": "Custom", "flow_research_custom_help": "Starts with the game's research. On the next step, put any unit under the one it's researched from, however you like.", "flow_research_none_done": "No research: {n} units can be built from the start now.", "flow_research_reset_done": "The game's research is back.", "flow_board_head": "Buildings", "flow_board_help": "Pick a nation. Each row is one of its buildings with its build menu, in the game's order: + adds a unit, drag a unit to move it, Research… puts it under the unit it's researched from.", "flow_board_help_custom": "Pick a nation. To change research: Research… on a unit, then click the unit it comes after, in any of the nation's buildings. + adds a unit, drag a unit to move it.", "tip_flow_board_nation": "Show {nation}'s buildings.", "flow_change_head": "What will your mod change?", "flow_change_help": "Tick what you want to change next: each one opens as its own tab, with Next above it to go on. Leave them all unticked to finish now.", "flow_change_units": "Units' values", "tip_flow_change_units": "Health, weapons, speed, price… of each unit (the Units tab).", "flow_change_ai": "AI and player settings", "tip_flow_change_ai": "Starting money, income, supply depots, and how the computer players play and what they build (the AI and player settings tab).", "flow_change_music": "Music and sounds", "tip_flow_change_music": "The game's songs, replaced, or new ones added (the Music tab).", "flow_change_values": "Any other value", "tip_flow_change_values": "Every value of the game's files, found by name (the All values tab).", "flow_help_units": "Pick a unit on the left and change its values. Next when you're done.", "flow_help_ai": "Change the money, income and depots, and how the computer players play. Next when you're done.", "flow_help_music": "Replace a song or add one. Next when you're done.", "flow_help_values": "Search for any value and change it. Next when you're done.", "flow_done_head": "{name} is ready", "flow_done_help": "Test it in the game, or keep changing it in any tab. The start screen's Carry on with a mod opens it again.", "flow_done_test": "Test in game", "tip_flow_done_test": "Build your mod into the modded copy and start the game from it.", "board_head": "Buildings and units", "tip_board_head": "Each of this nation's buildings with the units its build menu offers.", "board_help": "Each row is one of {nation}'s buildings with its build menu, in the game's order. + adds a unit; drag a unit along its row, or to another building; × takes it out; Research… puts it under the unit it's researched from.", "board_loading": "Reading the build menus…", "board_no_mod": "Pick or make a mod first: the board's changes are saved in it.", "board_count": "Units: {n}", "board_untried": "More than 10: not tried in the game yet", "tip_board_untried": "The game's own buildings use up to {n} places. More is allowed; how the game's menu shows them hasn't been tried yet.", "tip_board_add": "Add a unit to {nation}'s {building}: one of its own, a copy of another nation's, or an era unit.", "board_empty_row": "Nothing to build here. In the game, this building then shows the HQ's building list when it's picked. Click + to add a unit.", "board_dates_from": "From {year}", "board_dates_no_nuclear": "Not in Nuclear", "board_dates_nuclear_only": "Nuclear only", "board_dates_none": "In no battle", "tip_board_dates": "The battles whose build menu shows it, as in the game. In Total War it arrives when the battle reaches that year.", "board_new": "Yours", "tip_board_new": "A unit made in your mod.", "board_mix_short": "Not tried", "board_mix": "Not tried in the game yet: a plane in a ground building, or a vehicle at the Airfield.", "board_from_other": "Researched from {name} ({building})", "tip_board_from_other": "Researched from a unit of another building: not tried in the game yet. The unit it's researched from stays buildable.", "tip_board_take_out": "Take {name} out of this building's menu. A game unit is hidden, never deleted; a unit you made goes from your mod.", "board_research": "Research…", "tip_board_research": "Choose what {name} is researched from: then click the unit it comes after.", "board_research_pick": "{name}: click Put under this one on the unit it comes after (any of {nation}'s buildings), or", "board_research_none": "Buildable from the start", "tip_board_research_none": "No research: it can be built from the start.", "board_research_none_done": "{name} can be built from the start now.", "board_research_cancel": "Cancel", "tip_board_research_cancel": "Leave its research as it is.", "board_under": "Put under this one", "tip_board_under": "{name} is researched from {parent}.", "board_research_done": "{name} is researched from {parent} now.", "board_price": "Research cost", "tip_board_price": "What researching it costs, in $.", "board_time": "Research time (s)", "tip_board_time": "How many seconds researching it takes.", "board_cost_saved": "{name}: research saved.", "tip_board_open": "Open {name}'s page in the Units tab.", "tip_board_drag": "Drag it along the row to change its place, or onto another building's row to move it there.", "board_moved": "{name} is in the {building} now.", "board_put_done": "{name} is in the {building} now.", "board_copied": "It's a copy in your mod, named as the game names it.", "board_unlinked": "{list}: no longer researched from it (research stays inside one nation).", "board_dates_narrowed": "It's shown only in the battles the unit it's researched from is in.", "board_relinked": "{list}: now researched from the unit before it, or buildable from the start.", "board_taken_out": "{name} is out of the build menu (hidden, not deleted).", "board_deleted": "{name} is out of your mod.", "board_ask_delete": "Take {name} out of your mod? {list} are researched from it: they'll be researched from the unit it was researched from, or buildable from the start.", "board_pick_title": "Add a unit to {nation}'s {building}", "board_pick_search": "Search units", "tip_board_pick_search": "Type part of a unit's name.", "board_pick_close": "Close", "board_pick_own": "{nation}'s own units", "tip_board_pick_own": "Picked, it moves here (one taken out comes back).", "tip_board_pick_copy": "Picked, a copy of it is made for this building, in your mod.", "tip_board_pick_move": "Put {name} in the {building}.", "tip_board_pick_copy_one": "Make a copy of {name} for {nation}, in this building.", "board_pick_out": "taken out", "board_pick_where": "in the {building}", "board_pick_era": "Era units: {era}", "tip_board_pick_era": "RUSE 2.0's units for this era, with their own models.", "tip_board_pick_era_one": "Add {name} to the {building}.", "board_pick_added": "Already in your mod.", "board_pick_no_eras": "No era units yet: download an era in the Units tab (its era buttons).", "board_pick_none": "No unit matches that."});
  Object.assign(words.fr, {"ss_title": "Que voulez-vous faire ?", "ss_carry": "Continuer un mod", "tip_ss_carry": "Ouvrez l'un de vos mods : le Studio s'ouvre dessus, tel que vous l'avez laissé.", "ss_new": "Commencer un nouveau mod", "tip_ss_new": "Nommez-le, choisissez ce que garde chaque nation, organisez ses bâtiments et ses recherches. Chaque étape peut être passée.", "ss_skip": "Passer", "tip_ss_skip": "Aller directement au Studio, avec tous ses onglets.", "ss_always": "Toujours passer cet écran (je suis un moddeur expérimenté)", "tip_ss_always": "Coché, le Studio s'ouvre directement sur ses onglets. Paramètres > Écran de départ fait revenir cet écran.", "ss_carry_head": "Vos mods", "ss_open": "Ouvrir", "tip_ss_open": "Ouvrir {name} dans le Studio.", "ss_changed": "Dernière modification : {when}", "ss_back": "Retour", "tip_ss_back": "Revenir aux trois choix.", "set_start_title": "Écran de départ", "set_start_help": "L'écran sur lequel s'ouvre le Studio : continuer un mod, en commencer un nouveau, ou le passer.", "set_start_show": "Afficher l'écran de départ à l'ouverture du Studio", "tip_set_start_show": "Décoché, le Studio s'ouvre directement sur ses onglets, comme avec Toujours passer de l'écran de départ.", "set_start_open": "Ouvrir l'écran de départ maintenant", "tip_set_start_open": "Afficher l'écran de départ : continuer un mod, ou en commencer un nouveau.", "flow_bar": "Nouveau mod, étape {n} sur {all} : {step}", "flow_step_name": "Nom", "flow_step_nations": "Nations", "flow_step_research": "Recherche", "flow_step_board": "Bâtiments", "flow_step_change": "Quoi d'autre", "flow_step_done": "Terminé", "flow_back": "Retour", "tip_flow_back": "L'étape d'avant.", "flow_next": "Suivant", "tip_flow_next": "Garder ce que cette étape a réglé et passer à la suivante.", "flow_finish": "Terminer", "tip_flow_finish": "Terminer les étapes et aller au Studio.", "flow_studio": "Aller au Studio maintenant", "tip_flow_studio": "Quitter les étapes : tout ce qui a été réglé est enregistré dans votre mod.", "flow_name_head": "Comment s'appelle votre mod ?", "flow_name_help": "Le nom que les joueurs voient dans le Launcher.", "flow_name_placeholder": "Mon mod", "tip_flow_name": "Le nom de votre mod. Appuyez sur Entrée ou Suivant pour le créer.", "flow_name_needed": "Donnez d'abord un nom à votre mod.", "flow_made": "{name} est créé : tout ce qui suit y est enregistré.", "flow_name_made": "{name} est créé. Continuez avec Suivant.", "flow_help_nations": "Pour chaque nation : Garder ses unités (ses menus de construction comme dans le jeu) ou La vider (vous remplissez ses bâtiments à l'étape Bâtiments). Modifier lui donne un nouveau nom et un nouveau drapeau.", "flow_keep": "Garder ses unités", "tip_flow_keep": "Les menus de construction de {nation} restent comme dans le jeu.", "flow_empty": "La vider", "tip_flow_empty": "Retirer toutes les unités de {nation} de ses menus de construction, à chaque date de bataille. Son QG, ses usines et ses dépôts restent ; vous remplissez ses bâtiments à l'étape Bâtiments.", "flow_research_head": "Recherche", "flow_research_help": "Comment les unités se débloquent dans votre mod.", "flow_research_keep": "Garder les recherches du jeu", "flow_research_keep_help": "Les unités se recherchent comme dans le jeu.", "flow_research_none": "Aucune recherche", "flow_research_none_help": "Chaque unité peut être construite dès le départ : rien n'est à rechercher.", "flow_research_custom": "Personnalisée", "flow_research_custom_help": "Commence avec les recherches du jeu. À l'étape suivante, placez chaque unité sous celle dont elle se recherche, comme vous voulez.", "flow_research_none_done": "Aucune recherche : {n} unités peuvent maintenant être construites dès le départ.", "flow_research_reset_done": "Les recherches du jeu sont revenues.", "flow_board_head": "Bâtiments", "flow_board_help": "Choisissez une nation. Chaque ligne est l'un de ses bâtiments avec son menu de construction, dans l'ordre du jeu : + ajoute une unité, glissez une unité pour la déplacer, Recherche… la place sous l'unité dont elle se recherche.", "flow_board_help_custom": "Choisissez une nation. Pour changer la recherche : Recherche… sur une unité, puis cliquez l'unité après laquelle elle vient, dans n'importe quel bâtiment de la nation. + ajoute une unité, glissez une unité pour la déplacer.", "tip_flow_board_nation": "Afficher les bâtiments de {nation}.", "flow_change_head": "Que va changer votre mod ?", "flow_change_help": "Cochez ce que vous voulez changer ensuite : chacun s'ouvre dans son onglet, avec Suivant au-dessus pour continuer. Laissez tout décoché pour terminer maintenant.", "flow_change_units": "Valeurs des unités", "tip_flow_change_units": "Santé, armes, vitesse, prix… de chaque unité (l'onglet Unités).", "flow_change_ai": "Réglages de l'IA et des joueurs", "tip_flow_change_ai": "Argent de départ, revenus, dépôts de ravitaillement, et comment jouent les joueurs ordinateur et ce qu'ils construisent (l'onglet Réglages de l'IA et des joueurs).", "flow_change_music": "Musique et sons", "tip_flow_change_music": "Les musiques du jeu, remplacées, ou de nouvelles ajoutées (l'onglet Musique).", "flow_change_values": "Toute autre valeur", "tip_flow_change_values": "Chaque valeur des fichiers du jeu, trouvée par son nom (l'onglet Toutes les valeurs).", "flow_help_units": "Choisissez une unité à gauche et changez ses valeurs. Suivant quand vous avez fini.", "flow_help_ai": "Changez l'argent, les revenus et les dépôts, et la façon de jouer des joueurs ordinateur. Suivant quand vous avez fini.", "flow_help_music": "Remplacez une musique ou ajoutez-en une. Suivant quand vous avez fini.", "flow_help_values": "Cherchez n'importe quelle valeur et changez-la. Suivant quand vous avez fini.", "flow_done_head": "{name} est prêt", "flow_done_help": "Testez-le dans le jeu, ou continuez à le modifier dans n'importe quel onglet. Continuer un mod, sur l'écran de départ, le rouvre.", "flow_done_test": "Tester dans le jeu", "tip_flow_done_test": "Construire votre mod dans la copie moddée et lancer le jeu depuis celle-ci.", "board_head": "Bâtiments et unités", "tip_board_head": "Chaque bâtiment de cette nation avec les unités que propose son menu de construction.", "board_help": "Chaque ligne est l'un des bâtiments de {nation} avec son menu de construction, dans l'ordre du jeu. + ajoute une unité ; glissez une unité le long de sa ligne, ou vers un autre bâtiment ; × la retire ; Recherche… la place sous l'unité dont elle se recherche.", "board_loading": "Lecture des menus de construction…", "board_no_mod": "Choisissez ou créez d'abord un mod : les changements y sont enregistrés.", "board_count": "Unités : {n}", "board_untried": "Plus de 10 : pas encore essayé dans le jeu", "tip_board_untried": "Les bâtiments du jeu utilisent jusqu'à {n} places. Plus est permis ; la façon dont le menu du jeu les affiche n'a pas encore été essayée.", "tip_board_add": "Ajouter une unité au bâtiment {building} de {nation} : l'une des siennes, la copie d'une unité d'une autre nation, ou une unité d'époque.", "board_empty_row": "Rien à construire ici. Dans le jeu, ce bâtiment montre alors la liste de bâtiments du QG quand on le choisit. Cliquez sur + pour ajouter une unité.", "board_dates_from": "Dès {year}", "board_dates_no_nuclear": "Pas en Nucléaire", "board_dates_nuclear_only": "Nucléaire seulement", "board_dates_none": "Dans aucune bataille", "tip_board_dates": "Les batailles dont le menu de construction la montre, comme dans le jeu. En Guerre totale, elle arrive quand la bataille atteint cette année.", "board_new": "À vous", "tip_board_new": "Une unité créée dans votre mod.", "board_mix_short": "Pas essayé", "board_mix": "Pas encore essayé dans le jeu : un avion dans un bâtiment terrestre, ou un véhicule à l'aérodrome.", "board_from_other": "Recherchée depuis {name} ({building})", "tip_board_from_other": "Recherchée depuis une unité d'un autre bâtiment : pas encore essayé dans le jeu. L'unité dont elle se recherche reste constructible.", "tip_board_take_out": "Retirer {name} du menu de ce bâtiment. Une unité du jeu est cachée, jamais supprimée ; une unité que vous avez créée quitte votre mod.", "board_research": "Recherche…", "tip_board_research": "Choisir depuis quoi {name} se recherche : cliquez ensuite l'unité après laquelle elle vient.", "board_research_pick": "{name} : cliquez Placer sous celle-ci sur l'unité après laquelle elle vient (n'importe quel bâtiment de {nation}), ou", "board_research_none": "Constructible dès le départ", "tip_board_research_none": "Aucune recherche : elle peut être construite dès le départ.", "board_research_none_done": "{name} peut maintenant être construite dès le départ.", "board_research_cancel": "Annuler", "tip_board_research_cancel": "Laisser sa recherche telle quelle.", "board_under": "Placer sous celle-ci", "tip_board_under": "{name} se recherche depuis {parent}.", "board_research_done": "{name} se recherche maintenant depuis {parent}.", "board_price": "Coût de recherche", "tip_board_price": "Ce que coûte sa recherche, en $.", "board_time": "Temps de recherche (s)", "tip_board_time": "Combien de secondes dure sa recherche.", "board_cost_saved": "{name} : recherche enregistrée.", "tip_board_open": "Ouvrir la page de {name} dans l'onglet Unités.", "tip_board_drag": "Glissez-la le long de la ligne pour changer sa place, ou sur la ligne d'un autre bâtiment pour l'y déplacer.", "board_moved": "{name} est maintenant dans {building}.", "board_put_done": "{name} est maintenant dans {building}.", "board_copied": "C'est une copie dans votre mod, nommée comme dans le jeu.", "board_unlinked": "{list} : ne se recherchent plus depuis elle (la recherche reste dans une seule nation).", "board_dates_narrowed": "Elle n'apparaît que dans les batailles où se trouve l'unité dont elle se recherche.", "board_relinked": "{list} : se recherchent maintenant depuis l'unité d'avant, ou sont constructibles dès le départ.", "board_taken_out": "{name} a quitté le menu de construction (cachée, pas supprimée).", "board_deleted": "{name} a quitté votre mod.", "board_ask_delete": "Retirer {name} de votre mod ? {list} se recherchent depuis elle : elles se rechercheront depuis l'unité dont elle se recherchait, ou seront constructibles dès le départ.", "board_pick_title": "Ajouter une unité : {building} ({nation})", "board_pick_search": "Chercher des unités", "tip_board_pick_search": "Tapez une partie du nom d'une unité.", "board_pick_close": "Fermer", "board_pick_own": "Les unités de {nation}", "tip_board_pick_own": "Choisie, elle vient ici (une unité retirée revient).", "tip_board_pick_copy": "Choisie, une copie est faite pour ce bâtiment, dans votre mod.", "tip_board_pick_move": "Placer {name} dans {building}.", "tip_board_pick_copy_one": "Faire une copie de {name} pour {nation}, dans ce bâtiment.", "board_pick_out": "retirée", "board_pick_where": "dans {building}", "board_pick_era": "Unités d'époque : {era}", "tip_board_pick_era": "Les unités de RUSE 2.0 pour cette époque, avec leurs propres modèles.", "tip_board_pick_era_one": "Ajouter {name} à {building}.", "board_pick_added": "Déjà dans votre mod.", "board_pick_no_eras": "Pas encore d'unités d'époque : téléchargez une époque dans l'onglet Unités (ses boutons d'époque).", "board_pick_none": "Aucune unité ne correspond."});
  Object.assign(words.sc, {"ss_title": "你想做什么？", "ss_carry": "继续制作模组", "tip_ss_carry": "打开你的一个模组：Studio 会按你上次离开时的样子打开它。", "ss_new": "开始新模组", "tip_ss_new": "命名，选择每个国家保留什么，设置建筑和研究。每一步都可以跳过。", "ss_skip": "跳过", "tip_ss_skip": "直接进入 Studio，所有标签页都在。", "ss_always": "总是跳过此画面（我是有经验的模组作者）", "tip_ss_always": "勾选后，Studio 会直接打开各个标签页。设置 > 开始画面可以恢复此画面。", "ss_carry_head": "你的模组", "ss_open": "打开", "tip_ss_open": "在 Studio 中打开 {name}。", "ss_changed": "最后修改：{when}", "ss_back": "返回", "tip_ss_back": "返回三个选项。", "set_start_title": "开始画面", "set_start_help": "Studio 打开时的画面：继续制作模组、开始新模组或跳过。", "set_start_show": "打开 Studio 时显示开始画面", "tip_set_start_show": "取消勾选后，Studio 会直接打开标签页，和开始画面的“总是跳过”一样。", "set_start_open": "立即打开开始画面", "tip_set_start_open": "显示开始画面：继续制作模组或开始新模组。", "flow_bar": "新模组，第 {n} 步，共 {all} 步：{step}", "flow_step_name": "名称", "flow_step_nations": "国家", "flow_step_research": "研究", "flow_step_board": "建筑", "flow_step_change": "其他", "flow_step_done": "完成", "flow_back": "上一步", "tip_flow_back": "回到上一步。", "flow_next": "下一步", "tip_flow_next": "保留这一步的设置，进入下一步。", "flow_finish": "完成", "tip_flow_finish": "完成所有步骤，进入 Studio。", "flow_studio": "立即进入 Studio", "tip_flow_studio": "退出步骤：目前的所有设置都已保存在你的模组中。", "flow_name_head": "你的模组叫什么名字？", "flow_name_help": "玩家在 Launcher 中看到的名称。", "flow_name_placeholder": "我的模组", "tip_flow_name": "你的模组名称。按 Enter 或“下一步”创建。", "flow_name_needed": "请先给模组起个名字。", "flow_made": "{name} 已创建：之后的所有更改都会保存在其中。", "flow_name_made": "{name} 已创建。点“下一步”继续。", "flow_help_nations": "对每个国家：保留其单位（建造菜单与游戏相同），或从空开始（在“建筑”步骤中填充其建筑）。“更改”可为它设置新名称和旗帜。", "flow_keep": "保留其单位", "tip_flow_keep": "{nation}的建造菜单保持游戏原样。", "flow_empty": "从空开始", "tip_flow_empty": "把{nation}的所有单位从每个战斗年代的建造菜单中移除。其指挥部、工厂和补给站保留；在“建筑”步骤中填充其建筑。", "flow_research_head": "研究", "flow_research_help": "模组中单位如何解锁。", "flow_research_keep": "保留游戏的研究", "flow_research_keep_help": "单位的研究方式与游戏相同。", "flow_research_none": "无研究", "flow_research_none_help": "所有单位从一开始就可建造：不需要研究。", "flow_research_custom": "自定义", "flow_research_custom_help": "从游戏的研究开始。下一步中，可随意把任何单位放到其研究来源单位的下面。", "flow_research_none_done": "无研究：现在有 {n} 个单位从一开始就可建造。", "flow_research_reset_done": "已恢复游戏的研究。", "flow_board_head": "建筑", "flow_board_help": "选择一个国家。每一行是它的一座建筑及其建造菜单，顺序与游戏相同：+ 添加单位，拖动单位可移动，“研究…”把它放到其研究来源单位下面。", "flow_board_help_custom": "选择一个国家。要更改研究：点单位的“研究…”，再点它之前的那个单位（该国家的任何建筑都可以）。+ 添加单位，拖动可移动单位。", "tip_flow_board_nation": "显示{nation}的建筑。", "flow_change_head": "你的模组要改变什么？", "flow_change_help": "勾选接下来要更改的内容：每项都会在自己的标签页中打开，上方有“下一步”。全部不勾选则现在完成。", "flow_change_units": "单位数值", "tip_flow_change_units": "每个单位的生命值、武器、速度、价格……（“单位”标签页）。", "flow_change_ai": "AI 与玩家设置", "tip_flow_change_ai": "初始资金、收入、补给站，以及电脑玩家的打法和建造内容（“AI 与玩家设置”标签页）。", "flow_change_music": "音乐和声音", "tip_flow_change_music": "替换游戏的歌曲或添加新歌曲（“音乐”标签页）。", "flow_change_values": "任何其他数值", "tip_flow_change_values": "按名称查找游戏文件中的任何数值（“所有数值”标签页）。", "flow_help_units": "在左侧选择一个单位并修改其数值。完成后点“下一步”。", "flow_help_ai": "修改资金、收入和补给站，以及电脑玩家的打法。完成后点“下一步”。", "flow_help_music": "替换或添加一首歌曲。完成后点“下一步”。", "flow_help_values": "搜索任意数值并修改。完成后点“下一步”。", "flow_done_head": "{name} 已就绪", "flow_done_help": "在游戏中测试它，或在任意标签页继续修改。开始画面的“继续制作模组”可以再次打开它。", "flow_done_test": "在游戏中测试", "tip_flow_done_test": "把模组构建到模组副本中，并从中启动游戏。", "board_head": "建筑和单位", "tip_board_head": "该国家的每座建筑及其建造菜单提供的单位。", "board_help": "每一行是{nation}的一座建筑及其建造菜单，顺序与游戏相同。+ 添加单位；沿行拖动单位或拖到另一座建筑；× 移除；“研究…”把它放到其研究来源单位下面。", "board_loading": "正在读取建造菜单…", "board_no_mod": "请先选择或创建一个模组：更改会保存在其中。", "board_count": "单位：{n}", "board_untried": "超过 10 个：尚未在游戏中测试", "tip_board_untried": "游戏自带建筑最多使用 {n} 个位置。可以更多；游戏菜单会如何显示尚未测试。", "tip_board_add": "为{nation}的{building}添加单位：本国的、其他国家单位的副本，或时代单位。", "board_empty_row": "这里没有可建造的单位。游戏中选择该建筑时会显示指挥部的建筑列表。点 + 添加单位。", "board_dates_from": "从 {year} 年起", "board_dates_no_nuclear": "核战模式中没有", "board_dates_nuclear_only": "仅核战模式", "board_dates_none": "不出现在任何战斗中", "tip_board_dates": "与游戏相同，显示该单位的战斗类型。在全面战争中，战斗进入那一年时它才出现。", "board_new": "你的", "tip_board_new": "在你的模组中制作的单位。", "board_mix_short": "未测试", "board_mix": "尚未在游戏中测试：地面建筑中的飞机，或机场中的车辆。", "board_from_other": "由{name}研究（{building}）", "tip_board_from_other": "由另一座建筑的单位研究：尚未在游戏中测试。研究来源单位仍可建造。", "tip_board_take_out": "把{name}从该建筑的菜单中移除。游戏单位只会隐藏，不会删除；你制作的单位会从模组中移除。", "board_research": "研究…", "tip_board_research": "选择{name}从哪个单位研究：然后点击它之前的那个单位。", "board_research_pick": "{name}：在它之前的单位上点“放到它下面”（{nation}的任何建筑都可以），或", "board_research_none": "一开始即可建造", "tip_board_research_none": "无需研究：一开始即可建造。", "board_research_none_done": "{name} 现在一开始即可建造。", "board_research_cancel": "取消", "tip_board_research_cancel": "保持其研究不变。", "board_under": "放到它下面", "tip_board_under": "{name}由{parent}研究。", "board_research_done": "{name}现在由{parent}研究。", "board_price": "研究费用", "tip_board_price": "研究所需费用（$）。", "board_time": "研究时间（秒）", "tip_board_time": "研究需要多少秒。", "board_cost_saved": "{name}：研究已保存。", "tip_board_open": "在“单位”标签页中打开{name}的页面。", "tip_board_drag": "沿行拖动可改变位置，拖到另一座建筑的行可移到那里。", "board_moved": "{name} 现在在{building}中。", "board_put_done": "{name} 现在在{building}中。", "board_copied": "这是你模组中的副本，名称与游戏相同。", "board_unlinked": "{list}：不再由它研究（研究只在同一个国家内）。", "board_dates_narrowed": "它只出现在其研究来源单位出现的战斗中。", "board_relinked": "{list}：现在由前一个单位研究，或一开始即可建造。", "board_taken_out": "{name} 已从建造菜单中移除（只是隐藏，未删除）。", "board_deleted": "{name} 已从你的模组中移除。", "board_ask_delete": "要把{name}从模组中移除吗？{list}由它研究：之后将由它的研究来源单位研究，或一开始即可建造。", "board_pick_title": "为{nation}的{building}添加单位", "board_pick_search": "搜索单位", "tip_board_pick_search": "输入单位名称的一部分。", "board_pick_close": "关闭", "board_pick_own": "{nation}自己的单位", "tip_board_pick_own": "选择后会移到这里（已移除的会恢复）。", "tip_board_pick_copy": "选择后会在你的模组中为该建筑制作一个副本。", "tip_board_pick_move": "把{name}放入{building}。", "tip_board_pick_copy_one": "为{nation}在该建筑中制作{name}的副本。", "board_pick_out": "已移除", "board_pick_where": "在{building}", "board_pick_era": "时代单位：{era}", "tip_board_pick_era": "RUSE 2.0 为这个时代准备的单位，带有自己的模型。", "tip_board_pick_era_one": "把{name}添加到{building}。", "board_pick_added": "已在你的模组中。", "board_pick_no_eras": "还没有时代单位：请在“单位”标签页（时代按钮）中下载一个时代。", "board_pick_none": "没有匹配的单位。"});
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
  const nationHidden = new Set();  // units a nation's Hide all took out of its build menus (StudioApi.nation_units_hide)
  // the board's made-up build menus (StudioApi.board, ruse_studio/board.py): each made-up unit in its nation's
  // building, the Sherman researched from the Stuart (and shown from 1942), the board's own changes on top
  const FAKE_BOARD_ROWS = [8, 13, 10, 11, 9, 12];
  const FAKE_BOARD_BASE = { 8: 100, 13: 200, 10: 300, 11: 400, 9: 500, 12: 600, 6: 700, 4: 700, 7: 700 };
  const FAKE_OWN_KINDS = [6, 4, 7];  // rusemod.ownbuildings.KINDS: buildings with units of their own, three a nation
  const fakeBuildings = [];  // the board's Add a building: { address, name, nation, kind, source }
  const FAKE_BUILDING_NAMES = {
    us: { 8: "BARRACKS", 13: "ARTILLERY & ANTI-AIR BASE", 10: "ARMOR BASE", 11: "ANTI-TANK BASE", 9: "AIRFIELD", 12: "PROTOTYPE BASE" },
    fr: { 8: "CASERNE", 13: "BASE D'ARTILLERIE ET DCA", 10: "BASE DE BLINDES", 11: "BASE ANTICHAR", 9: "AERODROME", 12: "BASE DE PROTOTYPE" },
    sc: { 8: "兵营", 13: "火炮与防空基地", 10: "装甲基地", 11: "反坦克基地", 9: "机场", 12: "原型基地" } };
  const FAKE_GAME_PARENT = { [E + "M4_Sherman"]: E + "M3A1_Stuart" };
  const fakeBoardOwn = new Map();  // address -> { factory, nation, slot, shows, parent } the board set
  function fakeBoardInfo(lang) {
    const out = new Map();
    const add = (address, name, kind, nation, factory, slot, isNew) => {
      const o = fakeBoardOwn.get(address) || {};
      const game = address === E + "M4_Sherman" ? [1, 1, 0, 1, 1] : [1, 1, 1, 1, 1];
      out.set(address, { address, name, kind, new: isNew, nation: o.nation ?? nation, factory: o.factory ?? factory,
        slot: o.slot ?? slot, shows: o.shows || (nationHidden.has(address) ? [0, 0, 0, 0, 0] : game),
        parent: "parent" in o ? o.parent : FAKE_GAME_PARENT[address] || null,
        research: { UpgradePrice: researchEdits.get(`${address}|UpgradePrice`) ?? 25, UpgradeTime: researchEdits.get(`${address}|UpgradeTime`) ?? 50 } });
    };
    for (const u of units) if (u.kind !== "buildings" && FAKE_BOARD_ROWS.includes(u.factory)) add(E + u.id, nameOf(u, lang), u.kind, u.nation, u.factory, u.slot, false);
    for (const n of mine()) {
      const src = units.find((u) => E + u.id === n.source) || { kind: "ground" };
      add(newAddress(n.id), n.name, src.kind, n.nation, n.factory, null, true);
    }
    return out;
  }
  function fakeDates(shows) {
    const on = (k) => Boolean(shows[k]);
    return { from: on(2) ? 1939 : on(1) ? 1942 : on(0) ? 1945 : null, nuclear: on(4) };
  }
  function fakeBoardCard(address) {  // a made-up build-menu picture: the unit's name on the game's blue
    const name = address.split("_").slice(2).join(" ").slice(0, 16);
    return "data:image/svg+xml;base64," + btoa(`<svg xmlns="http://www.w3.org/2000/svg" width="96" height="49"><rect width="96" height="49" fill="#1f6fc4"/><text x="48" y="30" font-size="10" fill="#fff" text-anchor="middle" font-family="sans-serif">${name.replace(/[<&>]/g, "")}</text></svg>`);
  }
  function fakeBoardTop(n, factory, lang) {
    const info = fakeBoardInfo(lang);
    return [...info.values()].filter((i) => i.nation === n && i.factory === factory && i.shows.some(Boolean)
      && !(i.parent && info.get(i.parent) && info.get(i.parent).factory === factory))
      .sort((a, b) => (a.slot ?? 1e9) - (b.slot ?? 1e9)).map((i) => i.address);
  }
  function fakeBoardSlot(address, slot, lang) {
    fakeBoardOwn.set(address, { ...(fakeBoardOwn.get(address) || {}), slot });
    for (const [a, i] of fakeBoardInfo(lang)) if (i.parent === address && i.factory === (fakeBoardInfo(lang).get(address) || {}).factory) fakeBoardOwn.set(a, { ...(fakeBoardOwn.get(a) || {}), slot: slot + 1 });
  }
  function fakeBoardPlace(n, factory, address, index, lang) {
    const top = fakeBoardTop(n, factory, lang).filter((a) => a !== address);
    top.splice(index === null || index === undefined ? top.length : Math.max(0, Math.min(index, top.length)), 0, address);
    top.forEach((a, k) => fakeBoardSlot(a, FAKE_BOARD_BASE[factory] + 1 + k * 3, lang));
  }
  const fakeJobs = new Map();  // id -> { state, message, lines }: jobs the stand-ins finish at once (nation_fill)
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
    era: [["310000000/1240000000", "1240000000/1240000000", "unpack"], "The Modern units are ready."],
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
  let fakeCopies = null;  // the folder chosen for modded copies (Settings), or null: the recommended place
  const copiesView = () => ({ path: fakeCopies || (fakeGame ? "D:\\RUSE-Instances" : null), how: fakeCopies ? "chosen" : "recommended",
    recommended: fakeGame ? "D:\\RUSE-Instances" : null, drive: fakeGame ? "D:" : null, other_drive: Boolean(fakeGame && fakeCopies) });
  const doctorState = { running: true, leftovers: true };
  function fakeDoctor() {
    const f = (key, level, say, fix, data) => ({ key, level, say, data: data || {}, fix: fix || null });
    const copies = fakeCopies || "D:\\RUSE-Instances";
    const findings = [fakeGame ? f("game", "ok", "doc_game_ok", null, { path: fakeGame })
      : f("game", "fail", "doc_game_missing", "choose_game"), f("steam", "info", "doc_steam_off"),
    doctorState.running ? f("running", "warn", "doc_running_copy", "close_game", { names: "RUSE.exe (4120)" })
      : f("running", "ok", "doc_running_none")];
    if (fakeGame) {  // no game: no place for modded copies yet, so no checks of them
      findings.push(fakeCopies ? f("drive", "ok", "doc_copies_chosen", null, { path: copies, fs: "NTFS", how: "chosen" })
        : f("drive", "ok", "doc_copies_recommended", null, { path: copies, fs: "NTFS", how: "recommended" }));
      if (fakeCopies) findings.push(f("other_drive", "info", "doc_copies_other_drive", null, { path: copies, drive: "D:", recommended: "D:\\RUSE-Instances" }));
      findings.push(f("space", "ok", "doc_space_ok", null, { gb: 182.4 }),
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

  const FAKE_ERA_UNITS = [{"key": "WWI|Germany|A7V", "era": "WWI", "nation": "Germany", "name": "A7V", "in_place_of": "", "card": "Super-Heavy Tank", "building": "Prototype base", "copies": "$/GFX/Everything/Descriptor_Unit_Panzer_IV_G", "copies_name": "M4 Sherman", "game_nation": 1, "factory": 10, "aircraft": false, "model": "WWI/Germany/A7V.glb", "fits": true, "credit": {"title": "tank A7V", "author": "tnikita", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}, {"key": "WWI|Germany|Gotha G.V", "era": "WWI", "nation": "Germany", "name": "Gotha G.V", "in_place_of": "", "card": "Light Bomber", "building": "Airfield", "copies": "$/GFX/Everything/Descriptor_Unit_P40Warhawk", "copies_name": "M4 Sherman", "game_nation": 1, "factory": 10, "aircraft": true, "model": "WWI/Germany/Gotha_G_V.glb", "fits": true, "credit": {"title": "Gotha G.V", "author": "panzerowl", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}, {"key": "WWI|France|75 mm Mle 1897", "era": "WWI", "nation": "France", "name": "75 mm Mle 1897", "in_place_of": "", "card": "Advanced Anti-tank Gun", "building": "Anti-tank base", "copies": "$/GFX/Everything/Descriptor_Unit_M3A1_Stuart", "copies_name": "M4 Sherman", "game_nation": 3, "factory": 10, "aircraft": false, "model": "WWI/France/75_mm.glb", "fits": false, "credit": {"title": "75mm Field Gun", "author": "kisotsu", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}, {"key": "WWI|UK|Mark V", "era": "WWI", "nation": "UK", "name": "Mark V", "in_place_of": "", "card": "Heavy Tank", "building": "Armor base", "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman", "copies_name": "M4 Sherman", "game_nation": 2, "factory": 10, "aircraft": false, "model": null, "fits": true, "credit": {"title": "tank-ww1-mark v", "author": "Ara_my45yt", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}, {"key": "Cold War|USSR|T-10", "era": "Cold War", "nation": "USSR", "name": "T-10", "in_place_of": "", "card": "Super-Heavy Tank", "building": "Prototype base", "copies": "$/GFX/Everything/Descriptor_Unit_M4_Sherman", "copies_name": "M4 Sherman", "game_nation": 5, "factory": 10, "aircraft": false, "model": "Cold_War/USSR/T-10.glb", "fits": true, "credit": {"title": "Tank T-10M", "author": "yanix", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}, {"key": "Cold War|China|J-7", "era": "Cold War", "nation": "China", "name": "J-7", "in_place_of": "", "card": "Fighter", "building": "Airfield", "copies": "$/GFX/Everything/Descriptor_Unit_P40Warhawk", "copies_name": "M4 Sherman", "game_nation": null, "factory": 10, "aircraft": true, "model": "Cold_War/China/J-7.glb", "fits": true, "credit": {"title": "Mig21", "author": "manilov.ap", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}, {"key": "Modern|Germany|Leopard 2A7", "era": "Modern", "nation": "Germany", "name": "Leopard 2A7", "in_place_of": "", "card": "Main Battle Tank", "building": "Armor base", "copies": "$/GFX/Everything/Descriptor_Unit_Panzer_IV_G", "copies_name": "M4 Sherman", "game_nation": 1, "factory": 10, "aircraft": false, "model": "Modern/Germany/Leopard.glb", "fits": true, "credit": {"title": "Leopard 2 MBT Revolution", "author": "someone", "licence": "CC-BY 4.0", "url": "https://sketchfab.com/", "extra": ""}}];
  const eraAdded = new Map();
  const eraHere = new Set(["WWI", "WWII", "Cold War"]);  // the eras "downloaded": Modern comes with its Download
  // an era unit's add form for a start unit and a build menu (StudioApi.era_unit_start): the start unit's price, the size
  // suggested and the units of that menu it may be researched from. The A7V's real width (3.1 m) and the Gotha G.V's
  // wingspan (23.7 m) are Wikipedia's; the sizes are this preview's own (the Studio works them out from the models)
  const FAKE_ERA_SIZE = {
    "WWI|Germany|A7V": { size: 1.18, real: true, clamped: null, real_m: 3.1, what: "width", why: "" },
    "WWI|Germany|Gotha G.V": { size: 5, real: true, clamped: 7.31, real_m: 23.7, what: "span", why: "" } };
  function eraStart(u, source, nation, factory) {
    const src = units.find((g) => E + g.id === source);
    const { size, ...info } = FAKE_ERA_SIZE[u.key] || { size: 1, real: false, clamped: null, real_m: null,
      what: u.aircraft ? "span" : "width", why: "no_real" };
    const choices = units.filter((g) => g.nation === nation && g.factory === factory)
      .map((g) => ({ address: E + g.id, name: g.names.us, price: g.price }))
      .concat(mine().filter((n) => n.nation === nation && n.factory === factory)
        .map((n) => ({ address: newAddress(n.id), name: n.name, price: n.price })))
      .sort((a, b) => a.name.localeCompare(b.name));
    let suggested = null, why = "";
    const standsFor = choices.find((c) => u.in_place_of && c.name.toLowerCase() === u.in_place_of.toLowerCase());
    if (choices.some((c) => c.address === source)) [suggested, why] = [source, "start"];
    else if (standsFor) [suggested, why] = [standsFor.address, "in_place_of"];
    else if (["Cold War", "Modern"].includes(u.era) && choices.length) {
      [suggested, why] = [choices.reduce((a, b) => (b.price > a.price ? b : a)).address, "dearest"];
    }
    return { price: src ? src.price : 0, size, size_info: info,
      research: { offered: true, choices: choices.map(({ address, name }) => ({ address, name })), suggested, why } };
  }
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
          .filter((u) => fakeFinds(search, [u.name, u.address, u.type || "", u.nation_name], fakeTagsOf(u)));
        return { units: out, total: units.length + made.length, groups: GROUPS.filter((g) => present.has(g)), types,
          tags: fakeTagList(shown.map((u) => ({ ...u, address: E + u.id, group: u.group || groupOf(u) })), lang) };
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
      // where modded copies go (Settings): the recommended place until a folder is chosen, which here is on another
      // drive (so the full-copy note shows); Use the recommended place puts it back
      copies_folder: async () => copiesView(),
      choose_copies_folder: async () => { fakeCopies = "E:\\Games\\RUSE-Instances"; return copiesView(); },
      use_recommended_copies: async () => { fakeCopies = null; return copiesView(); },
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
      flags: async (lang) => ({ flags: knownFlags.map((f) => ({ ...f, meaning: f.meaning ? (f.meaning[lang] || f.meaning.us) : null,
        ...(FAKE_FLAG_GUIDE[f.flag] || {}) })), groups: ["kind", "combat", "movement", "sight", "player", "preview", "state", "unused"] }),
      numbers: async () => FAKE_NUMBERS,
      number_scale: async (address, prop) => {
        const made = { SeuilMort: [250, 300, 400, 900, 2000, 400], VitesseLineaire: [520, 2600, 4030, 6110, 57200, 4550],
          ProductionTime: [5, 5, 10, 20, 60, 20], ProductionPrice: [0, 5, 15, 40, 80, 15], DetectionBase: [26, 26000, 104000, 234000, 234000, 104000],
          VitesseRotation: [0.26, 0.35, 0.52, 2.1, 3.5, 0.52] }[prop];
        if (!made) return {};
        const [min, low, median, high, max, game] = made;
        return { class: "TUniteAuSolDescriptor", count: 204, min, low, median, high, max, game,
          marks: [{ name: "Jeep", value: min }, { name: "M4 Sherman", value: median }, { name: "Tiger", value: max }] };
      },
      flag_check: async (address, flags) => {
        const truck = /Truck|GMC/i.test(address), problems = [];
        for (const n of [62, 63]) if (!truck && (flags || []).includes(n)) problems.push({ level: "error", flag: n,
          why: `Flag ${n} (${n === 62 ? "truck" : "construction truck"}) crashes the game at match start on anything that isn't a truck. Take it off.` });
        const adding = truck ? {} : { 62: "error", 63: "error" };
        return { problems, blocked: problems.length > 0, adding };
      },
      delete_unit: async (address, researched) => {
        const j = newAmmo.findIndex((n) => n.mod === current && ammoAddress(n.id) === address);
        if (j >= 0) {
          const [gone] = newAmmo.splice(j, 1);
          for (const k of [...edits.keys()]) if (k.split("|")[1].startsWith(address) || edits.get(k) === address) edits.delete(k);
          return { deleted: address, source: gone.source, saved: current + "/src/studio.rndf" };
        }
        const i = newUnits.findIndex((n) => n.mod === current && newAddress(n.id) === address);
        if (i < 0) throw new Error(`${address} isn't a unit made in this mod, so it can't be deleted here`);
        const research = researchGone(address, researched);
        if (research.ask) return { deleted: null, ask: research.ask };
        const [gone] = newUnits.splice(i, 1);
        for (const k of [...edits.keys()]) if (k.split("|")[1].startsWith(address)) edits.delete(k);
        upgradeEdits.delete(address);
        return { deleted: address, source: gone.source, saved: current + "/src/studio.rndf", ...research };
      },
      unit: async (address, lang, via) => unit(address, lang, via),
      upgrade: async (address, lang) => upgradeOf(address, lang),
      plane_role: async (address) => roleOf(address),
      set_plane_role: async (address, role) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (role === null || role === roleOf(address).game) roleEdits.delete(address); else roleEdits.set(address, role);
        return { saved: current + "/src/studio.rndf", ...roleOf(address) };
      },
      ground_role: async (address) => groundRoleOf(address),
      set_ground_role: async (address, role) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (role === "recon") groundRoleEdits.set(address, role); else groundRoleEdits.delete(address);
        return { saved: current + "/src/studio.rndf", ...groundRoleOf(address) };
      },
      set_weapon_hits: async (unitAddress, weapon, hits) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (hits === "ground") hitsEdits.delete(weapon); else hitsEdits.set(weapon, hits);
        return { saved: current + "/src/studio.rndf", hits };
      },
      armour: async (address) => armourOf(address),
      set_armour: async (address, value) => {
        if (value === null || value === 6) armourEdits.delete(address); else armourEdits.set(address, value);
        return { saved: "src/studio.rndf", ...armourOf(address) };
      },
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
        fakeModels.set(address, { ...FAKE_IMPORT, scale: 2.46 * (size || 1), size: Number(size) || 1 });
        return { model: fakeModels.get(address), ...fakeLook(address) };
      },
      model_import_remove: async (address) => { fakeModels.delete(address); return fakeLook(address); },
      model_copy: async (address) => {
        if (fakeModels.has(address)) throw new Error("This unit has an imported model: take it out first (Remove the model), then give it a copy.");
        fakeModelCopies.add(address);
        return { ...fakeLook(address), message: fakeSquad(address) ? "It has a uniform of its own now: Repaint in Blender changes only this squad."
          : "It has its own copy of the model now: Repaint in Blender changes only this unit." };
      },
      model_copy_remove: async (address) => {
        fakeModelCopies.delete(address);
        return { ...fakeLook(address), message: fakeSquad(address) ? "It wears the default uniform again. Your paint is kept in the mod, for when it gets a custom one again."
          : "It draws the model it copies again. Its paint is kept in the mod, for when it gets a copy again." };
      },
      rides_in: async (address) => fakeRidesIn(address),
      rides_in_set: async (address, truck) => {
        const info = fakeRidesIn(address);
        const chosen = (info.choices || []).find((c) => c.address === truck);
        if (!chosen) throw new Error("That isn't one of the trucks it can ride in.");
        if (truck === info.game) fakeRides.delete(address); else fakeRides.set(address, truck);
        return { ...fakeRidesIn(address), message: `It rides in ${chosen.name} on the roads now.` };
      },
      // its size on the slider (StudioApi.model_size_marks / model_sizes / model_resize / models_resize_all): a plane
      // (an address with Avion in it) has a real-life size of 3.4, a ground unit 1.3
      model_size_marks: async (address) => ({ tiny: 0.05, huge: 20, game: 1, real: /Avion/.test(address) ? 3.4 : 1.3,
        start: (units.find((u) => address.endsWith(u.id)) || {}).name || "Sherman" }),
      model_sizes: async (address, lang) => {
        const own = fakeModels.get(address);
        if (!own) return null;
        const kind = /Avion/.test(address) ? "air" : "ground";
        return { size: own.size || 1, resizable: true, kind, marks: await window.pywebview.api.model_size_marks(address, lang),
          same_kind: [...fakeModels.keys()].filter((a) => /Avion/.test(a) === (kind === "air")).length };
      },
      model_resize: async (address, size) => {
        if (!fakeModels.has(address)) throw new Error("This unit has no model of its own to resize: import one first.");
        await new Promise((r) => setTimeout(r, 400));
        fakeModels.set(address, { ...fakeModels.get(address), scale: 2.46 * size, size: Number(size) });
        return { model: fakeModels.get(address), ...fakeLook(address) };
      },
      models_resize_all: async (kind, to, times) => {
        const lines = [];
        for (const [a, m] of fakeModels) {
          if (kind !== "all" && /Avion/.test(a) !== (kind === "air")) continue;
          const size = to === "game" ? 1 : to === "real" ? (/Avion/.test(a) ? 3.4 : 1.3) : Math.min(20, Math.max(0.05, (m.size || 1) * times));
          fakeModels.set(a, { ...m, scale: 2.46 * size, size });
          lines.push(`resized\t${a.split("/").pop()}\t${size}`);
        }
        fakeJobs.set("resize", { state: "done", message: `${lines.length} model(s) done.`, lines });
        return { job: "resize" };
      },
      look_open: async (address) => {
        if (mode === "noblender") throw new Error("Blender isn't found on this PC. Get it free from blender.org (Get Blender), then use Choose Blender… to show the Studio where blender.exe is.");
        if (fakeSquad(address) && !fakeModelCopies.has(address)) throw new Error("Pick Custom uniform first: the default uniform is worn by other squads and by gun and vehicle crews too, so it isn't repainted here.");
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
      // a building's look (StudioApi.building_look, ...): a made-up look's pieces, a new building's model kept here
      building_look: async (address) => fakeBuildingLook(address),
      building_look_import: async (address, piece, file, size = 1, twoSided = false, source = "", author = "",
        licence = "") => {
        const made = mine().find((n) => address === newAddress(n.id));
        if (!made) throw new Error("Only a new building made in this mod can get a model of its own: copy the building first.");
        if (licence && !["CC0", "CC-BY"].includes(licence)) throw new Error(`hall.glb: a model taken from others must be CC0 or CC-BY (this one says ${licence})`);
        await new Promise((r) => setTimeout(r, 400));
        fakeBuildingModels.set(address, { piece, file: `${made.id}.glb`, size: Number(size) || 1, two_sided: false,
          credit: Object.fromEntries(Object.entries({ source, author, licence }).filter(([, v]) => v)), triangles: 5120,
          versions: { medium: { file: `${made.id}_medium.glb`, triangles: 1400 }, far: { file: `${made.id}_far.glb`, triangles: 160 } } });
        return { done: true, ...fakeBuildingLook(address) };
      },
      building_look_change: async (address, size, twoSided, source, author, licence) => {
        const own = fakeBuildingModels.get(address);
        if (!own) throw new Error("This building has no model of its own yet.");
        Object.assign(own, { size: Number(size) || own.size,
          credit: Object.fromEntries(Object.entries({ source, author, licence }).filter(([, v]) => v)) });
        return fakeBuildingLook(address);
      },
      building_look_remove: async (address) => { fakeBuildingModels.delete(address); return fakeBuildingLook(address); },
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
      choose_mod: async (path, kind, anyway = false) => {
        if (fakeFormat(path).state === "newer" && !anyway) {
          throw new Error(`${path.split("/").pop()} was saved by a newer RUSE Studio (mod format 2; this one knows 1). Update the Studio before changing it: this version could drop what it doesn't know when it saves.`);
        }
        return kind === "map" ? (currentMap = path, mapsView()) : (current = path, modsView());
      },
      // the mod format (rusemod.modformat): ?fake=oldmod has the mod being edited in an older one with a step to run,
      // ?fake=newmod has "another-mod" saved by a newer Studio
      mod_format: async (kind, path = "") => {
        const p = path || (kind === "map" ? currentMap : current);
        return p ? { ...fakeFormat(p), name: p.split("/").pop(), path: p } : { state: "none" };
      },
      update_mod: async (kind) => {
        const p = kind === "map" ? currentMap : current;
        fakeFormats.set(p, 1);
        return { from: 0, to: 1, backup: `${home}mod-backups/${p.split("/").pop()}-2026-10-16-120000-format0.zip`, changed: [],
          format: { ...fakeFormat(p), name: p.split("/").pop(), path: p } };
      },
      open_mod_folder: async () => {
        const path = "D:/Mods/another-mod";
        if (!mods.some((m) => m.path === path)) mods.push({ path, name: "another-mod" });
        current = path;
        return modsView();
      },
      // Edit an installed mod: the Launcher's library, made up (a Studio mod of someone else's, one of yours, an .rmod)
      installed_mods: async () => ({ mods: [
        { id: "r-u-s-e-field-manual-v1", name: "R.U.S.E. Field Manual", version: "1.0.0", author: "nickgit", description: "",
          yours: "", older: false, units: true, maps: false, edited_from: "", error: "" },
        { id: "my-mod", name: "my-mod", version: "0.1.0", author: "", description: "", yours: home + "my-mod",
          older: false, units: true, maps: true, edited_from: "", error: "" },
        { id: "airfield-capacity", name: "Airfield Capacity", version: "1", author: "LittleGroove", description: "",
          yours: "", older: true, units: false, maps: false, edited_from: "", error: "" }] }),
      edit_installed: async (id, name) => {
        if (id === "my-mod") {
          current = currentMap = home + "my-mod";
          return { mod: modsView(), map: mapsView(), path: current, copied: false, units: true, maps: true,
                   message: "my-mod is open: your changes go into it. Export puts it in the Launcher again." };
        }
        const key = (s) => String(s || "").trim().toLowerCase().replace(/\s+/g, " ");
        const [original, author] = id === "airfield-capacity" ? ["Airfield Capacity", "LittleGroove"] : ["R.U.S.E. Field Manual", "nickgit"];
        if (!key(name)) throw new Error(`Give your copy a name of its own: it can't be called ${original}.`);
        if (key(name) === key(original)) throw new Error(`${original} is ${author}'s name for the mod. Give your copy a name of its own.`);
        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "my-edit";
        if (!mods.some((m) => m.path === home + slug)) mods.push({ path: home + slug, name: slug });
        current = home + slug;
        const message = id === "airfield-capacity"
          ? `Your copy ${name} is open. 12 of ${original}'s changes are in the Studio now, ready to change. Kept as they are, and still in the mod: 2 new objects.`
          : `Your copy ${name} is open: everything in ${original} is in it, and your changes go into it.`;
        return { mod: modsView(), map: mapsView(), path: current, copied: true, units: true, maps: false, message };
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
      // (each change kept per copy, "normal|prop" and "atomic|prop"; "split": the two modes shown apart)
      economy: async (lang) => ({ ready: mode !== "noindex", groups: ECONOMY.map(([id, rows]) => ({ id, rows: rows.map(
        ([prop, label, type, game, atomic]) => {
          const a = atomic === undefined ? game : atomic;
          const mine = (m) => economyEdits.has(`${m}|${prop}`) ? economyEdits.get(`${m}|${prop}`) : null;
          const n = mine("normal"), at = mine("atomic");
          const split = JSON.stringify(a) !== JSON.stringify(game)
            || JSON.stringify(n === null ? game : n) !== JSON.stringify(at === null ? a : at);
          return { prop, label: lang === "base" ? prop : label, type, list: Array.isArray(game), game,
            atomic: atomic === undefined ? null : atomic, split, value: split || n !== null ? n : at,
            atomic_value: split ? at : null };
        }) })) }),
      economy_edit: async (prop, value, which) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const row = ECONOMY.flatMap(([, rows]) => rows).find((r) => r[0] === prop);
        const whole = (v) => row[2] === "float32" ? v : Math.round(v);
        const v = Array.isArray(value) ? value.map(whole) : whole(value);
        for (const m of which ? [which] : ["normal", "atomic"]) {
          const game = m === "atomic" && row[4] !== undefined ? row[4] : row[3];
          if (JSON.stringify(v) === JSON.stringify(game)) economyEdits.delete(`${m}|${prop}`);
          else economyEdits.set(`${m}|${prop}`, v);
        }
        return { saved: current + "/src/studio.rndf", value: v };
      },
      economy_reset: async (prop, which) => {
        for (const m of which ? [which] : ["normal", "atomic"]) economyEdits.delete(`${m}|${prop}`);
        return { saved: current + "/src/studio.rndf" };
      },
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
        bonuses: [{ id: AI_BONUS, rows: AI_BONUS_ROWS.map((r) => ({ ...aiRowOf(AI_BONUS, lang, r),
          ...(AI_CHOICES[r[0]] ? { names: aiNames(r[0]) } : {}) })) }],
        cards: AI_CARDS.map(([id, name, about, rows]) => ({ id, name, about, in_menu: rows.some((r) => r[0] === "ShowInMenu"),
          rows: rows.map((r) => aiRowOf(id, lang, r)) })),
        battle: aiBattle(), choices: AI_CHOICES }),
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
      // a nation's units at once (StudioApi.nation_units / nation_units_hide / nation_fill_list / nation_fill)
      nation_units: async (n, lang = "us") => {
        const own = units.filter((u) => u.nation === n && u.kind !== "buildings" && u.factory !== undefined && u.factory !== null)
          .map((u) => ({ address: E + u.id, name: nameOf(u, lang), kind: u.kind, factory: u.factory, hidden: nationHidden.has(E + u.id) }));
        const eras = [...eraHere].map((era) => ({ era, nations: [...new Set(FAKE_ERA_UNITS.filter((u) => u.era === era).map((u) => u.nation))].sort() }))
          .filter((e) => e.nations.length);
        // its buildings left with nothing to build: every own unit there hidden, none of the era units added put in
        const filled = new Set(FAKE_ERA_UNITS.filter((u) => eraAdded.has(u.key)).map((u) => u.factory));
        const empty = [...new Set(own.map((u) => u.factory))].filter((f) => !filled.has(f)
          && own.filter((u) => u.factory === f).every((u) => u.hidden)).sort((a, b) => a - b);
        return { nation: n, units: own, hidden: own.filter((u) => u.hidden).length, can: Boolean(current), eras, empty };
      },
      nation_units_hide: async (n, hide = true, lang = "us", factory = null) => {
        if (!current) throw new Error("Pick or make a mod first: the change is saved in it.");
        for (const u of units.filter((x) => x.nation === n && x.kind !== "buildings" && (factory === null || x.factory === factory))) {
          if (hide) nationHidden.add(E + u.id); else nationHidden.delete(E + u.id);
        }
        return window.pywebview.api.nation_units(n);
      },
      nation_fill_list: async (n, era, source, lang = "us") => {
        const menus = (await window.pywebview.api.menus(lang)).nations[n].factories;
        const have = new Set(menus.map((m) => m.factory));
        return { menus, units: FAKE_ERA_UNITS.filter((u) => u.era === era && u.nation === source).map((u) => ({ key: u.key,
          name: u.name, card: u.card, kind: u.aircraft ? "air" : "ground", factory: have.has(u.factory) ? u.factory : null,
          added: eraAdded.has(u.key) })) };
      },
      nation_fill: async (n, picks) => {
        if (!current) throw new Error("Pick or make a mod first: the units are added to it.");
        const lines = [];
        for (const p of picks) {
          const u = FAKE_ERA_UNITS.find((x) => x.key === p.key);
          try {
            const made = await window.pywebview.api.era_unit_add(p.key, n, p.factory);
            lines.push(`added\t${made.name}`);
          } catch (err) { lines.push(`skipped\t${u ? u.name : p.key}\t${err.message}`); }
        }
        fakeJobs.set("fill", { state: "done", message: `${picks.length} era unit(s) done.`, lines });
        return { job: "fill" };
      },
      // the board (StudioApi.board / board_picker / board_cards / board_put / board_order / board_move /
      // board_research / board_take_out, research_clear_all / research_reset_all, ruse_studio/board.py): the made-up
      // units by nation and building, the Sherman researched from the Stuart; changes kept for the preview only
      board: async (n, lang = "us") => {
        const info = fakeBoardInfo(lang), rows = [];
        const ownKinds = FAKE_OWN_KINDS.filter((k) => fakeBuildings.some((b) => b.nation === n && b.kind === k));
        for (const f of [...FAKE_BOARD_ROWS, ...ownKinds]) {
          const here = [...info.values()].filter((i) => i.nation === n && i.factory === f && i.shows.some(Boolean))
            .sort((a, b) => (a.slot ?? 1e9) - (b.slot ?? 1e9) || a.address.localeCompare(b.address));
          const tree = [], seen = new Set();
          const walk = (i, depth) => {
            if (seen.has(i.address)) return;
            seen.add(i.address);
            tree.push([i, depth]);
            for (const k of here.filter((x) => x.parent === i.address)) walk(k, depth + 1);
          };
          for (const i of here.filter((x) => !here.some((p) => p.address === x.parent))) walk(i, 0);
          for (const i of here) walk(i, 0);
          const names = FAKE_BUILDING_NAMES[lang] || FAKE_BUILDING_NAMES.us;
          const own = FAKE_OWN_KINDS.includes(f);
          const added = fakeBuildings.filter((b) => b.nation === n && b.kind === f)
            .map((b) => ({ address: b.address, name: b.name, new: true }));
          const buildings = own ? added : [{ address: `$/GFX/Everything/Descriptor_Building_${n}_${f}`, name: names[f], new: false }, ...added];
          rows.push({ factory: f, building: buildings[0].name, buildings, own, most: tree.length, untried: tree.length > 10,
            units: tree.map(([i, depth]) => {
              const p = info.get(i.parent);
              return { address: i.address, name: i.name, new: i.new, kind: i.kind, depth, parent: i.parent || null,
                parent_name: p ? p.name : null, parent_factory: p && p.factory !== f ? p.factory : null,
                upgrade: Boolean(p && p.factory === f), dates: fakeDates(i.shows), research: i.parent ? i.research : null,
                untried_mix: i.kind !== "infantry" && (i.kind === "air") !== (f === 9) };
            }) });
        }
        const out = [...info.values()].filter((i) => i.nation === n && !i.shows.some(Boolean))
          .map((i) => ({ address: i.address, name: i.name, factory: i.factory, new: i.new }));
        return { nation: n, can: Boolean(current), rows, taken_out: out, own_left: 3 - ownKinds.length };
      },
      board_building_sources: async (n, lang = "us") => {
        const names = FAKE_BUILDING_NAMES[lang] || FAKE_BUILDING_NAMES.us, nationNames = await window.pywebview.api.nations(lang);
        const used = FAKE_OWN_KINDS.filter((k) => fakeBuildings.some((b) => b.nation === n && b.kind === k));
        const order = [n, ...[0, 1, 2, 3, 4, 5, 6].filter((m) => m !== n)];
        return { buildings: order.flatMap((m) => FAKE_BOARD_ROWS.map((k) => ({
          address: `$/GFX/Everything/Descriptor_Building_${m}_${k}`, name: names[k], nation: m,
          nation_name: nationNames[m] || String(m), kind: k }))),
        own_left: 3 - used.length, next_kind: FAKE_OWN_KINDS.find((k) => !used.includes(k)) ?? null, patch_kinds: [4, 7] };
      },
      board_add_building: async (n, source, name, own = false, lang = "us") => {
        if (!current) throw new Error("Pick or make a mod first: the board's changes are saved in it.");
        if (!String(name || "").trim()) throw new Error("Give the new building a name.");
        const used = FAKE_OWN_KINDS.filter((k) => fakeBuildings.some((b) => b.nation === n && b.kind === k));
        let kind = Number(String(source).split("_").pop());
        if (own) {
          kind = FAKE_OWN_KINDS.find((k) => !used.includes(k));
          if (kind === undefined) throw new Error("This nation already has 3 buildings with units of their own, the most there can be.");
        }
        const address = `$/GFX/Everything/Descriptor_Building_${String(name).trim().replace(/\W+/g, "_")}_${fakeBuildings.length + 1}`;
        fakeBuildings.push({ address, name: String(name).trim(), nation: n, kind, source });
        return { ...(await window.pywebview.api.board(n, lang)), made: address, kind: own ? kind : null };
      },
      board_remove_building: async (n, address, lang = "us") => {
        const at = fakeBuildings.findIndex((b) => b.address === address && b.nation === n);
        if (at < 0) throw new Error(`${address} isn't one of this nation's new buildings`);
        const b = fakeBuildings[at];
        const others = fakeBuildings.some((x) => x !== b && x.nation === n && x.kind === b.kind);
        if (FAKE_OWN_KINDS.includes(b.kind) && !others && fakeBoardTop(n, b.kind, lang).length)
          throw new Error(`Move or take out the units in ${b.name} first: with no building of their own they couldn't be built anywhere.`);
        fakeBuildings.splice(at, 1);
        return { ...(await window.pywebview.api.board(n, lang)), deleted: address };
      },
      board_picker: async (n, lang = "us") => {
        const info = fakeBoardInfo(lang), nationNames = await window.pywebview.api.nations(lang);
        const groups = [n, ...[0, 1, 2, 3, 4, 5, 6].filter((m) => m !== n)].map((m) => ({ nation: m, name: nationNames[m] || String(m),
          units: [...info.values()].filter((i) => i.nation === m && (m === n || i.shows.some(Boolean)))
            .map((i) => ({ address: i.address, name: i.name, kind: i.kind, factory: i.factory, new: i.new,
              here: m === n && i.shows.some(Boolean), taken_out: m === n && !i.shows.some(Boolean) })) }))
          .filter((g) => g.units.length);
        const eras = ["WWI", "WWII", "Cold War", "Modern"].filter((e) => eraHere.has(e)).map((era) => ({ era,
          units: FAKE_ERA_UNITS.filter((u) => u.era === era).map((u) => ({ key: u.key, name: u.name, nation: u.nation,
            kind: u.aircraft ? "air" : "ground", factory: u.factory, added: eraAdded.has(u.key) })) })).filter((e) => e.units.length);
        return { nations: groups, eras };
      },
      board_where: async (address, lang = "us") => {
        const i = fakeBoardInfo(lang).get(address);
        if (!i || !(FAKE_BOARD_ROWS.includes(i.factory) || FAKE_OWN_KINDS.includes(i.factory))) return { nation: null, factory: null, building: null, place: null, count: 0 };
        const row = (await window.pywebview.api.board(i.nation, lang)).rows.find((r) => r.factory === i.factory);
        if (!row) return { nation: i.nation, factory: null, building: null, place: null, count: 0 };
        const at = row.units.findIndex((u) => u.address === address);
        return { nation: i.nation, factory: i.factory, building: row.building, place: at < 0 ? null : at + 1, count: row.units.length };
      },
      board_cards: async (addresses) => Object.fromEntries((addresses || []).map((a) => [a, fakeBoardCard(a)])),
      board_put: async (n, factory, unit = "", era = "", index = null, lang = "us") => {
        if (!current) throw new Error("Pick or make a mod first: the board's changes are saved in it.");
        let address = unit, note = {};
        if (era) {
          const u = FAKE_ERA_UNITS.find((x) => x.key === era);
          address = (await window.pywebview.api.era_unit_add(era, n, factory, u.copies, u.name, 40, null, null)).address;
          fakeBoardOwn.set(address, { shows: [1, 1, 1, 1, 1] });
          note.era = true;
        } else {
          const info = fakeBoardInfo(lang), i = info.get(unit);
          if (!i) throw new Error(`${unit} isn't a unit the board can put in a building`);
          if (i.nation !== n && !i.new) {  // another nation's game unit: a copy, named as it is
            let stem = safeName(i.name) || "New", k = 2;
            while (units.some((u) => u.id === stem) || mine().some((x) => x.id === stem)) stem = `${safeName(i.name)}_${k++}`;
            newUnits.push({ mod: current, id: stem, source: unit, name: i.name, price: 40, nation: n, factory });
            address = newAddress(stem);
            fakeBoardOwn.set(address, { shows: [1, 1, 1, 1, 1], parent: null });
            note.copied = true;
          } else {
            const own = fakeBoardOwn.get(unit) || {};
            nationHidden.delete(unit);
            fakeBoardOwn.set(unit, { ...own, factory, nation: n, shows: own.shows && own.shows.some(Boolean) ? own.shows : null });
            for (const [a, o] of [...fakeBoardInfo(lang)].filter(([, x]) => x.parent === unit)) {  // its research comes along
              if (o.factory === i.factory) fakeBoardOwn.set(a, { ...(fakeBoardOwn.get(a) || {}), factory });
            }
          }
        }
        fakeBoardPlace(n, factory, address, index, lang);
        return { ...(await window.pywebview.api.board(n, lang)), made: address, note };
      },
      board_order: async (n, factory, order, lang = "us") => {
        const all = fakeBoardTop(n, factory, lang), seq = [...(order || []).filter((a) => all.includes(a)), ...all.filter((a) => !(order || []).includes(a))];
        seq.forEach((a, k) => fakeBoardSlot(a, FAKE_BOARD_BASE[factory] + 1 + k * 3, lang));
        return window.pywebview.api.board(n, lang);
      },
      board_move: async (n, address, factory, index = null, lang = "us") => window.pywebview.api.board_put(n, factory, address, "", index, lang),
      board_research: async (n, address, parent = null, lang = "us") => {
        if (!current) throw new Error("Pick or make a mod first: the board's changes are saved in it.");
        const info = fakeBoardInfo(lang), i = info.get(address);
        let up = parent;
        while (up) { if (up === address) throw new Error("A unit can't be researched from one that's researched from it."); up = (info.get(up) || {}).parent; }
        fakeBoardOwn.set(address, { ...(fakeBoardOwn.get(address) || {}), parent: parent || null });
        const p = info.get(parent);
        if (p && p.factory === i.factory) fakeBoardSlot(address, (p.slot || 0) + 1, lang);
        return { ...(await window.pywebview.api.board(n, lang)), note: { dates: false } };
      },
      board_take_out: async (n, address, researched = null, lang = "us") => {
        if (!current) throw new Error("Pick or make a mod first: the board's changes are saved in it.");
        const info = fakeBoardInfo(lang), i = info.get(address);
        const kids = [...info.values()].filter((x) => x.parent === address);
        if (i.new) {
          if (kids.length && researched !== "relink" && researched !== "anyway") return { ...(await window.pywebview.api.board(n, lang)), ask: kids.map((k) => k.name) };
          newUnits.splice(newUnits.findIndex((x) => newAddress(x.id) === address), 1);
        } else {
          fakeBoardOwn.set(address, { ...(fakeBoardOwn.get(address) || {}), shows: [0, 0, 0, 0, 0] });
        }
        for (const k of kids) fakeBoardOwn.set(k.address, { ...(fakeBoardOwn.get(k.address) || {}), parent: i.parent || null });
        return { ...(await window.pywebview.api.board(n, lang)), relinked: kids.map((k) => k.name), deleted: i.new ? address : undefined };
      },
      research_clear_all: async () => {
        const info = fakeBoardInfo("us");
        let n = 0;
        for (const [a, i] of info) if (i.parent) { fakeBoardOwn.set(a, { ...(fakeBoardOwn.get(a) || {}), parent: null }); n += 1; }
        return { cleared: n };
      },
      research_reset_all: async () => {
        let n = 0;
        for (const [a, o] of fakeBoardOwn) {
          if ("parent" in o && !mine().some((x) => newAddress(x.id) === a)) { delete o.parent; n += 1; }  // the game's units only
        }
        return { reset: n };
      },
      // the start screen (StudioApi.start_mods, ruse_studio/startscreen.py): ?fake=fresh shows a fresh install (no mods)
      start_mods: async () => ({ current, mods: mode === "fresh" ? [] : mods.map((m, k) => ({ ...m, folder: m.name,
        changed: Date.now() / 1000 - 3600 * (k + 2), recent: k })) }),
      // era units in the Units tab (StudioApi.era_units_list / era_unit_page / era_start_price / era_unit_add /
      // era_unit_remove / era_sections / era_download, ruse_studio.era_units): a small made-up library, nothing in the
      // mod until added; Modern isn't downloaded until its Download is pressed
      era_sections: async () => ({ message: "", sections: ["WWI", "WWII", "Cold War", "Modern"].map((era) => ({ era,
        units: FAKE_ERA_UNITS.filter((u) => u.era === era).length, size: era === "Modern" ? 1240000000 : 640000000,
        state: eraHere.has(era) ? "current" : "new" })) }),
      era_download: async (era) => { eraHere.add(era); return { job: "era" }; },
      era_units_list: async (era, kind = "all", nation = -1, search = "", group = "all") => {
        if (!eraHere.has(era)) return { library: true, installed: false, types: [], units: [] };
        const code = { USA: 0, Germany: 1, UK: 2, France: 3, Italy: 4, USSR: 5, Russia: 5, Japan: 6, China: 7 };
        let rows = FAKE_ERA_UNITS.filter((u) => u.era === era && ["all", u.aircraft ? "air" : "ground"].includes(kind)
          && (nation === -1 || code[u.nation] === nation));
        const types = [...new Set(rows.map((u) => u.card))].sort();
        if (group.startsWith("type:")) rows = rows.filter((u) => u.card === group.slice(5));
        rows = rows.filter((u) => u.name.toLowerCase().includes((search || "").toLowerCase()));
        return { library: true, installed: true, types, units: rows.map((u) => ({ key: u.key, name: u.name, nation: u.nation, code: code[u.nation],
          card: u.card, kind: u.aircraft ? "air" : "ground", added: eraAdded.get(u.key) || null })) };
      },
      era_unit_page: async (key) => {
        const u = FAKE_ERA_UNITS.find((x) => x.key === key);
        const start = units.filter((g) => g.kind === (u.aircraft ? "air" : "ground") && g.factory !== null).map((g) => ({
          address: E + g.id, name: g.names.us, nation: g.nation, suggested: E + g.id === u.copies,
          same_type: (FAKE_TYPES[g.id] || {}).us === u.card }))
          .sort((x, y) => (y.suggested - x.suggested) || (y.same_type - x.same_type) || x.name.localeCompare(y.name));
        return { ...u, added: eraAdded.get(key) || null, picture: null, start, has_model: u.model !== null,
          ...eraStart(u, u.copies, u.game_nation, u.factory) };
      },
      era_start_price: async (address) => ({ price: (units.find((g) => E + g.id === address) || { price: 0 }).price }),
      era_unit_start: async (key, source, nation, factory) => eraStart(FAKE_ERA_UNITS.find((x) => x.key === key), source,
        nation, factory),
      era_unit_add: async (key, nation, factory, source, name, price, size, researchFrom, researchPrice, researchTime) => {
        if (!current) throw new Error("Pick or make a mod first: an era unit is added to a mod.");
        const u = FAKE_ERA_UNITS.find((x) => x.key === key);
        if (eraAdded.has(key)) throw new Error(`${u.name} is already in this mod`);
        if (size !== null && size !== undefined && !(size >= 0.05 && size <= 20)) {
          throw new Error("Give a size from 0.05 to 20 (1 is as long as the unit it starts from).");
        }
        const made = await window.pywebview.api.new_unit(source || u.copies, name || u.name, price, nation, factory);
        eraAdded.set(key, made.address);
        if (researchFrom) {  // linked as the Upgrade box links it
          upgradeEdits.set(made.address, researchFrom);
          researchEdits.set(`${made.address}|UpgradePrice`, Math.round(researchPrice ?? 50));
          researchEdits.set(`${made.address}|UpgradeTime`, Math.round(researchTime ?? 50));
        }
        return { address: made.address, name: made.name, model: null, model_note: u.model === null ? "no_model" : (u.fits ? "" : "no_fit"),
          size: u.model === null ? null : size, research_from: researchFrom || null };
      },
      era_unit_remove: async (key, researched) => {
        const address = eraAdded.get(key);
        const research = researchGone(address, researched);  // before anything goes
        if (research.ask) return { removed: null, ask: research.ask };
        eraAdded.delete(key);
        await window.pywebview.api.delete_unit(address, "anyway");
        return { removed: address, ...research };
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
        : fakeJobs.has(id) ? { ...fakeJobs.get(id), lines: fakeJobs.get(id).lines.slice(since || 0), count: fakeJobs.get(id).lines.length }
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
        if (preset && !["blank_terrain", "blank_ocean"].includes(preset)) throw new Error(`There's no '${preset}' to start from.`);
        const own = (name.normalize("NFKD").replace(/[̀-ͯ]/g, "").match(/[A-Za-z0-9]+/g) || [])
          .map((x) => x[0].toUpperCase() + x.slice(1)).join("") || "NewMap";
        const kind = ((FAKE_ENTRIES[m.copy_of || pack] || []).find((e) => e.name === entry) || {}).kind || "battles";
        fakeMaps.splice(at + 1, 0, { ...m, pack: own, names: [name], paths: [own], file: `DataMap${own}_v09.dat`,
          kinds: [kind === "battles" ? "skirmish" : kind], titles: { us: [name], fr: [name], sc: [name] },
          copy_of: m.copy_of || pack, blank: preset ? true : Boolean(m.blank) });  // StudioApi.maps "blank"
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
      map_models: async () => fakeMapModels(),  // made-up models for the made-up types (fakeMapModels)
      // Map Paint's textures (rusemod.groundtex): a few made-up ones, each a two-colour checker
      ground_textures: async () => ({ base: "", groups: ["grass", "fields", "earth", "sand", "rock", "snow", "water",
        "roads", "town", "damage", "marks", "other"], textures: fakeTextures.map(([ref, group, words, a]) => ({
        ref, theatres: ["france"], group, words, period: 8192, see_through: false, thumb: fakeChecker(a, "#222") })) }),
      ground_texture: async (ref) => {
        const t = fakeTextures.find((x) => x[0] === ref), own = fakeOwnPictures.find((p) => p.ref === ref);
        const pal = fakePalette.find((p) => `swatch:dday:${p[0]}` === ref);
        if (pal) return { ref, period: pal[3] * 260, n: 8, png: fakeChecker(pal[4], "#222"), mirrored: true };
        return { ref, period: own && own.period ? own.period : ref.startsWith("map:") ? 81920 : 8192, n: 8,
          png: own ? own.thumb : fakeChecker(t ? t[3] : "#9a8a5a", "#4a3a2a"), mirrored: false };
      },
      // Paint by shape (rusemod.repaint): the preview has no ground brushes' result to work it out from
      repaint_preview: async () => ({ strokes: [], said: "no ground moved enough (16 m squares, 0 strokes)" }),
      // brush patterns (rusemod.brushmask): made-up ones, waves and dots, 64 x 64
      brush_masks: async () => {
        const one = (f) => btoa(String.fromCharCode(...Array.from({ length: 4096 }, (_, k) => {
          const i = k % 64, j = Math.floor(k / 64);
          return Math.max(0, Math.min(255, Math.round(255 * f(i, j))));
        })));
        const wave = (i, j) => 0.5 + 0.25 * Math.sin(i / 5) + 0.25 * Math.cos(j / 7);
        return { size: 64, turns: [[1, 0], [0, 1], [-1, 0], [0, -1]], edge: ["ragged"], rag_in: 0.6, masks: {
          noise: one(wave), splatter: one((i, j) => ((i * 7 + j * 13) % 23 < 4 ? 1 : 0)), ragged: one(wave),
          tufts: one((i, j) => ((i * 5 + j * 11) % 9 < 2 ? 1 : 0.25)), ridge: one((i, j) => 1 - Math.abs(Math.sin(i / 6 + j / 9))) } };
      },
      ground_palette: async () => ({ swatches: fakePalette.map(([name, label, kind, metres, colour]) => ({
        ref: `swatch:dday:${name}`, theme: "dday", name, label, map: "M04_Cotentin", kind, period: metres * 260,
        thumb: fakeChecker(colour, "#222") })) }),
      map_overview: async (pack) => ({ pack, picture: fakeChecker("#6a8a4a", "#c8b070"), bounds: [0, 0, 1000000, 1000000] }),
      map_texture: async (pack, x, y) => ({ ref: `map:${pack}:${Math.round(x)}:${Math.round(y)}`, period: 81920, n: 8,
        png: fakeChecker("#c8b070", "#8a7040") }),
      ground_pictures: async () => ({ pictures: fakeOwnPictures, folder: "mods/test/files/ground" }),
      add_ground_picture: async (name, picture, metres, credit) => {
        const ref = `file:${String(name).replace(/\.\w+$/, "")}.png`;
        fakeOwnPictures.push({ ref, name: ref.slice(5, -4), thumb: picture, period: metres ? metres * 260 : 8192,
          ...(metres ? { metres } : {}), ...(credit ? { credit } : {}) });
        return { pictures: fakeOwnPictures, folder: "mods/test/files/ground", ref };
      },
      online_textures: async (source, words) => {
        await new Promise((r) => setTimeout(r, 300));  // (a site's list takes a moment)
        if (source === "usgs") return { source, licence: "Public domain", metres: [160, 320, 640, 1280], default: 320,
          items: fakePlaces.map(([id, name, lat, lon]) => ({ id, name, lat, lon, group: "fields" })) };
        const find = String(words || "").toLowerCase();
        return { source, licence: "CC0", words, items: fakeOnline[source].filter(([, name]) => source !== "ambientcg"
          || !find || name.toLowerCase().includes(find)).map(([id, name, metres, a]) => ({ id, name, metres,
          thumb: fakeChecker(a, "#333"), tags: [], author: source === "ambientcg" ? "ambientCG" : "Rob Tuytel" })) };
      },
      online_texture: async (source, item, metres, where) => {
        await new Promise((r) => setTimeout(r, 500));  // (a download takes a moment)
        if (source === "usgs") {
          const p = fakePlaces.find((x) => x[0] === item);
          if (!p && !/^\s*-?\d+(\.\d+)?\s*,\s*-?\d+(\.\d+)?\s*$/.test(where || "")) {
            throw new Error("type a latitude and a longitude, like 38.2, -98.4");
          }
          return { name: `${p ? p[1].replace(/[()]/g, "") : `US photo ${where}`} ${metres}m`,
            picture: fakeChecker(p ? p[4] : "#7a8a5a", "#5a6a3a"), metres, credit: { source: "USGS National Map, NAIP imagery",
              author: "USDA Farm Production and Conservation, through the USGS", licence: "Public domain", url: "" } };
        }
        const t = fakeOnline[source].find((x) => x[0] === item);
        return { name: t[1], picture: fakeChecker(t[3], "#333"), metres: t[2],
          credit: { source: source === "ambientcg" ? "ambientCG" : "Poly Haven",
            author: source === "ambientcg" ? "ambientCG" : "Rob Tuytel", licence: "CC0", url: "" } };
      },
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
      unsaved: async (ask) => {  // what the window would ask before closing (kept for a look: window.fakeCloseAsk)
        window.fakeCloseAsk = ask && ask.text ? ask : null;
        return { asking: Boolean(window.fakeCloseAsk) };
      },
      closing_check: async () => window.fakeCloseAsk || null,
      scenery: async (pack) => ({ objects: current ? (placed.get(`${current}|${pack}`) || []) : [],
        erase: current ? (erased.get(`${current}|${pack}`) || []) : [],
        own: current ? (owned.get(`${current}|${pack}`) || []) : [], saved: null, mod: current }),
      map_objects_at: async (pack, x, y, radius = 2600) => ({
        objects: fakeOwnObjects(pack).map((o) => ({ ...o, distance: Math.hypot(o.x - x, o.y - y) }))
          .filter((o) => o.distance <= Math.min(radius, 26000)).sort((a, b) => a.distance - b.distance) }),
      map_objects_in: async (pack, x0, y0, x1, y1) => {
        const [xa, xb] = [x0, x1].sort((a, b) => a - b), [ya, yb] = [y0, y1].sort((a, b) => a - b);
        if (Math.hypot(xb - xa, yb - ya) / 2 > 130000) {
          throw new Error("That box is too big to pick from: at most 1,000 m corner to corner. Drag a smaller one, or use the Erase brush for a whole area.");
        }
        const objects = fakeOwnObjects(pack).filter((o) => o.x >= xa && o.x <= xb && o.y >= ya && o.y <= yb)
          .map((o) => ({ ...o, distance: Math.hypot(o.x - (xa + xb) / 2, o.y - (ya + yb) / 2) }));
        return { objects: objects.slice(0, 2000), more: objects.length > 2000 };
      },
      scenery_own: async (pack, rows) => {  // the whole list, each building opening its old ground (made-up reach)
        if (!current) throw new Error("Pick or make a mod first: what you place is saved in it.");
        const groups = new Map(fakeOwnObjects(pack).map((o) => [o.type, o.group]));
        const own = rows.map((r) => {
          const building = groups.get(r.type) === "building";
          return { gone: false, to_x: 0, to_y: 0, turn: 0, size: 1, lift: 0, ...r, solid: building && !r.gone,
            open: r.open || (building ? 1800 * (r.size || 1) : 0) };
        });
        owned.set(`${current}|${pack}`, own);
        return { own, saved: own.length ? `${current}/maps/${pack}/scenery.toml` : null };
      },
      scenery_change: async (pack, changes) => {  // [old, new] pairs; new null takes it off
        if (!current) throw new Error("Pick or make a mod first: what you place is saved in it.");
        const key = `${current}|${pack}`, list = (placed.get(key) || []).slice();
        const same = (a, b) => ["type", "x", "y", "turn", "size"].every((k) => a[k] === b[k]);
        let changed = 0;
        for (const [old, now] of changes) {
          const at = list.map((p) => same(p, old)).lastIndexOf(true);
          if (at < 0) continue;
          changed++;
          if (now) list[at] = now; else list.splice(at, 1);
        }
        placed.set(key, list);
        return { count: list.length, changed, saved: `${current}/maps/${pack}/scenery.toml` };
      },
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
      // the map mod's own models (StudioApi.assets, asset_import, …): kept per mod; "picking a file" picks a made-up
      // boulder.glb, drawn as the made-up basket
      assets: async () => fakeAssetList(),
      asset_import: async (kind, file, name, size = 1, twoSided = false, source = "", author = "", licence = "",
        replaceIt = false, solid = false) => {
        if (!current) throw new Error("Pick or make a mod first: the model is saved in it.");
        await new Promise((r) => setTimeout(r, 400));  // the real one reads the file and makes its versions
        const n = (name || "boulder").split(/[^A-Za-z0-9]+/).filter(Boolean).map((p) => p[0].toUpperCase() + p.slice(1)).join("");
        const list = fakeAssets.get(current) || [];
        if (!replaceIt && list.some((a) => a.name === n)) return { exists: n, file: file || "D:/models/boulder.glb", asset: null, ...fakeAssetList() };
        if (licence && !["CC0", "CC-BY"].includes(licence)) throw new Error(`boulder.glb: a model taken from others must be CC0 or CC-BY (this one says ${licence}); leave the licence empty for a model of your own`);
        const group = { rock: "prop", prop: "prop", plant: "vegetation", tree: "vegetation" }[kind];
        const asset = { name: n, type: `TypeWarrior/R2_${n}`, kind, group, label: kind, size: Number(size) || 1,
          two_sided: Boolean(twoSided), solid: Boolean(solid), metres: [1.3, 1.8, 1.0],
          credit: Object.fromEntries(Object.entries({ source, author, licence }).filter(([, v]) => v)),
          file: `${n}.glb`, triangles: 1180, versions: { medium: { file: `${n}_medium.glb`, triangles: 590 },
            far: { file: `${n}_far.glb`, triangles: 118 } } };
        fakeAssets.set(current, list.filter((a) => a.name !== n).concat([asset]));
        return { asset, ...fakeAssetList() };
      },
      asset_change: async (name, size, twoSided, source, author, licence, solid = null) => {
        const a = (fakeAssets.get(current) || []).find((x) => x.name === name);
        if (!a) throw new Error(`The mod has no model called '${name}'.`);
        Object.assign(a, { size: Number(size) || a.size, two_sided: Boolean(twoSided), solid: solid === null ? a.solid : Boolean(solid),
          credit: Object.fromEntries(Object.entries({ source, author, licence }).filter(([, v]) => v)) });
        return fakeAssetList();
      },
      asset_remove: async (name, placedToo = false) => {
        const t = `TypeWarrior/R2_${name}`, where = {};
        for (const [key, list] of placed) {
          const [mod, pack] = key.split("|"), n = list.filter((o) => o.type === t).length;
          if (mod === current && n) where[pack] = n;
        }
        if (Object.keys(where).length && !placedToo) return { placed: where, ...fakeAssetList() };
        for (const pack of Object.keys(where)) placed.set(`${current}|${pack}`, placed.get(`${current}|${pack}`).filter((o) => o.type !== t));
        fakeAssets.set(current, (fakeAssets.get(current) || []).filter((a) => a.name !== name));
        return fakeAssetList();
      },
      asset_models: async () => {
        const made = fakeMapModels(), models = {};
        for (const a of fakeAssetList().assets) models[a.type] = made.index.models[4];
        return { base: "", index: { bin: made.index.bin, models, textures: {} } };
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
      // the Sectors brush (StudioApi.sector_*): a 64 x 64 grid over the map; the map's own sectors two halves
      sector_view: async (pack, file, outlines) => fakeSectorView(pack, file, outlines),
      sector_paint: async (pack, file, sector, radius, points, shape) => {
        if (!(sector >= -1 && sector <= 254)) throw new Error("That stroke can't be saved (sector is a whole number from 0 to 254).");
        fakeSectors(pack, file).strokes.push({ sector, radius, points, shape });
        return fakeSectorView(pack, file);
      },
      sector_area: async (pack, file, areas) => {   // a shape edit: the sectors it changes, kept together for Undo
        const f = fakeSectors(pack, file), group = f.strokes.reduce((g, s) => Math.max(g, s.group || 0), 0) + 1;
        for (const a of areas) {
          if (!(a.sector >= -1 && a.sector <= 254) || (a.sector === -1 && !(a.points || []).length)) {
            throw new Error("That shape can't be saved (sector is a whole number from 0 to 254, or -1: no sector, with corners).");
          }
          f.strokes.push({ sector: a.sector, area: a.points || [], group });
        }
        return fakeSectorView(pack, file, true);
      },
      sector_undo: async (pack, file) => {
        const f = fakeSectors(pack, file);
        if (!f.strokes.length) throw new Error("There's no painted sector stroke to take back.");
        const last = f.strokes.pop();
        while (last.group && f.strokes.length && f.strokes[f.strokes.length - 1].group === last.group) f.strokes.pop();
        return fakeSectorView(pack, file, Boolean(last.group));
      },
      sector_auto: async (pack, file, metres, seed = 0) => {   // over what was there (Undo brings it back)
        if (!(metres >= 500 && metres <= 40000)) throw new Error("Those sectors can't be made (sectors are 500 m to 40 km across).");
        const f = fakeSectors(pack, file), last = f.strokes[f.strokes.length - 1];
        if (last && last.auto) f.strokes.pop();
        f.strokes.push({ auto: metres, seed });
        return fakeSectorView(pack, file);
      },
      sector_clear: async (pack, file) => { fakeSectors(pack, file).strokes = []; return fakeSectorView(pack, file); },
      sector_start: async (pack, file, empty) => { fakeSectors(pack, file).empty = Boolean(empty); return fakeSectorView(pack, file); },
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
      // with the units researched from one taken out after the warning (StudioApi._research_problems)
      check_mod: async () => ({ mod: current, problems: current ? checkProblems.concat([...upgradeEdits.keys()]
        .filter((a) => upgradeOf(a, "us").parent_gone)
        .map((a) => ({ file: null, set_aside: false, unit: a, problem: `${(mine().find((n) => newAddress(n.id) === a)
          || { name: a.slice(E.length) }).name} is researched from a unit that's no longer in the mod, so the build stops `
          + "on it. Pick another unit to research it from in its Upgrade and research box, or none." }))) : [] }),
      rename_map_folder: async () => ({ mod: current, problems: checkProblems }),
      set_aside: async (file) => {
        const p = checkProblems.find((x) => x.file === file);
        if (!p) throw new Error(`${file} isn't one of this mod's map files`);
        checkProblems = checkProblems.filter((x) => x !== p);
        return { mod: current, problems: checkProblems, kept: `${current}/${file.replace(".toml", ".broken.toml")}` };
      },
      fix_problem: async (fix) => {
        if (fix.fix === "set_aside") return window.pywebview.api.set_aside(fix.file);
        const p = checkProblems.find((x) => x.file === fix.file && x.plain.n === fix.n);
        if (!p) throw new Error(`${fix.file} isn't one of this mod's map files`);
        checkProblems = checkProblems.filter((x) => x !== p);
        const name = fix.file.split("/").pop();
        return { mod: current, problems: checkProblems, message: `Fixed. ${name} as it was is kept beside it, as ${name.replace(".toml", ".before-fix.toml")}.` };
      },
      open_mod_in_folder: async () => ({ opened: current }),
      scenario_spawn_many: async (pack, file, unit, points, camp = -1, rotation = 0, trucks = null) => {
        if (trucks !== null && unit !== "DalleBatimentDepot") throw new Error("Only a supply depot has trucks.");
        for (const [x, y] of points) {
          scenEdits(pack).spawns.push({ file, what: unit.replace(E, "Unit_"), x, y, camp, rotation, trucks });
        }
        return withScenarioEdits(pack);
      },
      // a spawn the mod adds: its side, a depot's trucks, its turn (StudioApi.scenario_spawn_set)
      scenario_spawn_set: async (pack, number, field, value) => {
        const sp = scenEdits(pack).spawns[number];
        if (!sp) throw new Error("that spawn isn't in the mod any more");
        if (field === "trucks" && sp.what !== "DalleBatimentDepot") throw new Error("Only a supply depot has trucks.");
        if (field === "trucks" && !(Number.isInteger(value) && value >= 0 && value <= 2147483647)) {
          throw new Error("A depot's trucks are a whole number from 0 to 2,147,483,647.");
        }
        sp[field === "rotation" ? "rotation" : field] = Number(value);
        return withScenarioEdits(pack);
      },
      // every depot of a scenario at once (StudioApi.scenario_depots): trucks each, times the game's, or back
      scenario_depots: async (pack, file, trucks = null, times = null) => {
        const e = scenEdits(pack), s = baseScenarios().scenarios.find((x) => x.file === file);
        e.changes = e.changes || [];
        let count = 0;
        const each = (game) => trucks !== null ? trucks : times !== null ? Math.round(game * times) : null;
        (s ? s.items : []).forEach((it, item) => {
          if (it.kind !== "Spawn" || it.what !== "DalleBatimentDepot") return;
          let c = e.changes.find((x) => x.file === file && x.item === item);
          if (!c) { c = { file, item, values: {} }; e.changes.push(c); }
          const n = each(it.trucks || 0);
          if (n === null || n === (it.trucks || 0)) delete c.values.trucks; else c.values.trucks = n;
          count += 1;
        });
        e.changes = e.changes.filter((c) => Object.keys(c.values).length);
        for (const sp of e.spawns) {
          if (sp.file !== file || sp.what !== "DalleBatimentDepot") continue;
          const n = each(25);
          sp.trucks = n === null || n === 25 ? null : n;
          count += 1;
        }
        return { ...withScenarioEdits(pack), depots: count };
      },
      // what a depot's trucks are worth (StudioApi.depot_money): the Economy tab's money a truck and trucks a convoy
      depot_money: async (pack = null) => {
        const value = (prop, game) => economyEdits.has(`normal|${prop}`) ? economyEdits.get(`normal|${prop}`) : game;
        const rule = pack ? (depotRules.get(pack.toLowerCase()) || depotRules.get("all")) : null;
        return { ready: mode !== "noindex", usual: 25, shipped: [15, 72], most: 2147483647,
          per_truck: value("QteDeviseParCamion", 3), per_truck_mine: economyEdits.has("normal|QteDeviseParCamion"),
          per_convoy: value("NbCamionParConvoi", 3), per_convoy_mine: economyEdits.has("normal|NbCamionParConvoi"),
          rule: rule ? { ...rule } : null };
      },
      // the Economy tab's Depots on the maps (StudioApi.economy_depots / economy_depots_set): all maps or one
      economy_depots: async () => ({ can: Boolean(current),
        rules: [...depotRules.values()].sort((a, b) => (a.map !== "all") - (b.map !== "all") || a.name.localeCompare(b.name)),
        maps: fakeMaps.map((m) => ({ pack: m.pack, name: m.names[0] })), money: await window.pywebview.api.depot_money() }),
      economy_depots_set: async (where, trucks = null, times = null) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        if (trucks !== null && times !== null) throw new Error("Give the depots a number of trucks, or a times, not both.");
        const key = String(where).toLowerCase();
        if (trucks === null && times === null) depotRules.delete(key);
        else {
          const m = fakeMaps.find((x) => x.pack.toLowerCase() === key);
          depotRules.set(key, { map: key === "all" ? "all" : m ? m.pack : where, name: m ? m.names[0] : where,
            trucks, times });
        }
        return window.pywebview.api.economy_depots();
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
      // Map size (StudioApi.map_size / set_map_size): the made-up island is 4 x 4 squares; a mod's size kept per map
      map_size: async (pack) => fakeMapSize(pack),
      set_map_size: async (pack, across, down, firstX = 0, firstY = 0) => {
        if (!current) throw new Error("Pick or make a mod first: the map's size is saved in it.");
        for (const n of [across, down]) {
          if (!Number.isInteger(n) || n % 2 || n < 2 || n > 128) throw new Error("The map's size must be two even whole numbers from 2 to 128.");
        }
        mapSizes.set(`${current}|${pack}`, across === 4 && down === 4 ? null : [across, down]);
        return fakeMapSize(pack);
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
