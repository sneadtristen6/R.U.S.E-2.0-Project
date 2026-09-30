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
      brush_flatten: "Flatten", brush_smooth: "Smooth", brush_size: "Size", brush_strength: "Strength",
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
      map_keys: "Keys: W A S D or arrows move · Q E turn · R F zoom · Shift faster · 1-8 brushes · B brush · P place · Esc look around · Ctrl+Z undo · [ ] size · - = strength or turn",
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
      brush_plateau: "Plateau", brush_flatten: "Aplanir", brush_smooth: "Adoucir", brush_size: "Taille",
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
      map_keys: "Touches : W A S D ou flèches pour déplacer · Q E tourner · R F zoom · Maj plus vite · 1-8 pinceaux · B pinceau · P placer · Échap regarder · Ctrl+Z annuler · [ ] taille · - = force ou rotation",
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
      brush_flatten: "压平", brush_smooth: "平滑", brush_size: "大小", brush_strength: "强度", brush_look: "查看", brush_undo: "撤销",
      brush_help: "在地面上点击或拖动来绘制 · 中键拖动旋转 · 右键拖动平移 · 滚轮缩放", brush_count: "此地图上的笔画：{n}",
      brush_note: "已保存到模组。“在游戏中测试”会将其构建进地图。", brush_ramp: "斜坡",
      ramp_help: "先点击斜坡的起点，再点击终点。按 Esc 取消。", brush_clear: "重新开始", really_clear: "删除此地图上的全部 {n} 个笔画？",
      remove_all: "删除",
      all_values: "全部 {n} 个", each_value: "逐个设置", price_dates: "每个战役年代一个价格：房主在创建游戏时选择年代（1939、1942、1945、全面战争）。",
      new_unit: "新单位…", new_unit_name: "新单位的名称(所有语言均显示)", price: "价格(所有战役年代)", build_menu: "生产菜单",
      same_menu: "与 {name} 相同", other_menu: "另一个", nation: "国家", factory: "工厂(按其中的单位显示)", more_units: "及另外 {n} 个",
      copy_of: "在此模组中创建的 {name} 的副本。", delete_unit: "删除此单位", really_delete: "删除 {name}?它的修改也会一并删除。",
      new_mark: "新", unit_made: "{name} 已加入模组。在游戏中测试即可在生产菜单中看到它。", unit_deleted: "已从模组中删除 {name}。",
      map_keys: "按键：W A S D 或方向键移动 · Q E 旋转 · R F 缩放 · Shift 加速 · 1-8 选笔刷 · B 笔刷 · P 放置 · Esc 查看 · Ctrl+Z 撤销 · [ ] 大小 · - = 强度或朝向",
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
      PorteeMaximale: "Maximum range", TempsEntreDeuxTirs: "Time between shots", TirEnMouvement: "Fires while moving" },
    fr: { SeuilMort: "Points de vie", VitesseLineaire: "Vitesse", ProductionPrice: "Prix", ProductionTime: "Temps de production",
      DetectionBase: "Portée de vision", Factory: "Usine", PositionInMenu: "Position dans le menu", Nationalite: "Nation",
      DescriptorId: "Identifiant", ClassNameForDebug: "Nom de débogage", NameInMenuToken: "Nom (clé de texte)",
      Puissance: "Puissance", PorteeMaximale: "Portée maximale", TempsEntreDeuxTirs: "Temps entre deux tirs",
      TirEnMouvement: "Tir en mouvement" },
    sc: { SeuilMort: "生命值", VitesseLineaire: "速度", ProductionPrice: "价格", ProductionTime: "生产时间",
      DetectionBase: "视野范围", Factory: "工厂", PositionInMenu: "菜单位置", Nationalite: "国家", DescriptorId: "编号",
      ClassNameForDebug: "调试名称", NameInMenuToken: "名称(文本键)", Puissance: "威力", PorteeMaximale: "最大射程",
      TempsEntreDeuxTirs: "射击间隔", TirEnMouvement: "行进间射击" },
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
      can_copy: editable && !address.includes(":") && units.some((u) => E + u.id === address), new: null };
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
        ["NameInMenuToken", 0, { text: lang === "base" ? u.key : `${u.key} (${nameOf(u, lang)})` }]]],
      ["cost", [["ProductionPrice", Array(5).fill(u.price)], ["ProductionTime", 20]]],
      ["combat", [["SeuilMort", u.hp]]],
      ["movement", [["VitesseLineaire", u.speed, { type: "float32" }]]],
      ["vision", [["DetectionBase", 2500]]],
      ["menu", [["Factory", u.factory], ["PositionInMenu", u.slot]]],
    ], [{ address: E + u.id + ":WeaponManager.Turrets[class=TTurretTwoAxisDescriptor]", class: "TTurretTwoAxisDescriptor",
      shared: false }, { address: BLAST, class: "TDamageDescriptor", shared: true }],
    [{ address: AMMO, class: "TAmmunition" }], [{ address: "$/GFX/Everything/Menu_Armour_US", path: "Units[3]" }]);
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
      status: async () => mode === "noindex" ? { ready: false, can_build: true } : { ready: true, build: "24687178" },
      units: async (lang, kind, nation, search) => {
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
      delete_unit: async (address) => {
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
        const v = Array.isArray(value) ? value.map(whole) : whole(value);
        const base = how === "own" && r.edited !== null ? [].concat(r.edited) : r.numbers;
        const same = [].concat(v).every((x, i) => x === base[i]);
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
      map_ground: async () => ({ url: null }),  // the made-up island has only its colours
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
