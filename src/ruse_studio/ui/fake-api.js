// A made-up StudioApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=noindex shows the "no index yet" state, ?fake=nomod the Studio before any mod is picked). Only English, French
// and Chinese words are included here; the real Studio has all ten languages. It does nothing in the real Studio window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
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
      brush_flatten: "Flatten", brush_level: "Level", scen_show: "Scenario", tip_scen_show: "Show the scenario's zones, starting points (pillars in each alliance's colour), spawns (white diamonds) and town names.", tip_scen_pick: "The map's scenarios: the skirmish one first, then challenges and campaign chapters.", scen_main: "main", scen_none: "This map has no scenario.", scen_stats: "{zones} zones · {starts} starting points · {spawns} spawns · {names} names", scen_zone: "Zone", scen_start: "Starting point, alliance {n}", scen_spawn: "Spawn", brush_water: "Water", brush_drain: "Drain", tip_brush_water: "Floods the ground below a water level: the height where you start dragging, plus Strength. The ground itself is unchanged.", tip_brush_drain: "Puts the water back to the map's base level: lakes and rivers there dry up.", tip_brush_level: "Paints the ground flat at one height: the height where you start dragging. Start on ground at the height you want.", brush_smooth: "Smooth", brush_size: "Size", brush_strength: "Strength",
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
      scenery_note: "For now, scenery is only for looks: trees give no cover and buildings don't block movement (that lives in other map files).",
      place_ground: "Click on the ground of the map.", undone: "Undone: {name} is back to what it was.",
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
      brush_plateau: "Plateau", brush_flatten: "Aplanir", brush_level: "Niveler", scen_show: "Scénario", tip_scen_show: "Afficher les zones du scénario, les points de départ (piliers à la couleur de chaque alliance), les apparitions (losanges blancs) et les noms de villes.", tip_scen_pick: "Les scénarios de la carte : l'escarmouche d'abord, puis les défis et les chapitres de campagne.", scen_main: "principal", scen_none: "Cette carte n'a pas de scénario.", scen_stats: "{zones} zones · {starts} points de départ · {spawns} apparitions · {names} noms", scen_zone: "Zone", scen_start: "Point de départ, alliance {n}", scen_spawn: "Apparition", brush_water: "Eau", brush_drain: "Assécher", tip_brush_water: "Inonde le sol sous un niveau d'eau : la hauteur où vous commencez à glisser, plus la force. Le sol lui-même ne change pas.", tip_brush_drain: "Remet l'eau au niveau de base de la carte : les lacs et rivières s'y assèchent.", tip_brush_level: "Peint le terrain à plat à une hauteur : celle où vous commencez à glisser. Commencez sur un terrain à la hauteur voulue.", brush_smooth: "Adoucir", brush_size: "Taille",
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
      scenery_note: "Pour l'instant, le décor n'est que visuel : les arbres n'offrent aucun couvert et les bâtiments ne bloquent pas les déplacements (cela se trouve dans d'autres fichiers de la carte).",
      place_ground: "Cliquez sur le sol de la carte.", undone: "Annulé : {name} est revenu à sa valeur précédente.",
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
      brush_flatten: "压平", brush_level: "整平", scen_show: "剧本", tip_scen_show: "显示剧本的区域、起始点（各同盟颜色的柱子）、出生点（白色菱形）和城镇名称。", tip_scen_pick: "地图的剧本：先是遭遇战，然后是挑战和战役章节。", scen_main: "主要", scen_none: "此地图没有剧本。", scen_stats: "{zones} 个区域 · {starts} 个起始点 · {spawns} 个出生点 · {names} 个名称", scen_zone: "区域", scen_start: "起始点，同盟 {n}", scen_spawn: "出生点", brush_water: "水", brush_drain: "排干", tip_brush_water: "把低于水位的地面淹没：水位为开始拖动处的高度加上强度。地面本身不变。", tip_brush_drain: "把水恢复到地图的基准水位：那里的湖泊和河流会干涸。", tip_brush_level: "把地面刷平到同一高度：即开始拖动处的高度。请从所需高度的地面开始。", brush_smooth: "平滑", brush_size: "大小", brush_strength: "强度", brush_look: "查看", brush_undo: "撤销",
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
      scenery_note: "目前，布景只是用来看的：树木不提供掩护，建筑也不阻挡移动（那些在地图的其他文件里）。", place_ground: "请点击地图的地面。",
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
  ];
  // units made in the Studio: copies of one of the above, kept per mod like src/studio.rndf holds them
  const newUnits = [];  // { mod, id, source, name, price, nation, factory }
  const newAddress = (id) => E + id;
  const safeName = (name) => name.normalize("NFKD").replace(/[^\x00-\x7f]/g, "").replace(/[^A-Za-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
  const home = "C:/Users/You/AppData/Local/RUSE Mod Platform/mods/";
  const mods = [{ path: home + "sherman-test", name: "sherman-test" }];  // sample data for the preview only
  let current = mode === "nomod" ? null : mods[0].path;
  const edits = new Map();  // `${mod}|${address}|${prop}|${how}|${via}` -> value, like the mod's src/studio.rndf
  const terrains = new Map();  // `${mod}|${map pack}` -> strokes, like the mod's maps/<pack>/terrain.toml
  const placed = new Map();    // `${mod}|${map pack}` -> placed objects, like the mod's maps/<pack>/scenery.toml
  const editKey = (address, prop, how, via) => `${current}|${address}|${prop}|${how || ""}|${how === "own" ? via : ""}`;
  if (current) edits.set(editKey(E + "M4_Sherman", "ProductionTime"), 1);  // a cheap, fast Sherman, as in the owner's test
  const mine = () => newUnits.filter((n) => n.mod === current);
  const BLAST = E + "M4_Sherman:Weapon.Blast";  // a part three units share
  const BLAST_OWNERS = ["M4_Sherman", "M3A1_Stuart", "Type97_ChiHa"];

  // ammunition: what a weapon fires; each unit has one mounted weapon here, and every ground unit two flags
  const A = "$/GFX/Everything/Ammo_";
  const ammo = [
    { id: "75mm_M3", ammoId: 1001, names: { us: "AP shell · Medium cal.", fr: "Obus AP · Moyen cal.", sc: "穿甲弹 · 中口径" },
      power: 40, range: 2800, users: ["M4_Sherman", "M3A1_Stuart"] },
    { id: "75mm_KwK40", ammoId: 1002, names: { us: "AP shell · Long 75", fr: "Obus AP · 75 long", sc: "穿甲弹 · 长身管75" },
      power: 55, range: 3200, users: ["Panzer_IV_G"] },
    { id: "MG_Cal30", ammoId: 1048, names: { us: "Machine-gun · .30 cal.", fr: "Mitrailleuse · cal. 30", sc: "机枪 · .30口径" },
      power: 2, range: 1300, users: ["Soldat_US_Leger", "P40Warhawk", "Type97_ChiHa"] },
  ];
  const newAmmo = [];  // { mod, id, source, name }: copies made here, like the new units
  const ammoAddress = (id) => A + id;
  const myAmmo = () => newAmmo.filter((n) => n.mod === current);
  const ammoName = (a, lang) => lang === "base" ? "Ammo_" + a.id : (a.names[lang] || a.names.us);
  const nationsOf = (a, lang) => [...new Set(a.users.map((id) => units.find((x) => x.id === id).nation))].sort()
    .map((n) => (nations[lang] || nations.us)[n]);
  const flags = { M4_Sherman: [4, 10, 41], M3A1_Stuart: [4, 10], Panzer_IV_G: [4, 10, 72], Type97_ChiHa: [4, 10] };
  const knownFlags = [
    { flag: 4, count: 302, meaning: null, examples: ["M4 Sherman", "M3A1 Stuart", "Panzer IV"] },
    { flag: 10, count: 908, meaning: null, examples: ["M4 Sherman", "Infantry", "P-40 Warhawk"] },
    { flag: 41, count: 876, meaning: null, examples: ["M4 Sherman"] },
    { flag: 72, count: 126, meaning: { us: "Sees through obstacles (no line-of-sight check; aircraft have it)",
      fr: "Voit à travers les obstacles (pas de test de ligne de vue ; les avions l'ont)", sc: "无视障碍物（不做视线检查；飞机默认具有）" },
      examples: ["Panzer IV", "P-40 Warhawk"] },
  ];
  const nameOf = (u, lang) => lang === "base" ? E.slice(17) + u.id : (u.names[lang] || u.names.us);
  const label = (prop, lang) => lang === "base" ? prop : ((labels[lang] || labels.us)[prop] || prop);
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
      paths: ["TwoIslands"], file: "DataMapTwoIslands_v09.dat",
      titles: { us: ["Centre of Gravity", "The Maginot Line"], fr: ["Centre de gravité", "Ligne Maginot"],
                sc: ["引力中心", "马奇诺防线"] } },
    { pack: "SuperCrossRoads4", names: ["(2) Blitz", "Challenge - 1v1 39 Blitz_2 (Anzio)"], paths: ["SuperCrossRoads4"],
      file: "DataMapSuperCrossRoads4_v09.dat",
      titles: { us: ["Blitz", "Anzio"], fr: ["Blitz", "Anzio"], sc: ["闪电战", "安齐奥"] } },
    { pack: "M02_Tunisie", names: ["M02_Tunisie_chapter1", "M02_Tunisie_chapter2"], paths: ["M02_Tunisie"],
      file: "DataMapM02_Tunisie_v09.dat",
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

  const jobs = {
    index: [["  ZZ_Win.dat"], "The game index is ready."],
    export: [["Building the mod on the game, to record the game build and the fingerprint…", "  fingerprint: K7Q2-M9XD",
      "Saved as C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod"], "Saved as C:\\Users\\You\\Documents\\sherman-test-0.1.0.rusemod"],
    test: [["Building the modded copy of R.U.S.E. for sherman-test in D:\\RUSE-Instances\\studio-sherman-test…",
      "  1 change in 1 file", "  modded copy ready: 41 files linked, 1 replaced", "Starting R.U.S.E. from the modded copy…"],
      "R.U.S.E. is starting."],
  };

  window.pywebview = {
    api: {
      languages: async () => [{ code: "base", name: null }, { code: "us", name: "English" }, { code: "fr", name: "Français" },
        { code: "ger", name: "Deutsch" }, { code: "ita", name: "Italiano" }, { code: "spa", name: "Español" },
        { code: "pol", name: "Polski" }, { code: "ru", name: "Русский" }, { code: "cz", name: "Čeština" },
        { code: "jpn", name: "日本語" }, { code: "sc", name: "简体中文" }],
      strings: async (lang) => words_(lang),
      nations: async (lang) => nations[lang] || nations.us,
      status: async () => mode === "noindex" ? { ready: false, can_build: true }
        : mode === "oldindex" ? { ready: false, can_build: true, old: true } : { ready: true, build: "24687178" },
      units: async (lang, kind, nation, search) => {
        if (kind === "ammo") {
          const copies = myAmmo().map((n) => ({ address: ammoAddress(n.id), name: n.name, base_name: "Ammo_" + n.id, kind: "ammo",
            id: null, users: [], nations: nationsOf(ammo.find((a) => ammoAddress(a.id) === n.source), lang), nation: -1, nation_name: "", factory: null, slot: null, new: true, source: n.source,
            source_name: ammoName(ammo.find((a) => ammoAddress(a.id) === n.source), lang) }));
          const out = copies.concat(ammo.map((a) => ({ address: ammoAddress(a.id), name: ammoName(a, lang), base_name: "Ammo_" + a.id,
            kind: "ammo", id: a.ammoId, users: a.users.map((id) => nameOf(units.find((x) => x.id === id), lang)),
            nations: nationsOf(a, lang), nation: -1,
            nation_name: "", factory: null, slot: null, new: false, source: null })))
            .filter((a) => !search || a.name.toLowerCase().includes(search.toLowerCase()) ||
              a.users.some((x) => x.toLowerCase().includes(search.toLowerCase())));
          return { units: out, total: ammo.length + copies.length };
        }
        const made = mine().map((n) => {
          const src = units.find((x) => E + x.id === n.source);
          return { id: n.id, kind: src.kind, nation: n.nation, factory: n.factory, slot: null, names: { us: n.name },
            new: true, source: n.source };
        });
        const out = made.concat(units).filter((u) => (kind === "all" || u.kind === kind) && (nation < 0 || u.nation === nation))
          .map((u) => ({ address: E + u.id, name: u.new ? u.names.us : nameOf(u, lang), base_name: "Descriptor_Unit_" + u.id,
            kind: u.kind, nation: u.nation, nation_name: (nations[lang] || nations.us)[u.nation], factory: u.factory,
            slot: u.slot, new: Boolean(u.new), source: u.source || null }))
          .filter((u) => !search || u.name.toLowerCase().includes(search.toLowerCase()));
        return { units: out, total: units.length + made.length };
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
      job: async (id) => ({ state: "done", message: jobs[id][1], lines: jobs[id][0], count: jobs[id][0].length }),
      maps: async () => ({ maps: fakeMaps }),
      map_view: async (pack, lod) => fakeGround(pack, lod || "lowdef"),
      map_ground: async () => ({ url: null }),
      map_models: async () => ({}),  // no game models in the preview: the shapes stay  // the made-up island has only its colours
      update_check: async () => mode === "update"
        ? { available: true, version: "9.9.9", installed: true, size: 60000000,
            page: "https://github.com/sneadtristen6/Ruse-Mod-Platform/releases" }
        : { available: false },
      update_install: async () => { throw new Error("The preview can't install updates."); },
      update_page: async () => ({ opened: "" }),
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
      // the preview island's scenario: two zones, two starting points, a spawn and a town name (rusemod.scenario.view)
      map_scenarios: async () => ({ scenarios: [
        { file: "leveldesign.scenario", zones: [
          { name: "zone_west", number: 0, points: [300000, 450000, 560000, 450000, 560000, 800000, 300000, 800000], triangles: [0, 1, 2, 0, 2, 3] },
          { name: "zone_east", number: 1, points: [760000, 450000, 1020000, 450000, 1020000, 800000, 760000, 800000], triangles: [0, 1, 2, 0, 2, 3] }],
          items: [{ kind: "StartingPoint", x: 430000, y: 620000, turn: 0, name: "", alliance: 1 },
            { kind: "StartingPoint", x: 890000, y: 620000, turn: 0, name: "", alliance: 2 },
            { kind: "Spawn", x: 655000, y: 420000, turn: 0, name: "depot", camp: 1, what: "Unit_M4_Sherman" },
            { kind: "LabelVille", x: 655000, y: 700000, turn: 0, name: "", text: "Port Island" }] },
        { file: "leveldesign_challenge.scenario", zones: [], items: [{ kind: "StartingPoint", x: 655000, y: 620000, turn: 0, name: "", alliance: 1 }] }] }),
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
