// A made-up LauncherApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=notfound shows the "game not found" state, ?fake=empty a launcher with no mods yet). Only English, French
// and Chinese words are included here; the real launcher has all ten languages. It does nothing in the real window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const prefs = {};  // what the real app keeps in settings.json (rusemod.home.PrefsCalls)
  const words = {
    us: { settings_tab: "Settings", settings_title: "Settings", set_language_title: "Language", set_game_title: "Game folder", set_game_path: "R.U.S.E. is in {path}.", set_game_none: "R.U.S.E. wasn't found. Pick its folder.", set_game_change: "Choose folder…", set_updates_title: "Updates", set_updates_latest: "This is RUSE Launcher {version}. It looks for a newer one each time it opens.", set_updates_check: "Check now", set_updates_checking: "Looking for a newer version…", best_order: "Put in best order", best_order_why: "Where two mods change the same thing, the lower one wins. The best order puts the mods that change more first and the smaller ones after, so each keeps as much as it can.", best_order_helps: "{names} would keep most of their changes instead of losing them.", best_order_done: "{name}: mods put in the best order.", clash_cant_play: "This set can't be played:", clash_overwrites: "Later mods overwrite earlier ones ({n}):", clash_file: "{a} and {b} both replace the same file, {file} ({kind}), with different contents. Only one of them can be in a set.", clash_archive: "{a} replaces the whole archive {file}, and {b} changes files inside it; one of the two would be lost. Only one of them can be in a set.", clash_create: "{a} and {b} each add a new object called {example}; two objects can't share a name. Only one of them can be in a set.", clash_value: "{a} changes {n} values {b} changed too, e.g. {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s values.", clash_value_one: "{a} changes a value {b} changed too, {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s value.", clash_text: "{a} changes {n} texts {b} changed too, e.g. {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s texts.", clash_text_one: "{a} changes a text {b} changed too, {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s text.", kind_script: "a script", kind_script_archive: "a script archive", kind_video: "a video", kind_sound: "a sound", kind_sound_archive: "a sound archive", kind_picture: "a picture", kind_map_file: "a map file", kind_text_file: "a text file", kind_game_data: "game data",
      update_out: "{app} {version} is out.", update_now: "Update", whats_new: "What's new", update_progress: "Downloading the update… {pct}", update_installing: "Installing: {app} closes and opens again by itself.", update_repo: "(This copy runs from the repo: update it with git pull.)", update_failed: "The update didn't work: {why}",
      guide_title: "Playing with mods, in three steps", guide_add: "Add mods: “Add a mod file…” on the left, or drop the file on this window. RUSE Studio mods (.rusemod), RUSE Mod Manager mods (.rmod) and .zip files all work. Or find one under “Browse mods”.", guide_set: "Make a mod set: “New mod set…”, tick the mods and put them in order. Where two mods change the same thing, the lower one wins.", guide_play: "Pick the set and press Play. The launcher builds a separate modded copy of the game and starts it; your Steam game stays as it is.", share: "Share", share_title: "Share this load order", share_help: "Copy this and send it to a friend (Discord, a message…). They import it in RUSE Launcher (“Import a load order…”) or in RUSE Mod Manager and get the same mods in the same order. They need the mods too.", copy: "Copy", copied: "Copied.", import_order: "Import a load order…", import_help: "Paste a load order a friend shared, from RUSE Launcher or RUSE Mod Manager. The new mod set gets the mods you have, in the same order.", import_paste: "Paste the load order here", check_order: "Check", make_set: "Make the mod set", import_found: "{n} of {total} mods are in your library.", import_missing: "Not in your library yet: {names}. Add them (Add a mod file… or Browse mods) and import again, or make the set without them.", import_version: "In your library in another version: {list}.", import_wrong_game: "Made for the other version of the game (R.U.S.E. or R.U.S.E. COMPAT): the mods may not fit yours.", import_done: "Mod set “{name}” made from the shared load order.",
      language: "Language", looking: "Looking for R.U.S.E.…", choose_folder: "Choose folder…", mod_sets: "Mod sets",
      vanilla: "Vanilla", vanilla_desc: "The game as Steam installed it.", no_mods: "No mods", one_mod: "1 mod",
      n_mods: "{n} mods", has_mistake: "Has a mistake", set_mistake: "This mod set has a mistake: {error}", play: "Play",
      play_set: "Play {name}", getting_ready: "Getting everything ready…", details: "Details", join: "Join a friend",
      browse: "Browse mods", coming_soon: "Coming soon", new_set: "New mod set…", set_name: "Name of the mod set",
      tick_mods: "Tick the mods to use. They load in this order: when two change the same thing, the lower one wins.",
      save: "Save", cancel: "Cancel", create: "Create", edit: "Edit", rename: "Rename", duplicate: "Duplicate",
      delete: "Delete", really_delete_set: "Delete the mod set {name}? Its mods stay in the library.", move_up: "Move up",
      move_down: "Move down", copy_name: "{name} (copy)", set_saved: "The mod set {name} was saved.",
      set_deleted: "The mod set {name} was deleted.", from_folder: "from a folder",
      library_empty_for_set: "Add a mod to the library first: a mod set is made of the mods in it.", library: "Mod library",
      add_mod: "Add a mod file…", drop_hint: "…or drop a mod folder or .zip anywhere on this window.",
      drop_here: "Drop it to add it to the library", adding: "Adding the mod…", remove: "Remove",
      really_remove_mod: "Remove {name} from the library? Mod sets that use it stop working until it's back.",
      version_v: "version {v}", by: "by {authors}", made_for: "made for game build {builds}",
      your_build: "you have {build}, so it may not fit", used_in_one: "in 1 mod set", used_in: "in {n} mod sets",
      library_empty: "No mods yet. Add a mod file, or drop one on this window.", mod_added: "{name} was added to the library.",
      mod_updated: "{name} was replaced by version {v}.", mod_removed: "{name} was removed from the library.",
      search_mods: "Search mods", back: "Back", install: "Install", update_to: "Update to {v}", installed: "Installed",
      installing: "Installing…", offline_note: "No connection to the mod list. This is the copy from {date}.",
      list_failed: "The mod list couldn't be loaded: {why}", list_empty: "No mods match.", for_build: "for game build {build}",
      more_info: "More about this mod", refresh_list: "Refresh",
      browse_help: "Mods from the community's list. Install puts one in your library; then tick it in a mod set." },
    fr: { settings_tab: "Réglages", settings_title: "Réglages", set_language_title: "Langue", set_game_title: "Dossier du jeu", set_game_path: "R.U.S.E. est dans {path}.", set_game_none: "R.U.S.E. est introuvable. Choisissez son dossier.", set_game_change: "Choisir le dossier…", set_updates_title: "Mises à jour", set_updates_latest: "Ceci est RUSE Launcher {version}. Il cherche une version plus récente à chaque ouverture.", set_updates_check: "Vérifier", set_updates_checking: "Recherche d'une version plus récente…", best_order: "Mettre dans le meilleur ordre", best_order_why: "Là où deux mods changent la même chose, celui du bas l'emporte. Le meilleur ordre met d'abord les mods qui changent le plus et les plus petits après, pour que chacun garde le plus possible.", best_order_helps: "{names} garderaient la plupart de leurs changements au lieu de les perdre.", best_order_done: "{name} : mods mis dans le meilleur ordre.", clash_cant_play: "Cet ensemble ne peut pas être joué :", clash_overwrites: "Des mods plus bas écrasent des mods plus haut ({n}) :", clash_file: "{a} et {b} remplacent tous deux le même fichier ({kind}), {file}, avec des contenus différents. Un seul d'entre eux peut être dans un ensemble.", clash_archive: "{a} remplace toute l'archive {file}, et {b} modifie des fichiers à l'intérieur ; l'un des deux serait perdu. Un seul d'entre eux peut être dans un ensemble.", clash_create: "{a} et {b} ajoutent chacun un nouvel objet nommé {example} ; deux objets ne peuvent pas porter le même nom. Un seul d'entre eux peut être dans un ensemble.", clash_value: "{a} modifie {n} valeurs que {b} modifie aussi, par ex. {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez les valeurs de {b}.", clash_value_one: "{a} modifie une valeur que {b} modifie aussi, {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez la valeur de {b}.", clash_text: "{a} modifie {n} textes que {b} modifie aussi, par ex. {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez les textes de {b}.", clash_text_one: "{a} modifie un texte que {b} modifie aussi, {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez le texte de {b}.", kind_script: "un script", kind_script_archive: "une archive de scripts", kind_video: "une vidéo", kind_sound: "un son", kind_sound_archive: "une archive de sons", kind_picture: "une image", kind_map_file: "un fichier de carte", kind_text_file: "un fichier de textes", kind_game_data: "des données du jeu",
      update_out: "{app} {version} est disponible.", update_now: "Mettre à jour", whats_new: "Nouveautés", update_progress: "Téléchargement de la mise à jour… {pct}", update_installing: "Installation : {app} se ferme puis se rouvre automatiquement.", update_repo: "(Cette copie s'exécute depuis le dépôt Git : mettez-la à jour avec git pull.)", update_failed: "La mise à jour n'a pas fonctionné : {why}",
      guide_title: "Jouer avec des mods, en trois étapes", guide_add: "Ajoutez des mods : « Ajouter un fichier de mod… » à gauche, ou déposez le fichier dans cette fenêtre. Les mods de RUSE Studio (.rusemod), les mods de RUSE Mod Manager (.rmod) et les fichiers .zip fonctionnent tous. Ou trouvez-en un dans « Parcourir les mods ».", guide_set: "Créez un ensemble de mods : « Nouvel ensemble de mods… », cochez les mods et mettez-les dans l'ordre. Si deux mods modifient la même chose, le plus bas l'emporte.", guide_play: "Choisissez l'ensemble et appuyez sur Jouer. Le lanceur crée une copie distincte du jeu avec les mods et la démarre ; votre jeu Steam reste tel quel.", share: "Partager", share_title: "Partager cet ordre de chargement", share_help: "Copiez ceci et envoyez-le à un ami (Discord, un message…). Il l'importe dans RUSE Launcher (« Importer un ordre de chargement… ») ou dans RUSE Mod Manager et obtient les mêmes mods dans le même ordre. Il lui faut aussi les mods.", copy: "Copier", copied: "Copié.", import_order: "Importer un ordre de chargement…", import_help: "Collez un ordre de chargement partagé par un ami, depuis RUSE Launcher ou RUSE Mod Manager. Le nouvel ensemble de mods reçoit les mods que vous avez, dans le même ordre.", import_paste: "Collez l'ordre de chargement ici", check_order: "Vérifier", make_set: "Créer l'ensemble de mods", import_found: "Mods présents dans votre bibliothèque : {n} sur {total}.", import_missing: "Pas encore dans votre bibliothèque : {names}. Ajoutez-les (Ajouter un fichier de mod… ou Parcourir les mods) et importez à nouveau, ou créez l'ensemble sans eux.", import_version: "Dans votre bibliothèque, mais dans une autre version : {list}.", import_wrong_game: "Conçu pour l'autre version du jeu (R.U.S.E. ou R.U.S.E. COMPAT) : les mods risquent de ne pas convenir à la vôtre.", import_done: "Ensemble de mods « {name} » créé à partir de l'ordre de chargement partagé.",
      language: "Langue", looking: "Recherche de R.U.S.E.…", choose_folder: "Choisir le dossier…",
      mod_sets: "Ensembles de mods", vanilla: "Jeu d'origine", vanilla_desc: "Le jeu tel que Steam l'a installé.",
      no_mods: "Aucun mod", one_mod: "1 mod", n_mods: "{n} mods", has_mistake: "Contient une erreur",
      set_mistake: "Cet ensemble de mods contient une erreur : {error}", play: "Jouer", play_set: "Jouer {name}",
      getting_ready: "Préparation en cours…", details: "Détails", join: "Rejoindre un ami", browse: "Parcourir les mods",
      coming_soon: "Bientôt", new_set: "Nouvel ensemble de mods…", set_name: "Nom de l'ensemble de mods",
      tick_mods: "Cochez les mods à utiliser. Ils se chargent dans cet ordre : si deux modifient la même chose, le plus bas l'emporte.",
      save: "Enregistrer", cancel: "Annuler", create: "Créer", edit: "Modifier", rename: "Renommer", duplicate: "Dupliquer",
      delete: "Supprimer", really_delete_set: "Supprimer l'ensemble de mods {name} ? Ses mods restent dans la bibliothèque.",
      move_up: "Monter", move_down: "Descendre", copy_name: "{name} (copie)",
      set_saved: "L'ensemble de mods {name} a été enregistré.", set_deleted: "L'ensemble de mods {name} a été supprimé.",
      from_folder: "depuis un dossier",
      library_empty_for_set: "Ajoutez d'abord un mod à la bibliothèque : un ensemble de mods se compose des mods qui s'y trouvent.",
      library: "Bibliothèque de mods", add_mod: "Ajouter un fichier de mod…",
      drop_hint: "…ou déposez un dossier de mod ou un .zip n'importe où dans cette fenêtre.",
      drop_here: "Déposez-le pour l'ajouter à la bibliothèque", adding: "Ajout du mod…", remove: "Retirer",
      really_remove_mod: "Retirer {name} de la bibliothèque ? Les ensembles de mods qui l'utilisent ne fonctionneront plus tant qu'il n'est pas de retour.",
      version_v: "version {v}", by: "par {authors}", made_for: "conçu pour la version du jeu {builds}",
      your_build: "vous avez la {build}, il se peut qu'il ne convienne pas", used_in_one: "dans 1 ensemble de mods",
      used_in: "dans {n} ensembles de mods",
      library_empty: "Pas encore de mod. Ajoutez un fichier de mod, ou déposez-en un dans cette fenêtre.",
      mod_added: "{name} a été ajouté à la bibliothèque.", mod_updated: "{name} a été remplacé par la version {v}.",
      mod_removed: "{name} a été retiré de la bibliothèque.",
      search_mods: "Rechercher des mods", back: "Retour", install: "Installer", update_to: "Mettre à jour vers {v}",
      installed: "Installé", installing: "Installation…", offline_note: "Pas de connexion à la liste des mods. Voici la copie du {date}.",
      list_failed: "La liste des mods n'a pas pu être chargée : {why}", list_empty: "Aucun mod ne correspond.",
      for_build: "pour la version du jeu {build}", more_info: "En savoir plus sur ce mod", refresh_list: "Actualiser",
      browse_help: "Les mods de la liste de la communauté. Installer le place dans votre bibliothèque ; cochez-le ensuite dans un ensemble de mods." },
    sc: { settings_tab: "设置", settings_title: "设置", set_language_title: "语言", set_game_title: "游戏文件夹", set_game_path: "R.U.S.E. 位于 {path}。", set_game_none: "未找到 R.U.S.E.，请选择其文件夹。", set_game_change: "选择文件夹…", set_updates_title: "更新", set_updates_latest: "这是 RUSE Launcher {version}。每次打开时都会检查新版本。", set_updates_check: "立即检查", set_updates_checking: "正在查找新版本…", best_order: "按最佳顺序排列", best_order_why: "当两个模组修改同一内容时，靠下的模组优先。最佳顺序会把修改多的模组放在前面、较小的放在后面，让每个模组尽量保留自己的修改。", best_order_helps: "{names} 将保留大部分修改，而不是失去它们。", best_order_done: "{name}：模组已按最佳顺序排列。", clash_cant_play: "此组合无法游玩：", clash_overwrites: "后面的模组覆盖了前面的模组（{n}）：", clash_file: "{a} 和 {b} 都用不同的内容替换了同一个文件（{kind}）{file}。组合中只能保留其中一个。", clash_archive: "{a} 替换了整个归档 {file}，而 {b} 修改了其中的文件；两者之一会丢失。组合中只能保留其中一个。", clash_create: "{a} 和 {b} 各自添加了一个名为 {example} 的新对象；两个对象不能同名。组合中只能保留其中一个。", clash_value: "{a} 修改了 {b} 也修改过的 {n} 个数值，例如 {example}；它在后面，所以它优先。如果想要 {b} 的数值，请把 {b} 放到 {a} 后面。", clash_value_one: "{a} 修改了 {b} 也修改过的数值 {example}；它在后面，所以它优先。如果想要 {b} 的数值，请把 {b} 放到 {a} 后面。", clash_text: "{a} 修改了 {b} 也修改过的 {n} 条文本，例如 {example}；它在后面，所以它优先。如果想要 {b} 的文本，请把 {b} 放到 {a} 后面。", clash_text_one: "{a} 修改了 {b} 也修改过的文本 {example}；它在后面，所以它优先。如果想要 {b} 的文本，请把 {b} 放到 {a} 后面。", kind_script: "脚本", kind_script_archive: "脚本归档", kind_video: "视频", kind_sound: "音效", kind_sound_archive: "音效归档", kind_picture: "图片", kind_map_file: "地图文件", kind_text_file: "文本文件", kind_game_data: "游戏数据",
      update_out: "{app} {version} 已发布。", update_now: "更新", whats_new: "更新内容", update_progress: "正在下载更新… {pct}", update_installing: "正在安装：{app} 会自动关闭并重新打开。", update_repo: "（此副本从代码仓库运行：请用 git pull 更新。）", update_failed: "更新失败：{why}",
      guide_title: "使用模组游玩，只需三步", guide_add: "添加模组：点击左侧的“添加模组文件…”，或将文件拖放到此窗口。RUSE Studio 模组（.rusemod）、RUSE Mod Manager 模组（.rmod）和 .zip 文件都可以使用。也可以在“浏览模组”中查找。", guide_set: "创建模组组合：点击“新建模组组合…”，勾选模组并排好顺序。两个模组修改同一项时，下面的优先。", guide_play: "选择组合，然后点击“开始游戏”。启动器会创建一份单独的模组版游戏副本并启动它；你的 Steam 游戏保持原样。", share: "分享", share_title: "分享此加载顺序", share_help: "复制这段内容并发送给好友（Discord、消息…）。对方在 RUSE Launcher（“导入加载顺序…”）或 RUSE Mod Manager 中导入，即可按相同顺序获得相同的模组。对方也需要拥有这些模组。", copy: "复制", copied: "已复制。", import_order: "导入加载顺序…", import_help: "粘贴好友分享的加载顺序（来自 RUSE Launcher 或 RUSE Mod Manager）。新的模组组合会按相同顺序包含你已有的模组。", import_paste: "在此粘贴加载顺序", check_order: "检查", make_set: "创建模组组合", import_found: "{total} 个模组中有 {n} 个在你的库中。", import_missing: "库中尚无：{names}。请添加它们（“添加模组文件…”或“浏览模组”）后重新导入，或不含它们直接创建组合。", import_version: "库中版本不同的模组：{list}。", import_wrong_game: "为游戏的另一个版本（R.U.S.E. 或 R.U.S.E. COMPAT）制作：这些模组可能与你的版本不兼容。", import_done: "已根据分享的加载顺序创建模组组合“{name}”。",
      language: "语言", looking: "正在查找 R.U.S.E.…", choose_folder: "选择文件夹…", mod_sets: "模组组合", vanilla: "原版",
      vanilla_desc: "Steam 安装的原始游戏。", no_mods: "无模组", one_mod: "1 个模组", n_mods: "{n} 个模组", has_mistake: "有错误",
      set_mistake: "此模组组合有错误:{error}", play: "开始游戏", play_set: "以 {name} 开始游戏", getting_ready: "正在准备…",
      details: "详情", join: "加入好友", browse: "浏览模组", coming_soon: "即将推出", new_set: "新建模组组合…",
      set_name: "模组组合的名称", tick_mods: "勾选要使用的模组。按此顺序加载:两个模组修改同一项时,下面的优先。", save: "保存",
      cancel: "取消", create: "创建", edit: "编辑", rename: "重命名", duplicate: "复制", delete: "删除",
      really_delete_set: "删除模组组合 {name}?其中的模组仍保留在库中。", move_up: "上移", move_down: "下移",
      copy_name: "{name}(副本)", set_saved: "模组组合 {name} 已保存。", set_deleted: "模组组合 {name} 已删除。",
      from_folder: "来自文件夹", library_empty_for_set: "请先向库中添加模组:模组组合由库中的模组组成。", library: "模组库",
      add_mod: "添加模组文件…", drop_hint: "…或将模组文件夹或 .zip 拖放到此窗口的任意位置。", drop_here: "松开即可添加到库中",
      adding: "正在添加模组…", remove: "移除", really_remove_mod: "从库中移除 {name}?使用它的模组组合在它重新添加之前无法使用。",
      version_v: "版本 {v}", by: "作者:{authors}", made_for: "适用于游戏版本 {builds}", your_build: "你的版本是 {build},可能不兼容",
      used_in_one: "用于 1 个模组组合", used_in: "用于 {n} 个模组组合", library_empty: "还没有模组。请添加模组文件,或将其拖放到此窗口。",
      mod_added: "{name} 已添加到库中。", mod_updated: "{name} 已替换为版本 {v}。", mod_removed: "已从库中移除 {name}。",
      search_mods: "搜索模组", back: "返回", install: "安装", update_to: "更新到 {v}", installed: "已安装", installing: "正在安装…",
      offline_note: "无法连接到模组列表。这是 {date} 的副本。", list_failed: "无法加载模组列表：{why}", list_empty: "没有匹配的模组。",
      for_build: "适用于游戏版本 {build}", more_info: "关于此模组的更多信息", refresh_list: "刷新",
      browse_help: "来自社区列表的模组。安装后进入你的库；然后在模组组合中勾选它。" },
  };
  const build = "24687178";
  // Sample data for the preview only: mods that exist in the repo's mods/ folder, nobody's name on them.
  let library = mode === "empty" ? [] : [
    { id: "airfield-capacity", name: "Airfield Capacity", version: "1.0.0", authors: [], author: "",
      description: "Airfields hold 128 planes instead of 8.", builds: ["24087620"], used_in: 1 },
    { id: "passable-forests", name: "Passable Forests", version: "1.0.0", authors: [], author: "",
      description: "Tanks and other vehicles can enter forests, like recon units already can.", builds: ["24087620"], used_in: 1 },
    // made-up .rmod mods for the clash boxes (rusemod.rmod.clashes): two rewrite the same map script, two set ship speeds
    { id: "harbour-pack", name: "Harbour Pack", version: "2.1", authors: [], author: "", description: "Faster, tougher ships.",
      builds: [build], used_in: 1 },
    { id: "anchored-ships", name: "Anchored Ships", version: "1.0", authors: [], author: "", description: "Battleships stay put.",
      builds: [build], used_in: 1 },
    { id: "ardennes-rescripted", name: "Ardennes Rescripted", version: "1.0", authors: [], author: "",
      description: "A new script for the Ardennes mission.", builds: [build], used_in: 1 },
    { id: "ardennes-endless", name: "Ardennes Endless", version: "3.0", authors: [], author: "",
      description: "The Ardennes mission never ends.", builds: [build], used_in: 1 },
  ];
  let sets = mode === "empty" ? [] : [
    { id: "my-set", name: "My set", description: "", mods: ["airfield-capacity", "passable-forests"] },
    { id: "missing-mod", name: "Sample set with a missing mod", description: "", mods: ["some-other-mod"] },
    { id: "clashing", name: "Sample set with clashing mods", description: "", mods: ["anchored-ships", "harbour-pack", "ardennes-rescripted", "ardennes-endless"] },
  ];
  const wordsOf = (lang) => words[lang] || words.us;
  const known = (id) => library.find((m) => m.id === id);
  const resolve = (entry) => known(entry) ? null : /^[a-z0-9][a-z0-9-]*$/.test(entry)
    ? `it needs ${entry}, which isn't in the library (add it with “Add a mod file…”)` : null;
  const setView = (s) => {
    const errors = s.mods.map(resolve).filter(Boolean);
    return { id: s.id, name: s.name, description: s.description, mods: s.mods.slice(),
      mod_names: s.mods.map((m) => known(m) ? known(m).name : m.split("/").pop()),
      error: s.mods.length ? errors[0] || null : "it lists no mods", editable: true };
  };
  const modSets = () => [{ id: "vanilla", name: "Vanilla", description: "The game as Steam installed it.", mods: [],
    mod_names: [], error: null, editable: false }].concat(sets.map(setView));
  const used = () => library.map((m) => ({ ...m, used_in: sets.filter((s) => s.mods.includes(m.id)).length }));
  const lists = (extra) => ({ library: used(), sets: modSets(), ...(extra || {}) });
  const slug = (name) => {
    const base = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "mod-set";
    let id = base, n = 2;
    while (id === "vanilla" || sets.some((s) => s.id === id)) id = `${base}-${n++}`;
    return id;
  };
  // what rusemod.rmod.clashes would say about these mods: a hard clash when both Ardennes mods are in (the same script
  // with different contents), a soft one when Harbour Pack and Anchored Ships both set the ships' values
  const clashesOf = (mods) => {
    const name = (id) => (known(id) || { name: id }).name;
    const hard = [], soft = [];
    if (mods.includes("ardennes-rescripted") && mods.includes("ardennes-endless")) {
      const pair = mods.filter((m) => m === "ardennes-rescripted" || m === "ardennes-endless").map(name);
      hard.push({ kind: "file", hard: true, mods: pair, what: "genpython/1000/test/map/m06_ardennes/scripting_chapter1/effetmap.xyz",
        message: `${pair[0]} and ${pair[1]} each replace the same script, effetmap.xyz, with different contents. Only one of them can be in a set.`,
        count: 1, file_kind: "script", a: pair[0], b: pair[1] });
    }
    if (mods.includes("harbour-pack") && mods.includes("anchored-ships")) {
      const pair = mods.filter((m) => m === "harbour-pack" || m === "anchored-ships").map(name);
      soft.push({ kind: "value", hard: false, mods: pair, what: "Unit_Battleship.VitesseLineaire",
        message: `${pair[1]} changes 8 values ${pair[0]} changed too, e.g. Unit_Battleship.VitesseLineaire; it comes later, so it wins.`,
        count: 8, file_kind: "", a: pair[1], b: pair[0] });
    }
    // the best order (rusemod.rmod.best_order): Harbour Pack changes more, so it goes first and Anchored Ships keeps its 8
    let best = null, helped = [];
    const [h, a] = [mods.indexOf("harbour-pack"), mods.indexOf("anchored-ships")];
    if (h >= 0 && a >= 0 && a < h) {
      best = mods.slice();
      [best[a], best[h]] = [best[h], best[a]];
      helped = ["Anchored Ships"];
    }
    return { hard, soft, best, helped };
  };
  const checkMods = (mods) => {
    if (!mods || !mods.length) throw new Error("Tick at least one mod for this mod set.");
    for (const m of mods) { const why = resolve(m); if (why) throw new Error(`This mod set can't be saved: ${why}.`); }
  };
  const fakeMod = (name) => {
    const id = name.toLowerCase().replace(/\.zip$/, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "mod";
    if (id.endsWith("exe")) throw new Error(`${name} isn't a mod: add a mod folder (with mod.toml in it) or a .zip of one.`);
    const replaced = Boolean(known(id));
    library = library.filter((m) => m.id !== id);
    const mod = { id, name: name.replace(/\.zip$/, ""), version: replaced ? "1.1.0" : "1.0.0", authors: [], author: "",
      description: "Added from a file.", builds: [build], used_in: 0 };
    library.push(mod);
    library.sort((a, b) => a.name.localeCompare(b.name));
    return lists({ mod, replaced });
  };
  const script = [
    "Building the modded copy of R.U.S.E. for My set in D:\\RUSE-Instances\\my-set…",
    "load order: airfield-capacity -> passable-forests",
    "  note     left 4 debug-info copies as shipped (everything_debuginfo.cpp.gladndfbin, …)",
    "0 error(s), 0 warning(s), 3 note(s)",
    "changed: genglad\\patchable\\gfx\\everything.cpp.gladndfbin",
    "fingerprint: S1HP-X6PM",
    "modded copy ready: D:\\RUSE-Instances\\my-set  {'linked': 37, 'copied': 23, 'written': 1}",
    "Starting R.U.S.E. from the modded copy…",
  ];
  // Sample data for the preview only: mods from the repo's mods/ folder with their real sizes and checksums; the
  // download links are placeholders until the mod index repository exists (MOD_FORMAT §15).
  const listed = [
    { id: "airfield-capacity", name: "Airfield Capacity", version: "1.0.0", author: "", description: "Raises the number of planes that can fit in an Airfield from 8 to 128.",
      homepage: "https://github.com/sneadtristen6/Ruse-Mod-Platform/tree/main/mods/airfield-capacity",
      download: "https://example.invalid/airfield-capacity-1.0.0.rusemod", size: 1315, sha256: "ae22dfd4ab5ff56254fff98e8d8a27b486f4ec5c821db83211c62b35aeb0f25a",
      game_build: "24087620", fingerprint: "", tags: ["air"] },
    { id: "passable-forests", name: "Passable Forests", version: "1.0.0", author: "", description: "Lets every tank, tank destroyer, AA vehicle, and mobile artillery/assault gun enter forest terrain the way recon vehicles already can, by removing the InitialFlagSet flags (11, 21, 55) that block forest entry. Confirmed in-game on the M4 Sherman before rolling out to the full roster.",
      homepage: "https://github.com/sneadtristen6/Ruse-Mod-Platform/tree/main/mods/passable-forests",
      download: "https://example.invalid/passable-forests-1.0.0.rusemod", size: 2744, sha256: "1fe29ca1b796b3e6034f1a4710d6ed0f10236f487ec88492a3550b19692d2102",
      game_build: "24087620", fingerprint: "", tags: ["movement"] },
    { id: "cheat-mod-v2", name: "Cheat Mod 2.0", version: "2.0.0", author: "", description: "Every unit AND every building costs $1 to build, every unit's ProductionTime is 0, and the global MinProductionTime floor is lowered to 0.01 seconds so 0-second production actually takes effect instead of being clamped back up to 1 second. Extends the example Cheat Mod (units-only $1 pricing) with building pricing and the confirmed-working instant-production fix.",
      homepage: "https://github.com/sneadtristen6/Ruse-Mod-Platform/tree/main/mods/cheat-mod-v2",
      download: "https://example.invalid/cheat-mod-v2-2.0.0.rusemod", size: 4918, sha256: "e010c5cc810fdc29a84704f4bc73dedd671132bd18adb9896e2867a03fae587c",
      game_build: "24087620", fingerprint: "", tags: ["testing"] },
  ];
  const sizeText = (n) => n < 1e6 ? `${Math.max(1, Math.round(n / 1000))} KB` : `${(n / 1e6).toFixed(1)} MB`;
  const browseView = (search) => {
    const q = (search || "").toLowerCase();
    const have = Object.fromEntries(library.map((m) => [m.id, m.version]));
    const mods = listed.filter((m) => !q || `${m.id} ${m.name} ${m.author} ${m.description} ${m.tags.join(" ")}`.toLowerCase().includes(q))
      .map((m) => ({ ...m, state: !have[m.id] ? "new" : have[m.id] < m.version ? "update" : "installed",
        installed_version: have[m.id] || "", size_text: sizeText(m.size) }));
    return { mods, source: mode === "offline" ? "cache" : "online", as_of: "2026-09-29 20:30", message: "", problems: [] };
  };
  let playing = null;
  window.pywebview = {
    api: {
      languages: async () => [{ code: "us", name: "English" }, { code: "fr", name: "Français" }, { code: "ger", name: "Deutsch" },
        { code: "ita", name: "Italiano" }, { code: "spa", name: "Español" }, { code: "pol", name: "Polski" },
        { code: "ru", name: "Русский" }, { code: "cz", name: "Čeština" }, { code: "jpn", name: "日本語" }, { code: "sc", name: "简体中文" }],
      default_language: async () => "us",
      strings: async (lang) => wordsOf(lang),
      status: async () => mode === "notfound"
        ? { found: false, message: "We couldn't find R.U.S.E. Is it installed through Steam?" }
        : { found: true, game_dir: "D:\\Steam\\steamapps\\common\\R.U.S.E", build, drive: "D:",
            message: `Found R.U.S.E. on D: (build ${build})` },
      choose_game_folder: async () => ({ found: true, drive: "D:", build, message: `Found R.U.S.E. on D: (build ${build})` }),
      update_check: async () => mode === "update"
        ? { available: true, version: "9.9.9", installed: true, size: 60000000,
            page: "https://github.com/sneadtristen6/Ruse-Mod-Platform/releases" }
        : { available: false, version: "0.2.6" },
      update_install: async () => { throw new Error("The preview can't install updates."); },
      update_page: async () => ({ opened: "" }),
      library: async () => used(),
      mod_sets: async () => modSets(),
      add_mod: async (path) => fakeMod(path.split(/[\\/]/).pop()),
      add_mod_file: async () => fakeMod("Pacific Maps.zip"),
      remove_mod: async (id) => {
        const mod = known(id);
        if (!mod) throw new Error(`There's no mod called '${id}' in the library.`);
        library = library.filter((m) => m.id !== id);
        return lists({ mod });
      },
      new_set: async (name, mods) => {
        if (!name.trim()) throw new Error("Give the mod set a name.");
        checkMods(mods);
        const id = slug(name);
        sets.push({ id, name: name.trim(), description: "", mods: mods.slice() });
        return lists({ set: id });
      },
      save_set: async (id, name, mods) => {
        const s = sets.find((x) => x.id === id);
        if (!s) throw new Error(`There's no mod set called '${id}' any more. Pick another one.`);
        if (mods) { checkMods(mods); s.mods = mods.slice(); }
        if (name && name.trim()) s.name = name.trim();
        return lists({ set: id });
      },
      duplicate_set: async (id, name) => {
        const s = sets.find((x) => x.id === id);
        const copy = { id: slug(name), name, description: s.description, mods: s.mods.slice() };
        sets.push(copy);
        return lists({ set: copy.id });
      },
      check_mods: async (mods) => clashesOf(mods || []),
      prefs: async () => ({ ...prefs }),
      set_pref: async (key, value) => { if (value === null) delete prefs[key]; else prefs[key] = value; return { ...prefs }; },
      set_check: async (id) => clashesOf((sets.find((x) => x.id === id) || { mods: [] }).mods),
      best_order: async (id) => {
        const s = sets.find((x) => x.id === id);
        const best = clashesOf(s.mods).best;
        if (best) s.mods = best;
        return lists({ set: id });
      },
      delete_set: async (id) => {
        sets = sets.filter((x) => x.id !== id);
        return lists({ set: "vanilla" });
      },
      // a load order to share, and one pasted in: the same text RUSE Mod Manager uses (rusemod/loadorder.py)
      share_set: async (id) => {
        const s = sets.find((x) => x.id === id);
        const rows = s.mods.map((m, i) => `${i + 1}. ${known(m) ? `${known(m).name} | v${known(m).version}` : m}`);
        return { text: ["=== R.U.S.E. Load Order ===", `Set: ${s.name}`, `Game build: ${build}`, ...rows,
          "=== End Load Order ==="].join("\n") + "\n" };
      },
      import_check: async (text) => {
        const lines = (text || "").split(/\r?\n/).map((l) => l.trim());
        const start = lines.findIndex((l) => l.includes("Load Order") && l.includes("R.U.S.E.") && !l.includes("End"));
        if (start < 0) throw new Error("There's no load order in that text. A shared load order starts with a line like “=== R.U.S.E. Load Order ===”: copy the whole block.");
        const found = [], missing = [], other = [];
        let setName = "";
        for (const l of lines.slice(start + 1)) {
          if (l.includes("End Load Order")) break;
          if (/^set:/i.test(l)) { setName = l.slice(4).trim(); continue; }
          const m = /^\d+\.\s+(.+)$/.exec(l);
          if (!m) continue;
          const [name, version] = m[1].includes(" | v") ? m[1].split(" | v") : [m[1], ""];
          const mod = library.find((x) => x.name.toLowerCase() === name.replace(/^\[COMPAT\] /, "").trim().toLowerCase());
          if (!mod) { missing.push({ name: name.trim(), version: version.trim() }); continue; }
          found.push({ id: mod.id, name: mod.name, version: mod.version });
          if (version && version.trim() !== mod.version) other.push({ name: mod.name, have: mod.version, wanted: version.trim() });
        }
        return { set_name: setName, mode: "public", build: "", wrong_game: false, found, missing, other_version: other, repeated: [] };
      },
      import_set: async (text, name) => {
        const check = await window.pywebview.api.import_check(text);
        if (!check.found.length) throw new Error("None of these mods are in your library yet.");
        const id = slug(name || check.set_name || "Shared load order");
        sets.push({ id, name: name || check.set_name || "Shared load order", description: "", mods: check.found.map((f) => f.id) });
        return lists({ set: id, import: check });
      },
      play: async (id) => {
        playing = { id, step: 0, lines: id === "vanilla" ? ["Starting R.U.S.E. through Steam…"] : script,
          message: "R.U.S.E. is starting." };
        return { job: "fake" };
      },
      browse: async (search) => browseView(search),
      install_from_index: async (id) => {
        const m = listed.find((x) => x.id === id);
        if (!m) throw new Error(`There's no mod called '${id}' in the mod list.`);
        playing = { id: "install", step: 0, message: `${m.name} is in the library.`,
          lines: [`Downloading ${m.name} ${m.version} (${sizeText(m.size)})…`, "The file matches the mod list (size and checksum).",
            `${m.name} ${m.version} is in the library.`],
          then: () => { library = library.filter((x) => x.id !== m.id); library.push({ id: m.id, name: m.name, version: m.version,
            authors: m.author ? [m.author] : [], author: m.author, description: m.description, builds: m.game_build ? [m.game_build] : [],
            used_in: 0 }); library.sort((a, b) => a.name.localeCompare(b.name)); } };
        return { job: "install" };
      },
      open_link: async (url) => ({ opened: url }),
      job: async (_job, since) => {
        playing.step = Math.min(playing.step + 2, playing.lines.length);
        const done = playing.step >= playing.lines.length;
        if (done && playing.then) { playing.then(); playing.then = null; }
        return { id: "fake", state: done ? "done" : "running", message: done ? playing.message : "",
          lines: playing.lines.slice(since, playing.step), count: playing.step };
      },
    },
  };
  // In the real window pywebview hands dropped files' paths to the launcher, which then tells the page; here the
  // page's own drop event has to do (a file's name stands in for the mod).
  window.addEventListener("drop", (e) => {
    for (const f of e.dataTransfer ? e.dataTransfer.files : []) {
      let detail;
      try { detail = { ok: true, ...fakeMod(f.name) }; } catch (err) { detail = { ok: false, message: err.message }; }
      setTimeout(() => window.dispatchEvent(new CustomEvent("mod-dropped", { detail })), 300);
    }
  });
  window.addEventListener("load", () => window.dispatchEvent(new Event("pywebviewready")));
})();
