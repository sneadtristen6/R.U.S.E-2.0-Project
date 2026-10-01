// A made-up StudioApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=noindex shows the "no index yet" state, ?fake=nomod the Studio before any mod is picked, ?fake=notfound no
// game found, ?fake=testfails a Test in game that fails, with its Troubleshoot link; ?fake=backup, ?fake=oldbackup,
// ?fake=nospace and ?fake=running the clean game backup's states, in Settings). Only English, French
// and Chinese words are included here; the real Studio has all ten languages. It does nothing in the real Studio window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const prefs = {};  // what the real app keeps in settings.json (rusemod.home.PrefsCalls)
  const words = {
    us: { update_out: "{app} {version} is out.", update_now: "Update", whats_new: "What's new", update_progress: "Downloading the update… {pct}", update_installing: "Installing: {app} closes and opens again by itself.", update_repo: "(This copy runs from the repo: update it with git pull.)", update_failed: "The update didn't work: {why}",
      language: "Language", game_names: "Code names", search: "Search", all: "All", ground: "Ground",
      infantry: "Infantry", air: "Air", buildings: "Buildings", units: "{n} units", parts: "Parts", uses: "Uses",
      own_part: "its own", shared_part: "shared with other units", used_by: "Used by", copy_address: "Copy address",
      no_index: "No game index yet. Build it once (about a minute).", build_index: "Build the index",
      pick_unit: "Pick a unit on the left.", mod: "Mod", new_mod: "New mod…", open_folder: "Open a mod folder…",
      export_mod: "Export mod…", version: "Version", author: "Author", description: "Description", export: "Export",
      export_help: "One file to share: the mod folder packed. The version, author and description are kept in the mod.",
      mod_name: "Name of the new mod", create: "Create", cancel: "Cancel", close: "Close",
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
      brush_flatten: "Flatten", brush_level: "Level", scen_show: "Scenario", maps_all: "All maps", tip_map_kind: "Show only the maps the game offers this way: skirmish, Operations, campaign, demo or test.", settings_tab: "Settings", tip_tab_settings: "Language, keys, the game folder and updates.", settings_title: "Settings", set_language_title: "Language", set_language_help: "Code names show the game's own names; any of the game's ten languages shows the names players know.", set_keys_title: "Map view keys", set_keys_help: "Click a key, then press the one you want.", set_game_title: "Game folder", set_game_path: "R.U.S.E. is in {path}.", set_game_none: "R.U.S.E. wasn't found. Pick its folder.", set_game_change: "Choose folder…", set_updates_title: "Updates", set_updates_latest: "This is RUSE Studio {version}. It looks for a newer one each time it opens.", set_updates_check: "Check now", set_updates_checking: "Looking for a newer version…", scen_kind_skirmish: "Battles", scen_kind_operation: "Operation", scen_kind_campaign: "Campaign", scen_kind_demo: "Demo", scen_kind_test: "Test setups", scen_kind_unused: "Not in any menu", tip_scen_show: "Show the scenario's zones, starting points (pillars in each alliance's colour), spawns (white diamonds) and town names.", tip_scen_pick: "The map's scenarios: the skirmish one first, then challenges and campaign chapters.", scen_main: "main", scen_none: "This map has no scenario.", scen_stats: "{zones} zones · {starts} starting points · {spawns} spawns · {names} names", scen_zone: "Zone", scen_start: "Starting point, alliance {n}", scen_spawn: "Spawn", tip_panel_grip: "Drag to move this panel. Double-click to put it back.", tip_panel_fold: "Fold this panel away.", tip_panel_unfold: "Open this panel again.", scen_where: "In the game: {where}", scen_players: "{n} players", tip_scen_where: "Start this in the game to see what you changed on this setup (after Test in game).", dock_roads: "Roads", tip_dock_roads: "Draw new roads: supply trucks follow them. Ends snap onto the roads they touch.", road_straight: "Straight", road_curve: "Curve", road_free: "Freeform", tip_road_straight: "A straight road: click where it starts, then where it ends.", tip_road_curve: "A curved road: click the start, then the bend it's pulled toward, then the end.", tip_road_free: "A road that follows your clicks: click along the way, then double-click or press Enter to finish.", road_help_straight: "Click where the road starts, then where it ends. An end near a road snaps onto it (a ring shows where).", road_help_curve: "Click the start, then the bend, then the end.", road_help_free: "Click along the road's way; double-click, press Enter or click Finish to end it. Esc drops it.", road_finish: "Finish", tip_road_finish: "End the road at its last point.", tip_road_undo: "Take back the last road (Ctrl+Z).", road_count: "{n} new road(s) on this map", scen_seat: "team {n}, place {p}", scen_start_tool: "Add starting point", tip_scen_start: "A new player's starting point: pick the team, then click the map. More players need one each.", scen_team_n: "Team {n}", tip_scen_team: "The team it's for: in a 4v4, teams 1 and 2 each need places 1 to 4.", scen_start_help: "Click the map where this team's next player starts (open ground, away from the others).", scen_start_place: "Starting point: team {n}, place {p}", scen_players_label: "Players", tip_scen_players: "How many players this map takes in this mod (up to 8). Each needs a starting point.", scen_players_game: "{n} (game)", scen_players_missing: "{n} players need a starting point at: {list} (scenario {where}). Add them with Add starting point.", scen_players_ok: "Every player has a starting point.", scen_players_none: "This map isn't played online, so its player count can't change.", road_part: "this part {len}", road_total: "{len} in all", road_note: "Supply trucks follow new roads, and they're painted on the ground (both proven in the game). A road over water gets a bridge.", roads_show: "Roads", tip_roads_show: "Show the map's roads in gold, on the ground as you shape it.", check_rename: "Rename to {name}", tip_check_rename: "Renames the map's folder in your mod to the pack name the game uses. Nothing inside it changes.", report_problem: "Report a problem", tip_report_problem: "Opens a bug report in your browser, with the app and its version filled in. You read it and post it yourself.", report: "Report", tip_report: "Report this as a bug: your browser opens a report with this message filled in (paths without your user name).", set_help_title: "Help & community", set_help_help: "The wiki is the field manual: a guide for every tool. Ask, suggest, show your mods or report a bug in Discussions.", help_wiki: "Wiki (field manual)", tip_help_wiki: "Opens the wiki in your browser: step-by-step guides for every tool.", help_discussions: "Discussions", tip_help_discussions: "Opens Discussions in your browser: questions, ideas, mods and maps.", check_title: "Mod check: {n} problem(s). The game build would stop here.", check_set_aside: "Set aside", tip_check_set_aside: "Rename the file <name>.broken.toml beside it: the build skips it, nothing is lost, and the map starts clean.", check_aside_done: "Set aside as {file}.", check_stop: "Fix the mod's problems first (the bar at the top).", scen_count: "How many", tip_scen_count: "How many one click adds, in the shape picked below.", formation_line: "Line", formation_column: "Column", formation_wedge: "Wedge", formation_box: "Box", formation_circle: "Circle", tip_scen_formation: "The shape they stand in. It faces up the screen, its middle where you click; the dots show where each goes.", tip_scen_gap: "How far apart they stand, in metres.", tip_maps_hide: "Fold the map list away: more room for the map.", tip_maps_show: "Show the map list again.", dock_terrain: "Ground", dock_movement: "Movement", tip_dock_terrain: "Hills, craters, plateaus, ramps: shape the ground.", tip_dock_water: "Lakes and rivers: flood the ground up to a level, or dry it up.", tip_dock_cover: "Where units hide: paint cover, take it away, or cover a whole town in one click.", tip_dock_movement: "Where units go: close ground to every unit, to infantry or to vehicles.", tip_dock_building: "Place the map's own buildings: one, an area, or a row.", tip_dock_prop: "Place the map's own objects: fences, crates, wrecks and the like.", tip_dock_vegetation: "Plant the map's own trees: one, a wood, or a tree line.", tip_dock_scenario: "The picked scenario: move starting points and spawns, or add units and buildings.", brush_block: "Block", brush_block_infantry: "Block infantry", brush_block_vehicles: "Block vehicles", tip_brush_block: "No unit can go here: they plan around it (a cliff, a lake, a wall). Proven in the game.", tip_brush_block_infantry: "Infantry can't go here; vehicles still can.", tip_brush_block_vehicles: "Vehicles can't go here; infantry still can (like a wood).", move_show: "Where units go", tip_move_show: "Show where units can go: red is closed to every unit (water, cliffs, off the map), yellow to vehicles only (woods).", place_solid: "Solid", tip_place_solid: "Units can't go through the buildings you place (proven in the game). Off: they're only drawn.", brush_cover: "Cover", brush_uncover: "Uncover", brush_town: "Town", tip_brush_cover: "Paints cover: units there are hidden, as in a wood (green). Proven in the game.", tip_brush_uncover: "Takes cover away: units there can be seen, even in a wood.", tip_brush_town: "Click a town: cover goes around every building of it (Size: how far around each), so units hide in it.", cover_show: "Cover", tip_cover_show: "Show where units hide (green): the map's woods and towns, and what this mod paints.", town_none: "No building here: click on a town or a group of buildings.", town_done: "Cover around {n} buildings.", group_ap: "AP shells (anti-tank)", group_he: "HE shells (explosive)", group_aa: "Anti-aircraft", group_mg: "Machine guns", group_infantry_weapons: "Infantry weapons", group_antitank_weapons: "Infantry anti-tank", group_bombs: "Bombs", group_rockets: "Rockets", scen_move_tool: "Move", tip_scen_move: "Move a starting point or a spawn: click it, then click where it goes. Saved in the mod.", scen_spawn_tool: "Add unit", tip_scen_spawn: "Add a unit or building that appears when this scenario starts: pick its kind, type and name, pick a side, then click the map.", tip_scen_kind: "Buildings, ground units, infantry or planes.", tip_scen_unit: "The unit or building, listed by nation.", tip_scen_camp: "The side it belongs to. Which number is which player: test it in the game.", scen_side_neutral: "Neutral", tip_scen_camp_skirmish: "A skirmish game spawns only neutral items, like the map's depots: a unit for a player's side would never appear, so this scenario takes Neutral only.", scen_side_n: "Side {n}", scen_pick_item: "Click a starting point or a spawn to move it.", scen_pick_place: "Now click where it goes: {what}.", scen_remove: "Remove", scen_put_back: "Put back", scen_spawn_help: "Click the map where it appears.", scen_pick_unit: "Pick a unit or building first.", scen_moved: "moved in this mod", scen_mine: "added in this mod", group_all: "All types", tip_group: "What it's for: a building's job (HQ, money, factory, fort, fake) or the factory that builds a unit.", group_hq: "HQ", group_money: "Money (depots, admin)", group_factory: "Factories", group_fort: "Forts and defenses", group_fake: "Fake (decoys)", group_barracks: "Barracks", group_armor: "Armor", group_antitank: "Anti-tank", group_artillery: "Artillery", group_prototype: "Prototypes", group_airfield: "Airfield", group_turret: "Fort guns", group_other: "Other", brush_water: "Water", brush_drain: "Drain", tip_brush_water: "Floods the ground below a water level: the height where you start dragging, plus Strength. The ground itself is unchanged.", tip_brush_drain: "Puts the water back to the map's base level: lakes and rivers there dry up.", tip_brush_level: "Paints the ground flat at one height: the height where you start dragging. Start on ground at the height you want.", brush_smooth: "Smooth", brush_size: "Size", brush_strength: "Strength",
      brush_look: "Look around", brush_undo: "Undo",
      brush_help: "Click or drag on the ground to paint · middle-drag to turn · right-drag to move · wheel to zoom",
      brush_count: "Strokes on this map: {n}", brush_note: "Saved in the mod. \"Test in game\" builds it into the map.",
      brush_ramp: "Ramp", ramp_help: "Click where the ramp starts, then where it ends. Esc cancels.",
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
      brush_plateau: "Plateau", brush_flatten: "Aplanir", brush_level: "Niveler", scen_show: "Scénario", maps_all: "Toutes les cartes", tip_map_kind: "Afficher seulement les cartes que le jeu propose ainsi : escarmouche, opérations, campagne, démo ou test.", settings_tab: "Réglages", tip_tab_settings: "Langue, touches, dossier du jeu et mises à jour.", settings_title: "Réglages", set_language_title: "Langue", set_language_help: "Les noms de code montrent les noms internes du jeu ; chacune des dix langues montre les noms que voient les joueurs.", set_keys_title: "Touches de la vue carte", set_keys_help: "Cliquez sur une touche, puis appuyez sur celle que vous voulez.", set_game_title: "Dossier du jeu", set_game_path: "R.U.S.E. est dans {path}.", set_game_none: "R.U.S.E. est introuvable. Choisissez son dossier.", set_game_change: "Choisir le dossier…", set_updates_title: "Mises à jour", set_updates_latest: "Ceci est RUSE Studio {version}. Il cherche une version plus récente à chaque ouverture.", set_updates_check: "Vérifier", set_updates_checking: "Recherche d'une version plus récente…", scen_kind_skirmish: "Batailles", scen_kind_operation: "Opération", scen_kind_campaign: "Campagne", scen_kind_demo: "Démo", scen_kind_test: "Réglages de test", scen_kind_unused: "Dans aucun menu", tip_scen_show: "Afficher les zones du scénario, les points de départ (piliers à la couleur de chaque alliance), les apparitions (losanges blancs) et les noms de villes.", tip_scen_pick: "Les scénarios de la carte : l'escarmouche d'abord, puis les défis et les chapitres de campagne.", scen_main: "principal", scen_none: "Cette carte n'a pas de scénario.", scen_stats: "{zones} zones · {starts} points de départ · {spawns} apparitions · {names} noms", scen_zone: "Zone", scen_start: "Point de départ, alliance {n}", scen_spawn: "Apparition", tip_panel_grip: "Glissez pour déplacer ce panneau. Double-cliquez pour le remettre en place.", tip_panel_fold: "Replier ce panneau.", tip_panel_unfold: "Rouvrir ce panneau.", scen_where: "En jeu : {where}", scen_players: "{n} joueurs", tip_scen_where: "Lancez ceci en jeu pour voir vos changements sur cette configuration (après Tester en jeu).", dock_roads: "Routes", tip_dock_roads: "Tracez de nouvelles routes : les camions de ravitaillement les suivent. Les extrémités s'accrochent aux routes touchées.", road_straight: "Droite", road_curve: "Courbe", road_free: "Libre", tip_road_straight: "Une route droite : cliquez là où elle commence, puis là où elle finit.", tip_road_curve: "Une route courbe : cliquez le début, puis le point vers lequel elle se courbe, puis la fin.", tip_road_free: "Une route qui suit vos clics : cliquez le long du tracé, puis double-cliquez ou appuyez sur Entrée.", road_help_straight: "Cliquez là où la route commence, puis là où elle finit. Une extrémité près d'une route s'y accroche (un cercle le montre).", road_help_curve: "Cliquez le début, puis la courbe, puis la fin.", road_help_free: "Cliquez le long du tracé ; double-cliquez, Entrée ou Terminer pour finir. Échap l'annule.", road_finish: "Terminer", tip_road_finish: "Terminer la route à son dernier point.", tip_road_undo: "Retirer la dernière route (Ctrl+Z).", road_count: "{n} nouvelle(s) route(s) sur cette carte", scen_seat: "équipe {n}, place {p}", scen_start_tool: "Ajouter un point de départ", tip_scen_start: "Un nouveau point de départ de joueur : choisissez l'équipe, puis cliquez sur la carte. Plus de joueurs en demandent un chacun.", scen_team_n: "Équipe {n}", tip_scen_team: "L'équipe concernée : en 4c4, les équipes 1 et 2 ont chacune besoin des places 1 à 4.", scen_start_help: "Cliquez sur la carte là où commence le prochain joueur de cette équipe (terrain dégagé, loin des autres).", scen_start_place: "Point de départ : équipe {n}, place {p}", scen_players_label: "Joueurs", tip_scen_players: "Combien de joueurs cette carte accepte dans ce mod (jusqu'à 8). Chacun a besoin d'un point de départ.", scen_players_game: "{n} (jeu)", scen_players_missing: "{n} joueurs demandent un point de départ : {list} (scénario {where}). Ajoutez-les avec Ajouter un point de départ.", scen_players_ok: "Chaque joueur a un point de départ.", scen_players_none: "Cette carte ne se joue pas en ligne : son nombre de joueurs ne peut pas changer.", road_part: "cette partie {len}", road_total: "{len} au total", road_note: "Les camions de ravitaillement suivent les nouvelles routes, peintes au sol (vérifié en jeu). Une route sur l'eau reçoit un pont.", roads_show: "Routes", tip_roads_show: "Afficher les routes de la carte en doré, sur le terrain que vous modelez.", check_rename: "Renommer en {name}", tip_check_rename: "Renomme le dossier de la carte dans votre mod avec le nom de pack du jeu. Rien à l'intérieur ne change.", report_problem: "Signaler un problème", tip_report_problem: "Ouvre un rapport de bug dans votre navigateur, avec l'application et sa version déjà remplies. Vous le relisez et le publiez vous-même.", report: "Signaler", tip_report: "Signaler ce bug : le navigateur ouvre un rapport avec ce message (chemins sans votre nom d'utilisateur).", set_help_title: "Aide et communauté", set_help_help: "Le wiki est le manuel : un guide pour chaque outil. Questions, idées, mods et bugs vont dans les Discussions.", help_wiki: "Wiki (manuel)", tip_help_wiki: "Ouvre le wiki dans le navigateur : des guides pas à pas pour chaque outil.", help_discussions: "Discussions", tip_help_discussions: "Ouvre les Discussions dans le navigateur : questions, idées, mods et cartes.", check_title: "Vérification du mod : {n} problème(s). La construction pour le jeu s'arrêterait ici.", check_set_aside: "Mettre de côté", tip_check_set_aside: "Renomme le fichier en <nom>.broken.toml à côté : la construction l'ignore, rien n'est perdu, la carte repart à zéro.", check_aside_done: "Mis de côté : {file}.", check_stop: "Corrigez d'abord les problèmes du mod (la barre en haut).", scen_count: "Combien", tip_scen_count: "Combien un clic en ajoute, dans la forme choisie dessous.", formation_line: "Ligne", formation_column: "Colonne", formation_wedge: "Coin", formation_box: "Carré", formation_circle: "Cercle", tip_scen_formation: "La forme dans laquelle ils se placent. Elle fait face au haut de l'écran, son centre là où vous cliquez ; les ronds montrent où va chacun.", tip_scen_gap: "L'écart entre eux, en mètres.", tip_maps_hide: "Replier la liste des cartes : plus de place pour la carte.", tip_maps_show: "Afficher à nouveau la liste des cartes.", dock_terrain: "Terrain", dock_movement: "Mouvement", tip_dock_terrain: "Collines, cratères, plateaux, rampes : modelez le terrain.", tip_dock_water: "Lacs et rivières : inondez jusqu'à un niveau, ou asséchez.", tip_dock_cover: "Où les unités se cachent : peignez du couvert, retirez-le, ou couvrez une ville en un clic.", tip_dock_movement: "Où vont les unités : fermez le terrain à toutes, à l'infanterie ou aux véhicules.", tip_dock_building: "Posez les bâtiments de la carte : un seul, une zone ou une rangée.", tip_dock_prop: "Posez les objets de la carte : clôtures, caisses, épaves, etc.", tip_dock_vegetation: "Plantez les arbres de la carte : un seul, un bois ou une rangée.", tip_dock_scenario: "Le scénario choisi : déplacez points de départ et apparitions, ou ajoutez unités et bâtiments.", brush_block: "Bloquer", brush_block_infantry: "Bloquer l'infanterie", brush_block_vehicles: "Bloquer les véhicules", tip_brush_block: "Aucune unité ne passe ici : elles contournent (falaise, lac, mur). Vérifié en jeu.", tip_brush_block_infantry: "L'infanterie ne passe pas ici ; les véhicules si.", tip_brush_block_vehicles: "Les véhicules ne passent pas ici ; l'infanterie si (comme un bois).", move_show: "Où vont les unités", tip_move_show: "Afficher où les unités peuvent aller : rouge = fermé à toutes (eau, falaises, hors carte), jaune = fermé aux véhicules (bois).", place_solid: "Solide", tip_place_solid: "Les unités ne traversent pas les bâtiments posés (vérifié en jeu). Désactivé : ils ne sont que dessinés.", brush_cover: "Couvert", brush_uncover: "Découvrir", brush_town: "Ville", tip_brush_cover: "Peint du couvert : les unités y sont cachées, comme dans un bois (en vert). Vérifié en jeu.", tip_brush_uncover: "Retire le couvert : les unités y sont visibles, même dans un bois.", tip_brush_town: "Cliquez sur une ville : du couvert est posé autour de chacun de ses bâtiments (Taille : jusqu'où), pour y cacher les unités.", cover_show: "Couvert", tip_cover_show: "Afficher où les unités se cachent (en vert) : bois et villes de la carte, et ce que peint ce mod.", town_none: "Pas de bâtiment ici : cliquez sur une ville ou un groupe de bâtiments.", town_done: "Couvert autour de {n} bâtiments.", group_ap: "Obus perforants (antichar)", group_he: "Obus explosifs", group_aa: "Antiaérien", group_mg: "Mitrailleuses", group_infantry_weapons: "Armes d'infanterie", group_antitank_weapons: "Antichar d'infanterie", group_bombs: "Bombes", group_rockets: "Roquettes", scen_move_tool: "Déplacer", tip_scen_move: "Déplacer un point de départ ou une apparition : cliquez dessus, puis là où il va. Enregistré dans le mod.", scen_spawn_tool: "Ajouter une unité", tip_scen_spawn: "Ajouter une unité ou un bâtiment qui apparaît au début de ce scénario : choisissez sa catégorie, son type et son nom, un camp, puis cliquez sur la carte.", tip_scen_kind: "Bâtiments, unités terrestres, infanterie ou avions.", tip_scen_unit: "L'unité ou le bâtiment, par nation.", tip_scen_camp: "Le camp auquel il appartient. Quel numéro correspond à quel joueur : testez dans le jeu.", scen_side_neutral: "Neutre", tip_scen_camp_skirmish: "Une partie en escarmouche ne fait apparaître que des éléments neutres, comme les dépôts de la carte : une unité pour le camp d'un joueur n'apparaîtrait jamais, ce scénario ne prend donc que Neutre.", scen_side_n: "Camp {n}", scen_pick_item: "Cliquez sur un point de départ ou une apparition à déplacer.", scen_pick_place: "Cliquez maintenant là où il va : {what}.", scen_remove: "Retirer", scen_put_back: "Remettre", scen_spawn_help: "Cliquez sur la carte là où il apparaît.", scen_pick_unit: "Choisissez d'abord une unité ou un bâtiment.", scen_moved: "déplacé dans ce mod", scen_mine: "ajouté dans ce mod", group_all: "Tous les types", tip_group: "À quoi il sert : le rôle d'un bâtiment (QG, argent, usine, fort, factice) ou l'usine qui produit une unité.", group_hq: "QG", group_money: "Argent (dépôts, administration)", group_factory: "Usines", group_fort: "Forts et défenses", group_fake: "Factices (leurres)", group_barracks: "Caserne", group_armor: "Blindés", group_antitank: "Antichar", group_artillery: "Artillerie", group_prototype: "Prototypes", group_airfield: "Aérodrome", group_turret: "Canons de fort", group_other: "Autres", brush_water: "Eau", brush_drain: "Assécher", tip_brush_water: "Inonde le sol sous un niveau d'eau : la hauteur où vous commencez à glisser, plus la force. Le sol lui-même ne change pas.", tip_brush_drain: "Remet l'eau au niveau de base de la carte : les lacs et rivières s'y assèchent.", tip_brush_level: "Peint le terrain à plat à une hauteur : celle où vous commencez à glisser. Commencez sur un terrain à la hauteur voulue.", brush_smooth: "Adoucir", brush_size: "Taille",
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
      brush_flatten: "压平", brush_level: "整平", scen_show: "剧本", maps_all: "所有地图", tip_map_kind: "只显示游戏以此方式提供的地图：遭遇战、作战、战役、演示或测试。", settings_tab: "设置", tip_tab_settings: "语言、按键、游戏文件夹和更新。", settings_title: "设置", set_language_title: "语言", set_language_help: "代号显示游戏内部名称；十种语言中的任何一种显示玩家看到的名称。", set_keys_title: "地图视图按键", set_keys_help: "点击一个按键，然后按下想要的键。", set_game_title: "游戏文件夹", set_game_path: "R.U.S.E. 位于 {path}。", set_game_none: "未找到 R.U.S.E.，请选择其文件夹。", set_game_change: "选择文件夹…", set_updates_title: "更新", set_updates_latest: "这是 RUSE Studio {version}。每次打开时都会检查新版本。", set_updates_check: "立即检查", set_updates_checking: "正在查找新版本…", scen_kind_skirmish: "战斗", scen_kind_operation: "任务", scen_kind_campaign: "战役", scen_kind_demo: "演示", scen_kind_test: "测试用", scen_kind_unused: "不在任何菜单中", tip_scen_show: "显示剧本的区域、起始点（各同盟颜色的柱子）、出生点（白色菱形）和城镇名称。", tip_scen_pick: "地图的剧本：先是遭遇战，然后是挑战和战役章节。", scen_main: "主要", scen_none: "此地图没有剧本。", scen_stats: "{zones} 个区域 · {starts} 个起始点 · {spawns} 个出生点 · {names} 个名称", scen_zone: "区域", scen_start: "起始点，同盟 {n}", scen_spawn: "出生点", tip_panel_grip: "拖动可移动此面板。双击可复位。", tip_panel_fold: "收起此面板。", tip_panel_unfold: "重新展开此面板。", scen_where: "游戏中：{where}", scen_players: "{n}人", tip_scen_where: "测试后在游戏中开始此项，即可看到你对该布局的更改。", dock_roads: "道路", tip_dock_roads: "绘制新道路：补给卡车会沿着它行驶。端点会吸附到接触的道路上。", road_straight: "直线", road_curve: "曲线", road_free: "自由", tip_road_straight: "直线道路：先点击起点，再点击终点。", tip_road_curve: "弯曲道路：依次点击起点、弯向的点、终点。", tip_road_free: "沿点击路线的道路：沿途点击，然后双击或按回车完成。", road_help_straight: "点击道路起点，再点击终点。靠近道路的端点会吸附上去（圆圈会显示）。", road_help_curve: "依次点击起点、弯曲处、终点。", road_help_free: "沿路线点击；双击、回车或“完成”结束。Esc 放弃。", road_finish: "完成", tip_road_finish: "在最后一个点结束道路。", tip_road_undo: "撤销最后一条道路（Ctrl+Z）。", road_count: "此地图上的新道路：{n}", scen_seat: "队伍 {n} 第 {p} 位", scen_start_tool: "添加起始点", tip_scen_start: "新的玩家起始点：选择队伍，然后点击地图。增加玩家需要每人一个。", scen_team_n: "队伍 {n}", tip_scen_team: "它属于哪个队伍：4对4时，队伍1和2各需要第1到第4个位置。", scen_start_help: "在地图上点击该队下一名玩家开始的位置（开阔地，远离其他人）。", scen_start_place: "起始点：队伍 {n}，第 {p} 位", scen_players_label: "玩家", tip_scen_players: "此模组中这张地图可容纳的玩家数（最多 8）。每人需要一个起始点。", scen_players_game: "{n}（游戏）", scen_players_missing: "{n} 名玩家需要起始点：{list}（剧本 {where}）。用“添加起始点”添加。", scen_players_ok: "每名玩家都有起始点。", scen_players_none: "这张地图不能在线游玩，玩家数无法更改。", road_part: "本段 {len}", road_total: "共 {len}", road_note: "补给卡车会走新道路，道路也会绘制在地面上（已在游戏中验证）。跨越水面的道路会架桥。", roads_show: "道路", tip_roads_show: "以金色显示地图的道路，贴在你塑造的地形上。", check_rename: "重命名为 {name}", tip_check_rename: "把模组中的地图文件夹改名为游戏使用的包名。其中内容不变。", report_problem: "报告问题", tip_report_problem: "在浏览器中打开错误报告，已填好应用和版本。由你检查后自行发布。", report: "报告", tip_report: "作为错误报告：浏览器会打开包含此消息的报告（路径中不含你的用户名）。", set_help_title: "帮助与社区", set_help_help: "Wiki 是使用手册：每个工具都有指南。提问、建议、展示模组或报告错误请到 Discussions。", help_wiki: "Wiki（手册）", tip_help_wiki: "在浏览器中打开 Wiki：每个工具的分步指南。", help_discussions: "Discussions", tip_help_discussions: "在浏览器中打开 Discussions：提问、建议、模组和地图。", check_title: "模组检查：{n} 个问题。游戏构建会在此停止。", check_set_aside: "搁置", tip_check_set_aside: "把文件改名为 <名称>.broken.toml 放在旁边：构建会跳过它，不会丢失任何内容，地图从头开始。", check_aside_done: "已搁置为 {file}。", check_stop: "请先修复模组的问题（顶部的横条）。", scen_count: "数量", tip_scen_count: "一次点击添加的数量（按下方所选队形）。", formation_line: "横队", formation_column: "纵队", formation_wedge: "楔形", formation_box: "方阵", formation_circle: "圆阵", tip_scen_formation: "它们站立的队形。朝向屏幕上方，中心在点击处；圆圈显示每个单位的位置。", tip_scen_gap: "单位之间的间距（米）。", tip_maps_hide: "收起地图列表：给地图更多空间。", tip_maps_show: "再次显示地图列表。", dock_terrain: "地形", dock_movement: "通行", tip_dock_terrain: "山丘、弹坑、高地、坡道：塑造地形。", tip_dock_water: "湖泊与河流：淹没到某一水位，或将其排干。", tip_dock_cover: "单位隐藏之处：绘制掩护、移除掩护，或一键覆盖整个城镇。", tip_dock_movement: "单位可达之处：对所有单位、步兵或车辆封锁地面。", tip_dock_building: "放置地图自带的建筑：单个、区域或一排。", tip_dock_prop: "放置地图自带的物件：栅栏、箱子、残骸等。", tip_dock_vegetation: "种植地图自带的树木：单棵、树林或一排树。", tip_dock_scenario: "所选剧本：移动起始点和出生点，或添加单位和建筑。", brush_block: "封锁", brush_block_infantry: "封锁步兵", brush_block_vehicles: "封锁车辆", tip_brush_block: "任何单位都不能通过：它们会绕行（悬崖、湖、墙）。已在游戏中验证。", tip_brush_block_infantry: "步兵不能通过；车辆可以。", tip_brush_block_vehicles: "车辆不能通过；步兵可以（如同树林）。", move_show: "单位可达", tip_move_show: "显示单位可达之处：红色对所有单位关闭（水、悬崖、地图外），黄色仅对车辆关闭（树林）。", place_solid: "实体", tip_place_solid: "单位不能穿过你放置的建筑（已在游戏中验证）。关闭时：仅绘制。", brush_cover: "掩护", brush_uncover: "移除掩护", brush_town: "城镇", tip_brush_cover: "绘制掩护：单位在其中会像在树林里一样隐藏（绿色）。已在游戏中验证。", tip_brush_uncover: "移除掩护：单位在其中可被看见，即使在树林里。", tip_brush_town: "点击一个城镇：在其每栋建筑周围加上掩护（大小：范围），让单位能在城中隐藏。", cover_show: "掩护", tip_cover_show: "显示单位隐藏之处（绿色）：地图的树林和城镇，以及本模组绘制的区域。", town_none: "这里没有建筑：请点击城镇或一组建筑。", town_done: "{n} 栋建筑周围已加掩护。", group_ap: "穿甲弹（反坦克）", group_he: "高爆弹", group_aa: "防空", group_mg: "机枪", group_infantry_weapons: "步兵武器", group_antitank_weapons: "步兵反坦克武器", group_bombs: "炸弹", group_rockets: "火箭", scen_move_tool: "移动", tip_scen_move: "移动起始点或出生点：点击它，再点击要放的位置。保存在模组中。", scen_spawn_tool: "放置单位", tip_scen_spawn: "添加在此剧本开始时出现的单位或建筑：选择类别、类型和名称，选择阵营，然后点击地图。", tip_scen_kind: "建筑、地面单位、步兵或飞机。", tip_scen_unit: "单位或建筑（按国家）。", tip_scen_camp: "所属阵营。哪个编号对应哪个玩家：请在游戏中测试。", scen_side_neutral: "中立", tip_scen_camp_skirmish: "遭遇战只会生成中立物体，例如地图上的补给站：属于玩家阵营的单位永远不会出现，因此本剧本只能选择中立。", scen_side_n: "阵营 {n}", scen_pick_item: "点击要移动的起始点或出生点。", scen_pick_place: "现在点击 {what} 要放的位置。", scen_remove: "移除", scen_put_back: "放回", scen_spawn_help: "在地图上点击它出现的位置。", scen_pick_unit: "请先选择单位或建筑。", scen_moved: "已在此模组中移动", scen_mine: "已在此模组中添加", group_all: "所有类型", tip_group: "用途：建筑的作用（司令部、资金、工厂、要塞、假的）或生产该单位的工厂。", group_hq: "司令部", group_money: "资金（补给站、行政）", group_factory: "工厂", group_fort: "要塞与防御", group_fake: "假的（诱饵）", group_barracks: "兵营", group_armor: "装甲", group_antitank: "反坦克", group_artillery: "炮兵", group_prototype: "原型", group_airfield: "机场", group_turret: "要塞火炮", group_other: "其他", brush_water: "水", brush_drain: "排干", tip_brush_water: "把低于水位的地面淹没：水位为开始拖动处的高度加上强度。地面本身不变。", tip_brush_drain: "把水恢复到地图的基准水位：那里的湖泊和河流会干涸。", tip_brush_level: "把地面刷平到同一高度：即开始拖动处的高度。请从所需高度的地面开始。", brush_smooth: "平滑", brush_size: "大小", brush_strength: "强度", brush_look: "查看", brush_undo: "撤销",
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
  // units made in the Studio: copies of one of the above, kept per mod like src/studio.rndf holds them
  const newUnits = [];  // { mod, id, source, name, price, nation, factory }
  const newAddress = (id) => E + id;
  const safeName = (name) => name.normalize("NFKD").replace(/[^\x00-\x7f]/g, "").replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  const home = "C:/Users/You/AppData/Local/RUSE Mod Platform/mods/";
  const mods = [{ path: home + "sherman-test", name: "sherman-test" }];  // sample data for the preview only
  let checkProblems = [{ file: "maps/SuperCrossRoads4/terrain.toml", set_aside: true,
    problem: "maps/SuperCrossRoads4/terrain.toml: stroke 1: the water brush needs level" }];
  const fakeRoads = {};  // the made-up mod's new roads, per map
  let current = mode === "nomod" ? null : mods[0].path;
  const edits = new Map();  // `${mod}|${address}|${prop}|${how}|${via}` -> value, like the mod's src/studio.rndf
  const terrains = new Map();  // `${mod}|${map pack}` -> strokes, like the mod's maps/<pack>/terrain.toml
  const placed = new Map();    // `${mod}|${map pack}` -> placed objects, like the mod's maps/<pack>/scenery.toml
  const editKey = (address, prop, how, via) => `${current}|${address}|${prop}|${how || ""}|${how === "own" ? via : ""}`;
  if (current) edits.set(editKey(E + "M4_Sherman", "ProductionTime"), 1);  // a cheap, fast Sherman, as in the owner's test
  const mine = () => newUnits.filter((n) => n.mod === current);
  const BLAST = E + "M4_Sherman:Weapon.Blast";  // a part three units share
  const BLAST_OWNERS = ["M4_Sherman", "M3A1_Stuart", "Type97_ChiHa"];

  // ammunition: what a weapon fires; each unit has one mounted weapon here, and every ground unit its flags
  const A = "$/GFX/Everything/Ammo_";
  const ammo = [
    { id: "75mm_M3", ammoId: 1001, names: { us: "AP shell · Medium cal.", fr: "Obus AP · Moyen cal.", sc: "穿甲弹 · 中口径" },
      power: 40, range: 2800, users: ["M4_Sherman", "M3A1_Stuart"], group: "ap" },
    { id: "75mm_KwK40", ammoId: 1002, names: { us: "AP shell · Long 75", fr: "Obus AP · 75 long", sc: "穿甲弹 · 长身管75" },
      power: 55, range: 3200, users: ["Panzer_IV_G"], group: "ap" },
    { id: "MG_Cal30", ammoId: 1048, names: { us: "Machine-gun · .30 cal.", fr: "Mitrailleuse · cal. 30", sc: "机枪 · .30口径" },
      power: 2, range: 1300, users: ["Soldat_US_Leger", "P40Warhawk", "Type97_ChiHa"], group: "mg" },
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
          { name: "zone_east", number: 1, points: [760000, 450000, 1020000, 450000, 1020000, 800000, 760000, 800000], triangles: [0, 1, 2, 0, 2, 3] }],
          items: [{ kind: "StartingPoint", x: 430000, y: 620000, turn: 0, name: "", alliance: 1 },
            { kind: "StartingPoint", x: 890000, y: 620000, turn: 0, name: "", alliance: 2 },
            { kind: "Spawn", x: 655000, y: 420000, turn: 0, name: "depot", camp: -1, what: "Unit_M4_Sherman" },
            { kind: "LabelVille", x: 655000, y: 700000, turn: 0, name: "", text: "Port Island" }] },
        { file: "leveldesign_challenge.scenario", kind: "operation", entries: [{ name: "Challenge - Island", kind: "operation", titles: { us: "Harbour raid", fr: "Raid sur le port" } }], zones: [], items: [{ kind: "StartingPoint", x: 655000, y: 620000, turn: 0, name: "", alliance: 1 }] }] });
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
    if (!scenarioEdits.has(key)) scenarioEdits.set(key, { moves: [], spawns: [], starts: [] });
    return scenarioEdits.get(key);
  }
  function withScenarioEdits(pack) {
    const out = baseScenarios();
    const e = current && scenarioEdits.get(`${current}|${pack}`) || { moves: [], spawns: [], starts: [] };
    for (const s of out.scenarios) {
      s.items.forEach((it, i) => { it.item = i; if (it.kind === "StartingPoint") it.place = it.place || 1; });
      for (const m of e.moves) if (m.file === s.file && s.items[m.item]) Object.assign(s.items[m.item], { x: m.x, y: m.y, moved: true });
      (e.starts || []).forEach((st, n) => {
        if (st.file !== s.file) return;
        const place = 1 + Math.max(0, ...s.items.filter((it) => it.kind === "StartingPoint" && it.alliance === st.team).map((it) => it.place || 1));
        s.items.push({ kind: "StartingPoint", x: st.x, y: st.y, turn: 0, name: "", alliance: st.team, place, mine: true,
          start: n, item: s.items.length });
      });
      e.spawns.forEach((sp, n) => {
        if (sp.file === s.file) s.items.push({ kind: "Spawn", x: sp.x, y: sp.y, turn: 0, name: "", camp: sp.camp, what: sp.what,
          mine: true, spawn: n, item: s.items.length });
      });
    }
    return out;
  }
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
    return { address, class: cls, name, stable: true, shared: Boolean(share), owners: [], groups: out, parts, uses,
      used_by: usedBy, editable, why_not: whyNot, users, share: share || null, named: !address.includes(":"),
      can_copy: editable && !address.includes(":") && units.some((u) => E + u.id === address), new: null,
      can_copy_ammo: false, has_weapons: !address.includes(":") && cls !== "TAmmunition" };
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
        [["weapon", [["Puissance", 40], ["PorteeMaximale", 2800], ["TempsEntreDeuxTirs", 3.5, { type: "float32" }]]]],
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
    return { weapons: [{ address: weapon, name: "weapon_effet_tag1", ammo: { address: current_, name: names.get(current_) || current_ },
      game_ammo: ammoAddress(game.id), edited: Boolean(chosen), shot: shotOf(current_) }], choices };
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
    const palette = [["TypeWarrior/MairieNormande", "MairieNormande", "building", "COC/Normandie/Batiments_Villes_Villages", 1],
      ["TypeWarrior/TownHouseB2_Haut", "TownHouseB2_Haut", "building", "COC/Normandie/BatimentsMorceaux/TownHouseB/B2", 39],
      ["TypeWarrior/Charette_1", "Charette_1", "prop", "Props/Ferme", 30],
      ["TypeWarrior/Chene_02", "Chene_02", "vegetation", "Vegetation/Arbres", 12000]];
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
      triangles: await packed(new Uint32Array(tri)), water: await packed(new Uint32Array(wtri)), picture: "" };
  }

  // Share your mod (words.toml share_*): the steps onto the supported-mods list, and an export's file
  Object.assign(words.us, {"share_mod": "Share your mod…", "share_title": "Share your mod", "share_lead": "Made a mod? Add it to the list and become a contributor.", "share_step_export": "Export it as a .rusemod (Export mod… in the mod menu). Its size and SHA-256 show here.", "share_step_pr": "Upload the .rusemod (a GitHub Release is easiest), then open a pull request to {repo} that adds its entry to index.toml, with the size and SHA-256 the export shows.", "share_step_post": "Or post it in the Discussions, and it's added to the list for you.", "share_file": "File: {file} ({size} bytes)", "share_sha": "SHA-256: {sha}", "share_entry": "Its entry for index.toml (put the file's link in download):", "share_copy": "Copy the entry", "share_copied": "Copied: paste it into index.toml.", "share_open": "Open the mod list on GitHub", "share_discussions": "Open the Discussions"});
  Object.assign(words.fr, {"share_mod": "Partager votre mod…", "share_title": "Partagez votre mod", "share_lead": "Vous avez fait un mod ? Ajoutez-le à la liste et devenez contributeur.", "share_step_export": "Exportez-le en .rusemod (Exporter le mod… dans le menu du mod). Sa taille et son SHA-256 s'affichent ici.", "share_step_pr": "Mettez le .rusemod en ligne (une GitHub Release est le plus simple), puis ouvrez une pull request sur {repo} qui ajoute son entrée à index.toml, avec la taille et le SHA-256 qu'affiche l'export.", "share_step_post": "Ou publiez-le dans les Discussions, et il sera ajouté à la liste pour vous.", "share_file": "Fichier : {file} ({size} octets)", "share_sha": "SHA-256 : {sha}", "share_entry": "Son entrée pour index.toml (mettez le lien du fichier dans download) :", "share_copy": "Copier l'entrée", "share_copied": "Copié : collez-la dans index.toml.", "share_open": "Ouvrir la liste des mods sur GitHub", "share_discussions": "Ouvrir les Discussions"});
  Object.assign(words.sc, {"share_mod": "分享你的模组…", "share_title": "分享你的模组", "share_lead": "做了模组？把它加入列表，成为贡献者。", "share_step_export": "将其导出为 .rusemod（模组菜单中的“导出模组…”）。其大小和 SHA-256 会显示在这里。", "share_step_pr": "上传 .rusemod（用 GitHub Release 最简单），然后向 {repo} 提交一个拉取请求，把它的条目加入 index.toml，并填上导出时显示的大小和 SHA-256。", "share_step_post": "或者在 Discussions 中发布，我们会替你把它加入列表。", "share_file": "文件：{file}（{size} 字节）", "share_sha": "SHA-256：{sha}", "share_entry": "它在 index.toml 中的条目（在 download 中填入文件链接）：", "share_copy": "复制条目", "share_copied": "已复制：请粘贴到 index.toml 中。", "share_open": "在 GitHub 上打开模组列表", "share_discussions": "打开 Discussions"});
  const exported = { path: "C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod", file: "sherman-test-0.1.0.rusemod",
    size: 2711, size_text: "3 KB", sha256: "5d1c0f4b0e7f7c3ad8b0a4f6f1f0a0e8c4b2d6e1f3a5c7e9b1d3f5a7c9e1b3d5",
    entry: ["[[mod]]", 'id = "sherman-test"', 'name = "sherman-test"', 'version = "0.1.0"', 'description = "Made in the RUSE Studio."',
      'download = ""  # the https:// link to the .rusemod once it is uploaded (a GitHub Release)', "size = 2711",
      'sha256 = "5d1c0f4b0e7f7c3ad8b0a4f6f1f0a0e8c4b2d6e1f3a5c7e9b1d3f5a7c9e1b3d5"', 'game_build = "24687178"',
      'fingerprint = "K7Q2-M9XD"', 'tags = []  # e.g. ["gameplay"]; a cheat or a test tool: ["cheat"]'].join("\n") + "\n" };
  const jobs = {
    index: [["  ZZ_Win.dat"], "The game index is ready."],
    export: [["Building the mod on the game, to record the game build and the fingerprint…", "  fingerprint: K7Q2-M9XD",
      "Saved as C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod", "Size: 2711 bytes",
      "SHA-256: 5d1c0f4b0e7f7c3ad8b0a4f6f1f0a0e8c4b2d6e1f3a5c7e9b1d3f5a7c9e1b3d5"],
      "Saved as C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod"],
    test: [["Building the modded copy of R.U.S.E. for sherman-test in D:\\RUSE-Instances\\studio-sherman-test…",
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
        const out = shown.filter((u) => group === "all" || (u.group || groupOf(u)) === group)
          .map((u) => ({ address: E + u.id, name: u.new ? u.names.us : nameOf(u, lang), base_name: "Descriptor_Unit_" + u.id,
            kind: u.kind, nation: u.nation, nation_name: (nations[lang] || nations.us)[u.nation], factory: u.factory,
            slot: u.slot, new: Boolean(u.new), source: u.source || null, group: u.group || groupOf(u) }))
          .filter((u) => !search || u.name.toLowerCase().includes(search.toLowerCase()));
        return { units: out, total: units.length + made.length, groups: GROUPS.filter((g) => present.has(g)) };
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
      mods: async () => modsView(),
      new_mod: async (name) => {
        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "my-mod";
        mods.push({ path: home + slug, name: slug });
        current = home + slug;
        return modsView();
      },
      choose_mod: async (path) => { current = path; return modsView(); },
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
      test_in_game: async () => ({ job: "test" }),
      mod_info: async () => ({ id: "sherman-test", name: "sherman-test", version: "0.1.0", authors: [], author: "",
        description: "Made in the RUSE Studio.", builds: [], data_revision: "", fingerprint: "" }),
      export_mod: async () => ({ job: "export" }),
      build_index: async () => ({ job: "index" }),
      job: async (id, since) => backupJobs[id] ? backupJobView(id, since || 0)
        : mode === "testfails" && id === "test"  // a test stopped by a leftover copy, as a player's was
        ? { state: "failed", message: "[WinError 5] Access is denied: 'D:\\RUSE-Instances\\studio-sherman-test.old'",
          lines: jobs.test[0].slice(0, 1), count: 1 }
        : { state: "done", message: jobs[id][1], lines: jobs[id][0], count: jobs[id][0].length,
            ...(id === "export" ? { result: exported } : {}) },  // the file for "Share your mod"
      share_info: async () => ({ repo: "sneadtristen6/Ruse-Mods", page: "https://github.com/sneadtristen6/Ruse-Mods" }),
      maps: async () => ({ maps: fakeMaps }),
      map_view: async (pack, lod) => fakeGround(pack, lod || "lowdef"),
      map_ground: async () => ({ url: null }),
      map_models: async () => ({}),  // no game models in the preview: the shapes stay  // the made-up island has only its colours
      update_check: async () => mode === "update"
        ? { available: true, version: "9.9.9", installed: true, size: 60000000,
            page: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases" }
        : { available: false, version: "0.6.3" },
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
      scenery: async (pack) => ({ objects: current ? (placed.get(`${current}|${pack}`) || []) : [], saved: null, mod: current }),
      scenery_add: async (pack, objects) => {
        if (!current) throw new Error("Pick or make a mod first: what you place is saved in it.");
        const key = `${current}|${pack}`, list = (placed.get(key) || []).concat(objects);
        placed.set(key, list);
        return { count: list.length, saved: `${current}/maps/${pack}/scenery.toml` };
      },
      scenery_undo: async (pack, count = 1) => {
        const key = `${current}|${pack}`, list = placed.get(key) || [], n = Math.min(count, list.length);
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
      roads: async (pack) => ({ roads: (fakeRoads[pack] || []).map((points) => ({ points, join: 3000 })), mod: current,
        saved: null }),
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
      scenario_move: async (pack, file, item, x, y) => {
        const e = scenEdits(pack);
        e.moves = e.moves.filter((m) => !(m.file === file && m.item === item)).concat([{ file, item, x, y }]);
        return withScenarioEdits(pack);
      },
      scenario_put_back: async (pack, file, item) => {
        const e = scenEdits(pack);
        e.moves = e.moves.filter((m) => !(m.file === file && m.item === item));
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
