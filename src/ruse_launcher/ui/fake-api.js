// A made-up LauncherApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=notfound shows the "game not found" state, ?fake=empty a launcher with no mods yet, ?fake=first its first
// run ("Choose your mods"), ?fake=firstoffline the first run with no list to show, ?fake=offline the list's saved
// copy, ?fake=installfail one mod of several that fails its check; ?fake=backup,
// ?fake=oldbackup, ?fake=nospace and ?fake=running the clean game backup's states, in Settings; ?fake=firstbackup the
// installer's "Keep a clean copy" ask, made on the first start; ?fake=lang "Choose your language" with the game set to
// French in Steam). Only English, French
// and Chinese words are included here; the real launcher has all ten languages. It does nothing in the real window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const prefs = {};  // what the real app keeps in settings.json (rusemod.home.PrefsCalls)
  const words = {
    us: { settings_tab: "Settings", settings_title: "Settings", set_language_title: "Language", set_game_title: "Game folder", set_game_path: "R.U.S.E. is in {path}.", set_game_none: "R.U.S.E. wasn't found. Pick its folder.", set_game_change: "Choose folder…", set_updates_title: "Updates", set_updates_latest: "This is RUSE Launcher {version}. It looks for a newer one each time it opens.", set_updates_check: "Check now", set_updates_checking: "Looking for a newer version…", best_order: "Put in best order", best_order_why: "Where two mods change the same thing, the lower one wins. The best order puts the mods that change more first and the smaller ones after, so each keeps as much as it can.", best_order_helps: "{names} would keep most of their changes instead of losing them.", best_order_done: "{name}: mods put in the best order.", clash_cant_play: "This set can't be played:", clash_overwrites: "Later mods overwrite earlier ones ({n}):", clash_file: "{a} and {b} both replace the same file, {file} ({kind}), with different contents. Only one of them can be in a set.", clash_archive: "{a} replaces the whole archive {file}, and {b} changes files inside it; one of the two would be lost. Only one of them can be in a set.", clash_create: "{a} and {b} each add a new object called {example}; two objects can't share a name. Only one of them can be in a set.", clash_value: "{a} changes {n} values {b} changed too, e.g. {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s values.", clash_value_one: "{a} changes a value {b} changed too, {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s value.", clash_text: "{a} changes {n} texts {b} changed too, e.g. {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s texts.", clash_text_one: "{a} changes a text {b} changed too, {example}; it comes later, so it wins. Put {b} after {a} if you want {b}'s text.", kind_script: "a script", kind_script_archive: "a script archive", kind_video: "a video", kind_sound: "a sound", kind_sound_archive: "a sound archive", kind_picture: "a picture", kind_map_file: "a map file", kind_text_file: "a text file", kind_game_data: "game data",
      update_out: "{app} {version} is out.", update_now: "Update", whats_new: "What's new", release_page: "Release page", changes_before: "In your version ({version})", changes_now: "In {version}", changes_none: "The release notes list no changes: open the release page for them.", update_progress: "Downloading the update… {pct}", update_installing: "Installing: {app} closes and opens again by itself.", update_repo: "(This copy runs from the repo: update it with git pull.)", update_failed: "The update didn't work: {why}",
      doc_button: "Troubleshoot", doc_title: "Troubleshooter", doc_intro: "What can stop a test or Play, checked in one go.", doc_checking: "Checking…", doc_again: "Check again", doc_copy: "Copy report", doc_copied: "Report copied: paste it into your bug report or on Discord.", doc_close: "Close", doc_fix_close_game: "Close R.U.S.E.", doc_fix_clear_leftovers: "Clear them", doc_fix_choose_game: "Choose folder…", doc_fixed: "Done ({done}).", doc_fix_left: "Not everything could be done: {left}", doc_game_ok: "R.U.S.E. found: {path}", doc_game_missing: "R.U.S.E. wasn't found. Choose its folder (the one with RUSE.exe).", doc_steam_ok: "Steam is running.", doc_steam_off: "Steam isn't running. It's started for you when you play.", doc_running_none: "No R.U.S.E. left running.", doc_running_copy: "R.U.S.E. is still running from a modded copy: {names}. Close it before the next test or Play.", doc_running_game: "R.U.S.E. is running (the Steam game): {names}. Close it before testing mods.", doc_drive_ok: "Modded copies go to {path} ({fs}).", doc_drive_other: "Modded copies go to {path}, on a {fs} drive: each copy is a full copy, and Windows may refuse to delete one while R.U.S.E. runs. An NTFS drive is best.", doc_space_ok: "{gb} GB free for modded copies.", doc_space_low: "Only {gb} GB free where modded copies go: a copy may need {need} GB.", doc_left_none: "No leftover copies.", doc_left: "Leftover copies: {names}. They only take up space; you can clear them now.", doc_left_held: "Leftover copies: {names}, held by {held}. Close that program, then clear them.", doc_readonly: "{n} of the game's files are marked read-only. That's fine: modded copies never keep the mark.", doc_write_ok: "The app can write where modded copies go.", doc_write_fail: "The app can't write to {path} ({why}). Check that folder's permissions, or whether an antivirus blocks it, or choose another folder for modded copies in Settings.", doc_troubleshoot_link: "Troubleshoot",
      set_copies_title: "Where modded copies go", set_copies_help: "Play builds the modded copy of the game in this folder. The recommended place is RUSE-Instances on the game's drive: there the copy shares the game's files and is ready in seconds. On another drive it is a full copy of the game, slower and bigger. The game's clean backup goes beside it, in RUSE-Backup. After a change, the next Play builds in the new place; the old folder only takes up space and can be deleted by hand.", set_copies_none: "R.U.S.E. wasn't found yet, so the recommended place isn't known. Pick the game folder first.", set_copies_change: "Choose folder…", set_copies_default: "Use the recommended place", set_copies_changed: "Modded copies now go to {path}. The next Play builds there; the old folder only takes up space and can be deleted by hand.", set_copies_fixed: "Modded copies go to {path}, the folder given when the app started.", tip_copies_change: "Pick the folder the modded copies of the game are built in; the old folder stays until you delete it.", tip_copies_default: "Build the modded copies in RUSE-Instances on the game's drive again, the recommended place.", tip_copies_default_off: "Modded copies already go to the recommended place.", tip_copies_fixed: "The folder was given when the app started, so it can't be changed here.", doc_copies_recommended: "Modded copies go to {path}, the recommended place.", doc_copies_chosen: "Modded copies go to {path}, the folder chosen in Settings.", doc_copies_env: "Modded copies go to {path}, set by the RUSE_INSTANCES environment variable.", doc_copies_other_drive: "{path} is on another drive than the game ({drive}): each modded copy is a full copy of the game, slower to build and as big as the game. The recommended place is {recommended}.",
      guide_title: "Playing with mods, in three steps", guide_add: "Add mods: “Add a mod file…” on the left, or drop the file on this window. RUSE Studio mods (.rusemod), RUSE Mod Manager mods (.rmod) and .zip files all work. Or find one under “Supported mods”.", guide_set: "Make a mod set: “New mod set…”, tick the mods and put them in order. Where two mods change the same thing, the lower one wins.", guide_play: "Pick the set and press Play. The launcher builds a separate modded copy of the game and starts it; your Steam game stays as it is.", share: "Share", share_title: "Share this load order", share_help: "Copy this and send it to a friend (Discord, a message…). They import it in RUSE Launcher (“Import a load order…”) or in RUSE Mod Manager and get the same mods in the same order. They need the mods too.", copy: "Copy", copied: "Copied.", import_order: "Import a load order…", import_help: "Paste a load order a friend shared, from RUSE Launcher or RUSE Mod Manager. The new mod set gets the mods you have, in the same order.", import_paste: "Paste the load order here", check_order: "Check", make_set: "Make the mod set", import_found: "{n} of {total} mods are in your library.", import_missing: "Not in your library yet: {names}. Add them (Add a mod file… or Supported mods) and import again, or make the set without them.", import_version: "In your library in another version: {list}.", import_wrong_game: "Made for the other version of the game (R.U.S.E. or R.U.S.E. COMPAT): the mods may not fit yours.", import_done: "Mod set “{name}” made from the shared load order.",
      language: "Language", looking: "Looking for R.U.S.E.…", choose_folder: "Choose folder…", mod_sets: "Mod sets",
      vanilla: "Vanilla", vanilla_desc: "The game with no mods.", no_mods: "No mods", one_mod: "1 mod",
      n_mods: "{n} mods", has_mistake: "Has a mistake", set_mistake: "This mod set has a mistake: {error}", play: "Play",
      play_set: "Play {name}", getting_ready: "Getting everything ready…", details: "Details", join: "Join a friend",
      browse: "Supported mods", mod_check_warn: "The mod check found {n} problem(s) Play would stop at; its author can fix them:", report_problem: "Report a problem", tip_report_problem: "Opens a bug report in your browser, with the app and its version filled in. You read it and post it yourself.", report: "Report", tip_report: "Report this as a bug: your browser opens a report with this message filled in (paths without your user name).", help: "Help", tip_help: "Opens the wiki in your browser: how to add mods, play and play with friends.", coming_soon: "Coming soon", new_set: "New mod set…", set_name: "Name of the mod set",
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
      library_search: "Search your mods", library_count: "{n} mods", library_no_match: "No mod matches “{q}”.", library_empty: "No mods yet. Add a mod file, or drop one on this window.", mod_added: "{name} was added to the library.",
      mod_updated: "{name} was replaced by version {v}.", mod_removed: "{name} was removed from the library.",
      search_mods: "Search mods", back: "Back", install: "Install", update_to: "Update to {v}", installed: "Installed",
      installing: "Installing…", offline_note: "No connection to the mod list. This is the copy from {date}.",
      list_failed: "The mod list couldn't be loaded: {why}", list_empty: "No mods match.", for_build: "for game build {build}",
      more_info: "More about this mod", refresh_list: "Refresh",
      browse_help: "Mods from the community's list. Install puts one in your library; then tick it in a mod set." },
    fr: { settings_tab: "Réglages", settings_title: "Réglages", set_language_title: "Langue", set_game_title: "Dossier du jeu", set_game_path: "R.U.S.E. est dans {path}.", set_game_none: "R.U.S.E. est introuvable. Choisissez son dossier.", set_game_change: "Choisir le dossier…", set_updates_title: "Mises à jour", set_updates_latest: "Ceci est RUSE Launcher {version}. Il cherche une version plus récente à chaque ouverture.", set_updates_check: "Vérifier", set_updates_checking: "Recherche d'une version plus récente…", best_order: "Mettre dans le meilleur ordre", best_order_why: "Là où deux mods changent la même chose, celui du bas l'emporte. Le meilleur ordre met d'abord les mods qui changent le plus et les plus petits après, pour que chacun garde le plus possible.", best_order_helps: "{names} garderaient la plupart de leurs changements au lieu de les perdre.", best_order_done: "{name} : mods mis dans le meilleur ordre.", clash_cant_play: "Cet ensemble ne peut pas être joué :", clash_overwrites: "Des mods plus bas écrasent des mods plus haut ({n}) :", clash_file: "{a} et {b} remplacent tous deux le même fichier ({kind}), {file}, avec des contenus différents. Un seul d'entre eux peut être dans un ensemble.", clash_archive: "{a} remplace toute l'archive {file}, et {b} modifie des fichiers à l'intérieur ; l'un des deux serait perdu. Un seul d'entre eux peut être dans un ensemble.", clash_create: "{a} et {b} ajoutent chacun un nouvel objet nommé {example} ; deux objets ne peuvent pas porter le même nom. Un seul d'entre eux peut être dans un ensemble.", clash_value: "{a} modifie {n} valeurs que {b} modifie aussi, par ex. {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez les valeurs de {b}.", clash_value_one: "{a} modifie une valeur que {b} modifie aussi, {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez la valeur de {b}.", clash_text: "{a} modifie {n} textes que {b} modifie aussi, par ex. {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez les textes de {b}.", clash_text_one: "{a} modifie un texte que {b} modifie aussi, {example} ; il vient après, donc il l'emporte. Placez {b} après {a} si vous voulez le texte de {b}.", kind_script: "un script", kind_script_archive: "une archive de scripts", kind_video: "une vidéo", kind_sound: "un son", kind_sound_archive: "une archive de sons", kind_picture: "une image", kind_map_file: "un fichier de carte", kind_text_file: "un fichier de textes", kind_game_data: "des données du jeu",
      update_out: "{app} {version} est disponible.", update_now: "Mettre à jour", whats_new: "Nouveautés", update_progress: "Téléchargement de la mise à jour… {pct}", update_installing: "Installation : {app} se ferme puis se rouvre automatiquement.", update_repo: "(Cette copie s'exécute depuis le dépôt Git : mettez-la à jour avec git pull.)", update_failed: "La mise à jour n'a pas fonctionné : {why}",
      doc_button: "Dépannage", doc_title: "Dépannage", doc_intro: "Tout ce qui peut bloquer un test ou Jouer, vérifié d'un coup.", doc_checking: "Vérification…", doc_again: "Vérifier à nouveau", doc_copy: "Copier le rapport", doc_copied: "Rapport copié : collez-le dans votre rapport de bug ou sur Discord.", doc_close: "Fermer", doc_fix_close_game: "Fermer R.U.S.E.", doc_fix_clear_leftovers: "Les supprimer", doc_fix_choose_game: "Choisir le dossier…", doc_fixed: "Fait ({done}).", doc_fix_left: "Tout n'a pas pu être fait : {left}", doc_game_ok: "R.U.S.E. trouvé : {path}", doc_game_missing: "R.U.S.E. est introuvable. Choisissez son dossier (celui qui contient RUSE.exe).", doc_steam_ok: "Steam est lancé.", doc_steam_off: "Steam n'est pas lancé. Il sera démarré pour vous quand vous jouerez.", doc_running_none: "Aucun R.U.S.E. resté ouvert.", doc_running_copy: "R.U.S.E. tourne encore depuis une copie avec les mods : {names}. Fermez-le avant le prochain test ou Jouer.", doc_running_game: "R.U.S.E. est lancé (le jeu Steam) : {names}. Fermez-le avant de tester des mods.", doc_drive_ok: "Les copies avec les mods vont dans {path} ({fs}).", doc_drive_other: "Les copies avec les mods vont dans {path}, sur un disque {fs} : chaque copie est complète, et Windows peut refuser d'en supprimer une tant que R.U.S.E. tourne. Un disque NTFS est préférable.", doc_space_ok: "{gb} Go libres pour les copies avec les mods.", doc_space_low: "Seulement {gb} Go libres là où vont les copies avec les mods : une copie peut demander {need} Go.", doc_left_none: "Aucune copie restante.", doc_left: "Copies restantes : {names}. Elles ne font qu'occuper de la place ; vous pouvez les supprimer dès maintenant.", doc_left_held: "Copies restantes : {names}, bloquées par {held}. Fermez ce programme, puis supprimez-les.", doc_readonly: "{n} fichiers du jeu sont en lecture seule. Pas de souci : les copies avec les mods ne gardent jamais cet attribut.", doc_write_ok: "L'application peut écrire là où vont les copies avec les mods.", doc_write_fail: "L'application ne peut pas écrire dans {path} ({why}). Vérifiez les autorisations de ce dossier, ou si un antivirus le bloque, ou choisissez un autre dossier pour les copies avec les mods dans les Réglages.", doc_troubleshoot_link: "Dépannage",
      guide_title: "Jouer avec des mods, en trois étapes", guide_add: "Ajoutez des mods : « Ajouter un fichier de mod… » à gauche, ou déposez le fichier dans cette fenêtre. Les mods de RUSE Studio (.rusemod), les mods de RUSE Mod Manager (.rmod) et les fichiers .zip fonctionnent tous. Ou trouvez-en un dans « Mods compatibles ».", guide_set: "Créez un ensemble de mods : « Nouvel ensemble de mods… », cochez les mods et mettez-les dans l'ordre. Si deux mods modifient la même chose, le plus bas l'emporte.", guide_play: "Choisissez l'ensemble et appuyez sur Jouer. Le lanceur crée une copie distincte du jeu avec les mods et la démarre ; votre jeu Steam reste tel quel.", share: "Partager", share_title: "Partager cet ordre de chargement", share_help: "Copiez ceci et envoyez-le à un ami (Discord, un message…). Il l'importe dans RUSE Launcher (« Importer un ordre de chargement… ») ou dans RUSE Mod Manager et obtient les mêmes mods dans le même ordre. Il lui faut aussi les mods.", copy: "Copier", copied: "Copié.", import_order: "Importer un ordre de chargement…", import_help: "Collez un ordre de chargement partagé par un ami, depuis RUSE Launcher ou RUSE Mod Manager. Le nouvel ensemble de mods reçoit les mods que vous avez, dans le même ordre.", import_paste: "Collez l'ordre de chargement ici", check_order: "Vérifier", make_set: "Créer l'ensemble de mods", import_found: "Mods présents dans votre bibliothèque : {n} sur {total}.", import_missing: "Pas encore dans votre bibliothèque : {names}. Ajoutez-les (Ajouter un fichier de mod… ou Mods compatibles) et importez à nouveau, ou créez l'ensemble sans eux.", import_version: "Dans votre bibliothèque, mais dans une autre version : {list}.", import_wrong_game: "Conçu pour l'autre version du jeu (R.U.S.E. ou R.U.S.E. COMPAT) : les mods risquent de ne pas convenir à la vôtre.", import_done: "Ensemble de mods « {name} » créé à partir de l'ordre de chargement partagé.",
      language: "Langue", looking: "Recherche de R.U.S.E.…", choose_folder: "Choisir le dossier…",
      mod_sets: "Ensembles de mods", vanilla: "Jeu d'origine", vanilla_desc: "Le jeu sans mods.",
      no_mods: "Aucun mod", one_mod: "1 mod", n_mods: "{n} mods", has_mistake: "Contient une erreur",
      set_mistake: "Cet ensemble de mods contient une erreur : {error}", play: "Jouer", play_set: "Jouer {name}",
      getting_ready: "Préparation en cours…", details: "Détails", join: "Rejoindre un ami", browse: "Mods compatibles", mod_check_warn: "La vérification a trouvé {n} problème(s) qui bloqueraient Jouer ; son auteur peut les corriger :", report_problem: "Signaler un problème", tip_report_problem: "Ouvre un rapport de bug dans votre navigateur, avec l'application et sa version déjà remplies. Vous le relisez et le publiez vous-même.", report: "Signaler", tip_report: "Signaler ce bug : le navigateur ouvre un rapport avec ce message (chemins sans votre nom d'utilisateur).", help: "Aide", tip_help: "Ouvre le wiki dans le navigateur : ajouter des mods, jouer, jouer entre amis.",
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
      library_search: "Chercher dans vos mods", library_count: "{n} mods", library_no_match: "Aucun mod ne correspond à « {q} ».", library_empty: "Pas encore de mod. Ajoutez un fichier de mod, ou déposez-en un dans cette fenêtre.",
      mod_added: "{name} a été ajouté à la bibliothèque.", mod_updated: "{name} a été remplacé par la version {v}.",
      mod_removed: "{name} a été retiré de la bibliothèque.",
      search_mods: "Rechercher des mods", back: "Retour", install: "Installer", update_to: "Mettre à jour vers {v}",
      installed: "Installé", installing: "Installation…", offline_note: "Pas de connexion à la liste des mods. Voici la copie du {date}.",
      list_failed: "La liste des mods n'a pas pu être chargée : {why}", list_empty: "Aucun mod ne correspond.",
      for_build: "pour la version du jeu {build}", more_info: "En savoir plus sur ce mod", refresh_list: "Actualiser",
      browse_help: "Les mods de la liste de la communauté. Installer le place dans votre bibliothèque ; cochez-le ensuite dans un ensemble de mods." },
    sc: { settings_tab: "设置", settings_title: "设置", set_language_title: "语言", set_game_title: "游戏文件夹", set_game_path: "R.U.S.E. 位于 {path}。", set_game_none: "未找到 R.U.S.E.，请选择其文件夹。", set_game_change: "选择文件夹…", set_updates_title: "更新", set_updates_latest: "这是 RUSE Launcher {version}。每次打开时都会检查新版本。", set_updates_check: "立即检查", set_updates_checking: "正在查找新版本…", best_order: "按最佳顺序排列", best_order_why: "当两个模组修改同一内容时，靠下的模组优先。最佳顺序会把修改多的模组放在前面、较小的放在后面，让每个模组尽量保留自己的修改。", best_order_helps: "{names} 将保留大部分修改，而不是失去它们。", best_order_done: "{name}：模组已按最佳顺序排列。", clash_cant_play: "此组合无法游玩：", clash_overwrites: "后面的模组覆盖了前面的模组（{n}）：", clash_file: "{a} 和 {b} 都用不同的内容替换了同一个文件（{kind}）{file}。组合中只能保留其中一个。", clash_archive: "{a} 替换了整个归档 {file}，而 {b} 修改了其中的文件；两者之一会丢失。组合中只能保留其中一个。", clash_create: "{a} 和 {b} 各自添加了一个名为 {example} 的新对象；两个对象不能同名。组合中只能保留其中一个。", clash_value: "{a} 修改了 {b} 也修改过的 {n} 个数值，例如 {example}；它在后面，所以它优先。如果想要 {b} 的数值，请把 {b} 放到 {a} 后面。", clash_value_one: "{a} 修改了 {b} 也修改过的数值 {example}；它在后面，所以它优先。如果想要 {b} 的数值，请把 {b} 放到 {a} 后面。", clash_text: "{a} 修改了 {b} 也修改过的 {n} 条文本，例如 {example}；它在后面，所以它优先。如果想要 {b} 的文本，请把 {b} 放到 {a} 后面。", clash_text_one: "{a} 修改了 {b} 也修改过的文本 {example}；它在后面，所以它优先。如果想要 {b} 的文本，请把 {b} 放到 {a} 后面。", kind_script: "脚本", kind_script_archive: "脚本归档", kind_video: "视频", kind_sound: "音效", kind_sound_archive: "音效归档", kind_picture: "图片", kind_map_file: "地图文件", kind_text_file: "文本文件", kind_game_data: "游戏数据",
      update_out: "{app} {version} 已发布。", update_now: "更新", whats_new: "更新内容", update_progress: "正在下载更新… {pct}", update_installing: "正在安装：{app} 会自动关闭并重新打开。", update_repo: "（此副本从代码仓库运行：请用 git pull 更新。）", update_failed: "更新失败：{why}",
      doc_button: "故障排查", doc_title: "故障排查", doc_intro: "一次性检查所有可能妨碍测试或“开始游戏”的问题。", doc_checking: "正在检查…", doc_again: "重新检查", doc_copy: "复制报告", doc_copied: "报告已复制：请粘贴到你的错误报告或 Discord 中。", doc_close: "关闭", doc_fix_close_game: "关闭 R.U.S.E.", doc_fix_clear_leftovers: "清除它们", doc_fix_choose_game: "选择文件夹…", doc_fixed: "已完成（{done}）。", doc_fix_left: "部分操作未能完成：{left}", doc_game_ok: "已找到 R.U.S.E.：{path}", doc_game_missing: "未找到 R.U.S.E.。请选择其文件夹（包含 RUSE.exe 的那个）。", doc_steam_ok: "Steam 正在运行。", doc_steam_off: "Steam 未运行。开始游戏时会自动为你启动。", doc_running_none: "没有仍在运行的 R.U.S.E.。", doc_running_copy: "R.U.S.E. 仍在从模组版副本运行：{names}。请在下次测试或“开始游戏”前关闭它。", doc_running_game: "R.U.S.E.（Steam 游戏）正在运行：{names}。测试模组前请关闭它。", doc_drive_ok: "模组版副本保存在 {path}（{fs}）。", doc_drive_other: "模组版副本保存在 {path}，位于 {fs} 驱动器：每个副本都是完整复制，且 R.U.S.E. 运行时 Windows 可能拒绝删除副本。最好使用 NTFS 驱动器。", doc_space_ok: "模组版副本可用空间：{gb} GB。", doc_space_low: "模组版副本所在位置仅剩 {gb} GB：一个副本可能需要 {need} GB。", doc_left_none: "没有残留的副本。", doc_left: "残留的副本：{names}。它们只占用空间；你可以现在就清除。", doc_left_held: "残留的副本：{names}，被 {held} 占用。请关闭该程序，然后清除它们。", doc_readonly: "游戏中有 {n} 个文件被标记为只读。这没关系：模组版副本不会保留此标记。", doc_write_ok: "应用可以写入模组版副本所在的位置。", doc_write_fail: "应用无法写入 {path}（{why}）。请检查该文件夹的权限，或是否被杀毒软件拦截，或者在设置中为模组版副本选择另一个文件夹。", doc_troubleshoot_link: "故障排查",
      guide_title: "使用模组游玩，只需三步", guide_add: "添加模组：点击左侧的“添加模组文件…”，或将文件拖放到此窗口。RUSE Studio 模组（.rusemod）、RUSE Mod Manager 模组（.rmod）和 .zip 文件都可以使用。也可以在“支持的模组”中查找。", guide_set: "创建模组组合：点击“新建模组组合…”，勾选模组并排好顺序。两个模组修改同一项时，下面的优先。", guide_play: "选择组合，然后点击“开始游戏”。启动器会创建一份单独的模组版游戏副本并启动它；你的 Steam 游戏保持原样。", share: "分享", share_title: "分享此加载顺序", share_help: "复制这段内容并发送给好友（Discord、消息…）。对方在 RUSE Launcher（“导入加载顺序…”）或 RUSE Mod Manager 中导入，即可按相同顺序获得相同的模组。对方也需要拥有这些模组。", copy: "复制", copied: "已复制。", import_order: "导入加载顺序…", import_help: "粘贴好友分享的加载顺序（来自 RUSE Launcher 或 RUSE Mod Manager）。新的模组组合会按相同顺序包含你已有的模组。", import_paste: "在此粘贴加载顺序", check_order: "检查", make_set: "创建模组组合", import_found: "{total} 个模组中有 {n} 个在你的库中。", import_missing: "库中尚无：{names}。请添加它们（“添加模组文件…”或“支持的模组”）后重新导入，或不含它们直接创建组合。", import_version: "库中版本不同的模组：{list}。", import_wrong_game: "为游戏的另一个版本（R.U.S.E. 或 R.U.S.E. COMPAT）制作：这些模组可能与你的版本不兼容。", import_done: "已根据分享的加载顺序创建模组组合“{name}”。",
      language: "语言", looking: "正在查找 R.U.S.E.…", choose_folder: "选择文件夹…", mod_sets: "模组组合", vanilla: "原版",
      vanilla_desc: "不带模组的游戏。", no_mods: "无模组", one_mod: "1 个模组", n_mods: "{n} 个模组", has_mistake: "有错误",
      set_mistake: "此模组组合有错误:{error}", play: "开始游戏", play_set: "以 {name} 开始游戏", getting_ready: "正在准备…",
      details: "详情", join: "加入好友", browse: "支持的模组", mod_check_warn: "模组检查发现 {n} 个会让“开始游戏”停止的问题；作者可以修复：", report_problem: "报告问题", tip_report_problem: "在浏览器中打开错误报告，已填好应用和版本。由你检查后自行发布。", report: "报告", tip_report: "作为错误报告：浏览器会打开包含此消息的报告（路径中不含你的用户名）。", help: "帮助", tip_help: "在浏览器中打开 Wiki：添加模组、游玩、与好友一起玩。", coming_soon: "即将推出", new_set: "新建模组组合…",
      set_name: "模组组合的名称", tick_mods: "勾选要使用的模组。按此顺序加载:两个模组修改同一项时,下面的优先。", save: "保存",
      cancel: "取消", create: "创建", edit: "编辑", rename: "重命名", duplicate: "复制", delete: "删除",
      really_delete_set: "删除模组组合 {name}?其中的模组仍保留在库中。", move_up: "上移", move_down: "下移",
      copy_name: "{name}(副本)", set_saved: "模组组合 {name} 已保存。", set_deleted: "模组组合 {name} 已删除。",
      from_folder: "来自文件夹", library_empty_for_set: "请先向库中添加模组:模组组合由库中的模组组成。", library: "模组库",
      add_mod: "添加模组文件…", drop_hint: "…或将模组文件夹或 .zip 拖放到此窗口的任意位置。", drop_here: "松开即可添加到库中",
      adding: "正在添加模组…", remove: "移除", really_remove_mod: "从库中移除 {name}?使用它的模组组合在它重新添加之前无法使用。",
      version_v: "版本 {v}", by: "作者:{authors}", made_for: "适用于游戏版本 {builds}", your_build: "你的版本是 {build},可能不兼容",
      used_in_one: "用于 1 个模组组合", used_in: "用于 {n} 个模组组合", library_search: "搜索你的模组", library_count: "{n} 个模组", library_no_match: "没有与“{q}”匹配的模组。", library_empty: "还没有模组。请添加模组文件,或将其拖放到此窗口。",
      mod_added: "{name} 已添加到库中。", mod_updated: "{name} 已替换为版本 {v}。", mod_removed: "已从库中移除 {name}。",
      search_mods: "搜索模组", back: "返回", install: "安装", update_to: "更新到 {v}", installed: "已安装", installing: "正在安装…",
      offline_note: "无法连接到模组列表。这是 {date} 的副本。", list_failed: "无法加载模组列表：{why}", list_empty: "没有匹配的模组。",
      for_build: "适用于游戏版本 {build}", more_info: "关于此模组的更多信息", refresh_list: "刷新",
      browse_help: "来自社区列表的模组。安装后进入你的库；然后在模组组合中勾选它。" },
  };
  // where your files are, Show in folder, Delete a mod… (words.toml where_*, del_*, show_*_folder)
  Object.assign(words.us, {"lib_show": "Show in folder", "tip_lib_show": "Opens this mod's folder on your PC.", "set_where_title": "Where your files are", "set_where_help": "The Launcher's mods, and what you make in RUSE Studio, are kept in these folders. Show in folder opens one on your PC.", "where_library": "Your library: the mods the Launcher plays", "where_mods": "Mods made in RUSE Studio", "where_maps": "Map changes made in RUSE Studio", "where_exports": "Files exported from RUSE Studio, to share", "where_show": "Show in folder", "tip_where_show": "Opens {path} on your PC.", "really_remove_mod": "Remove {name} from the library? It goes to the Recycle Bin, so you can bring it back from there. Mod sets that use it stop working until it's back.", "mod_removed": "{name} was removed from the library: it's in the Recycle Bin, if you want it back."});
  Object.assign(words.fr, {"lib_show": "Afficher dans le dossier", "tip_lib_show": "Ouvre le dossier de ce mod sur votre PC.", "set_where_title": "Où sont vos fichiers", "set_where_help": "Les mods du Launcher, et ce que vous créez dans RUSE Studio, sont rangés dans ces dossiers. Afficher dans le dossier en ouvre un sur votre PC.", "where_library": "Votre bibliothèque : les mods que lance le Launcher", "where_mods": "Mods créés dans RUSE Studio", "where_maps": "Modifs de cartes créées dans RUSE Studio", "where_exports": "Fichiers exportés depuis RUSE Studio, à partager", "where_show": "Afficher dans le dossier", "tip_where_show": "Ouvre {path} sur votre PC.", "really_remove_mod": "Retirer {name} de la bibliothèque ? Il part dans la Corbeille, d'où vous pouvez le récupérer. Les ensembles de mods qui l'utilisent ne fonctionneront plus tant qu'il n'est pas de retour.", "mod_removed": "{name} a été retiré de la bibliothèque : il est dans la Corbeille, si vous voulez le récupérer."});
  Object.assign(words.sc, {"lib_show": "在文件夹中显示", "tip_lib_show": "在你的电脑上打开此模组的文件夹。", "set_where_title": "你的文件在哪里", "set_where_help": "Launcher 的模组以及你在 RUSE Studio 中制作的内容都保存在这些文件夹中。“在文件夹中显示”会在你的电脑上打开对应文件夹。", "where_library": "你的模组库：Launcher 使用的模组", "where_mods": "在 RUSE Studio 中制作的模组", "where_maps": "在 RUSE Studio 中制作的地图修改", "where_exports": "从 RUSE Studio 导出的文件（用于分享）", "where_show": "在文件夹中显示", "tip_where_show": "在你的电脑上打开 {path}。", "really_remove_mod": "从库中移除 {name}?它会移到回收站，可从那里找回。使用它的模组组合在它重新添加之前无法使用。", "mod_removed": "已从库中移除 {name}：如需找回，它在回收站中。"});
  // the clean game backup's words (words.toml backup_*, set_backup_*)
  Object.assign(words.us, { set_backup_title: "Clean game backup", set_backup_help: "RUSE Launcher and RUSE Studio never change the game's own folder, but other mod managers and hand edits can. Make a backup while the game is clean, right after Steam installs or verifies it. Check game files then shows what has changed since, and Restore clean files puts the game's files back.", backup_none: "No backup yet. It takes {need} GB; {free} GB is free on {drive}.", backup_have: "Backup of build {build}, made {date} ({size} GB): {path}", backup_other: "The backup is of build {build} (made {date}), but Steam has updated the game since (build {now}), so it can't be used. Verify with Steam, then make a new backup.", backup_make: "Make backup", backup_make_again: "Make backup again", backup_replace_ask: "This replaces the backup made {date}. Do it only if the game is clean now (use Verify with Steam first). Replace it?", backup_replace_yes: "Replace", backup_check: "Check game files", backup_deep: "Compare every byte (slower)", backup_restore: "Restore clean files", backup_restore_ask: "{n} file(s) will be copied back from the backup, and {m} file(s) that aren't the game's will be moved into a folder in {path}. Nothing is deleted. Restore?", backup_restore_yes: "Restore", backup_verify: "Verify with Steam", backup_verify_tip: "Steam's own repair: it checks every file and downloads the ones that changed. No backup needed.", backup_verify_opened: "Steam is checking the game's files and downloads any that changed; Steam shows how far it is.", backup_making: "Making the backup… {pct}", backup_checking: "Checking the game's files… {pct}", backup_restoring: "Restoring the game's files… {pct}", backup_made: "Backup made: {files} files, {size} GB.", backup_clean: "The game's files match the backup: nothing has changed.", backup_differs: "{n} file(s) differ from the backup:", backup_changed: "Changed ({n})", backup_missing: "Missing ({n})", backup_added: "Not the game's ({n})", backup_more: "…and {n} more", backup_nothing: "Nothing to restore: the game's files match the backup.", backup_restored: "Done: {n} file(s) restored.", backup_set_aside: "{m} file(s) that weren't the game's are now in {path}.", backup_kept: "The {k} changed file(s) that were replaced are kept in {path}." });
  Object.assign(words.fr, { set_backup_title: "Sauvegarde propre du jeu", set_backup_help: "RUSE Launcher et RUSE Studio ne modifient jamais le dossier du jeu, mais d'autres gestionnaires de mods et des modifications à la main peuvent le faire. Faites une sauvegarde pendant que le jeu est propre, juste après que Steam l'a installé ou vérifié. « Vérifier les fichiers du jeu » montre ensuite ce qui a changé depuis, et « Restaurer les fichiers propres » remet les fichiers du jeu en place.", backup_none: "Pas encore de sauvegarde. Elle demande {need} Go ; {free} Go sont libres sur {drive}.", backup_have: "Sauvegarde de la version {build}, faite le {date} ({size} Go) : {path}", backup_other: "La sauvegarde est de la version {build} (faite le {date}), mais Steam a mis le jeu à jour depuis (version {now}) : elle ne peut pas servir. Vérifiez avec Steam, puis faites une nouvelle sauvegarde.", backup_make: "Faire une sauvegarde", backup_make_again: "Refaire la sauvegarde", backup_replace_ask: "Ceci remplace la sauvegarde faite le {date}. Ne le faites que si le jeu est propre maintenant (utilisez d'abord « Vérifier avec Steam »). La remplacer ?", backup_replace_yes: "Remplacer", backup_check: "Vérifier les fichiers du jeu", backup_deep: "Comparer chaque octet (plus lent)", backup_restore: "Restaurer les fichiers propres", backup_restore_ask: "{n} fichier(s) seront recopiés depuis la sauvegarde, et {m} fichier(s) qui ne sont pas ceux du jeu seront déplacés dans un dossier de {path}. Rien n'est supprimé. Restaurer ?", backup_restore_yes: "Restaurer", backup_verify: "Vérifier avec Steam", backup_verify_tip: "La réparation de Steam : il vérifie chaque fichier et retélécharge ceux qui ont changé. Aucune sauvegarde nécessaire.", backup_verify_opened: "Steam vérifie les fichiers du jeu et retélécharge ceux qui ont changé ; Steam affiche sa progression.", backup_making: "Sauvegarde en cours… {pct}", backup_checking: "Vérification des fichiers du jeu… {pct}", backup_restoring: "Restauration des fichiers du jeu… {pct}", backup_made: "Sauvegarde faite : {files} fichiers, {size} Go.", backup_clean: "Les fichiers du jeu correspondent à la sauvegarde : rien n'a changé.", backup_differs: "{n} fichier(s) diffèrent de la sauvegarde :", backup_changed: "Modifiés ({n})", backup_missing: "Manquants ({n})", backup_added: "Pas du jeu ({n})", backup_more: "…et {n} de plus", backup_nothing: "Rien à restaurer : les fichiers du jeu correspondent à la sauvegarde.", backup_restored: "Terminé : {n} fichier(s) restauré(s).", backup_set_aside: "{m} fichier(s) qui n'étaient pas ceux du jeu sont maintenant dans {path}.", backup_kept: "Les {k} fichier(s) modifié(s) qui ont été remplacés sont conservés dans {path}." });
  Object.assign(words.sc, { set_backup_title: "游戏的干净备份", set_backup_help: "RUSE Launcher 和 RUSE Studio 从不修改游戏本身的文件夹，但其他模组管理器和手动修改可能会。请在游戏干净时（Steam 刚安装或验证完之后）创建备份。之后，“检查游戏文件”会显示自那以后改变了什么，“恢复干净文件”会把游戏文件还原。", backup_none: "还没有备份。需要 {need} GB；{drive} 上有 {free} GB 可用。", backup_have: "版本 {build} 的备份，创建于 {date}（{size} GB）：{path}", backup_other: "备份来自版本 {build}（创建于 {date}），但 Steam 之后更新了游戏（版本 {now}），因此无法使用。请先通过 Steam 验证，然后创建新的备份。", backup_make: "创建备份", backup_make_again: "重新创建备份", backup_replace_ask: "这将替换创建于 {date} 的备份。只有在游戏现在是干净的时候才这样做（请先使用“通过 Steam 验证”）。要替换吗？", backup_replace_yes: "替换", backup_check: "检查游戏文件", backup_deep: "逐字节比较（较慢）", backup_restore: "恢复干净文件", backup_restore_ask: "将从备份复制回 {n} 个文件，并把 {m} 个不属于游戏的文件移到 {path} 中的一个文件夹。不会删除任何东西。要恢复吗？", backup_restore_yes: "恢复", backup_verify: "通过 Steam 验证", backup_verify_tip: "Steam 自带的修复：检查每个文件并重新下载有变化的文件。不需要备份。", backup_verify_opened: "Steam 正在检查游戏文件，并重新下载有变化的文件；进度显示在 Steam 中。", backup_making: "正在创建备份… {pct}", backup_checking: "正在检查游戏文件… {pct}", backup_restoring: "正在恢复游戏文件… {pct}", backup_made: "备份已创建：{files} 个文件，{size} GB。", backup_clean: "游戏文件与备份一致：没有任何变化。", backup_differs: "与备份不同的文件：{n} 个", backup_changed: "已更改（{n}）", backup_missing: "缺失（{n}）", backup_added: "不属于游戏（{n}）", backup_more: "…还有 {n} 个", backup_nothing: "无需恢复：游戏文件与备份一致。", backup_restored: "完成：已恢复 {n} 个文件。", backup_set_aside: "{m} 个不属于游戏的文件现在位于 {path}。", backup_kept: "被替换的 {k} 个已更改文件保存在 {path}。" });
  // the supported-mods list: its tab, the cheats' group and the first run's "Choose your mods" (words.toml)
  Object.assign(words.us, {"browse_help": "These are the mods that work with the Launcher. Tick the ones you want and press Install: each file is checked against the list before it goes into your library. Then tick them in a mod set.", "see_list": "See the list on GitHub", "install_ticked": "Install ticked mods ({n})", "cheats_group": "Cheats and test tools (optional)", "cheats_help": "These change the game for testing (units for free, instant building…). They're never ticked for you, and never downloaded unless you tick them.", "welcome_title": "Choose your mods", "welcome_help": "These are the mods that work with the Launcher. Everything is ticked except the cheats and test tools: untick what you don't want, then Install. You can add more later under “Supported mods”.", "welcome_skip": "Skip", "welcome_offline": "Skip for now: the mods are under “Supported mods” whenever you're online.", "loading_list": "Loading the list…"});
  Object.assign(words.fr, {"browse_help": "Voici les mods qui fonctionnent avec le Launcher. Cochez ceux que vous voulez et appuyez sur Installer : chaque fichier est vérifié par rapport à la liste avant d'entrer dans votre bibliothèque. Cochez-les ensuite dans un ensemble de mods.", "see_list": "Voir la liste sur GitHub", "install_ticked": "Installer les mods cochés ({n})", "cheats_group": "Triches et outils de test (facultatif)", "cheats_help": "Ils modifient le jeu pour les tests (unités gratuites, construction instantanée…). Ils ne sont jamais cochés pour vous, et jamais téléchargés si vous ne les cochez pas.", "welcome_title": "Choisissez vos mods", "welcome_help": "Voici les mods qui fonctionnent avec le Launcher. Tout est coché sauf les triches et les outils de test : décochez ce que vous ne voulez pas, puis Installer. Vous pourrez en ajouter d'autres plus tard dans « Mods compatibles ».", "welcome_skip": "Passer", "welcome_offline": "Passez pour l'instant : les mods sont dans « Mods compatibles » dès que vous êtes en ligne.", "loading_list": "Chargement de la liste…"});
  Object.assign(words.sc, {"browse_help": "这些是可在 Launcher 中使用的模组。勾选你想要的，然后点击“安装”：每个文件在进入你的库之前都会与列表核对。然后在模组组合中勾选它们。", "see_list": "在 GitHub 上查看列表", "install_ticked": "安装勾选的模组（{n}）", "cheats_group": "作弊和测试工具（可选）", "cheats_help": "它们为测试而修改游戏（单位免费、瞬间建造…）。它们不会被自动勾选，除非你勾选，否则也不会被下载。", "welcome_title": "选择你的模组", "welcome_help": "这些是可在 Launcher 中使用的模组。除作弊和测试工具外均已勾选：取消勾选你不需要的，然后点击“安装”。以后也可以在“支持的模组”中添加更多。", "welcome_skip": "跳过", "welcome_offline": "暂时跳过：联网后可随时在“支持的模组”中找到这些模组。", "loading_list": "正在加载列表…"});
  const build = "24687178";
  // Sample data for the preview only: mods that exist in the repo's mods/ folder, nobody's name on them.
  let library = ["empty", "first", "firstoffline"].includes(mode) ? [] : [
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
      description: "A new script for the Ardennes mission.", builds: [build], used_in: 1, scripts: true, trusted: false },
    // fair play (rusemod.fairplay): a made-up test tool, tagged "cheat" in the mod list
    { id: "money-test-tool", name: "Money Test Tool", version: "0.2.0", authors: [], author: "",
      description: "Adds money for testing.", builds: [build], used_in: 0, cheat: true,
      offline: "Money Test Tool is a cheat or a test tool" },
    { id: "ardennes-endless", name: "Ardennes Endless", version: "3.0", authors: [], author: "",
      description: "The Ardennes mission never ends.", builds: [build], used_in: 1 },
  ];
  let sets = ["empty", "first", "firstoffline"].includes(mode) ? [] : [
    { id: "my-set", name: "My set", description: "", mods: ["airfield-capacity", "passable-forests"] },
    { id: "missing-mod", name: "Sample set with a missing mod", description: "", mods: ["some-other-mod"] },
    { id: "clashing", name: "Sample set with clashing mods", description: "", mods: ["anchored-ships", "harbour-pack", "ardennes-rescripted", "ardennes-endless"] },
  ];
  // "Choose your language" (?fake=lang: the game set to French in Steam; it also opens on the first-run modes)
  Object.assign(words.us, {"convert_mod": "Convert an old mod…", "tip_convert_mod": "For an old mod that comes as the game's own files (.dat packs) to copy into the game folder: makes it a mod the library can play beside others.", "convert_title": "Convert an old mod", "convert_help": "Some older mods come as the game's own packs (.dat files) with the changes inside, made to be copied into the game folder. Pick the folder the mod came in: the Launcher compares each pack with your game's clean one, keeps only what the mod changes, and adds it to your library. Your game folder isn't touched. Uses LittleGroove's converter.", "convert_pick": "Pick the mod's folder…", "tip_convert_pick": "Choose the folder the old mod came in (the one holding its .dat files, or a Data or PC folder with them inside).", "tip_convert_cancel": "Close this without converting anything.", "convert_found": "{n} game pack(s) found in {folder}:", "convert_none": "There's no game pack in {folder} (a .dat file the game has too). Pick the folder the old mod came in.", "convert_ref_backup": "Compared with your clean backup of the game, so mods already copied into the game folder don't get mixed in.", "convert_ref_game": "Compared with your game folder, as there's no clean backup. If you ever copied mods into the game folder, make a clean backup first (Settings) after letting Steam repair the game, or their changes end up in this mod too.", "convert_name": "Name", "tip_convert_name": "The mod's name in your library and in mod sets.", "convert_version": "Version", "tip_convert_version": "Numbers with dots, like 1.0.0. Converting it again with a higher one replaces the old copy.", "convert_author": "Author", "tip_convert_author": "Who made the old mod (shown in your library, to give them credit).", "convert_description": "Description", "tip_convert_description": "A line about what the mod does (shown in your library).", "convert_go": "Convert and add to the library", "tip_convert_go": "Compare the packs and make the mod. A big mod takes a minute or two; the lines below say how far it is.", "convert_running": "Converting…", "convert_failed": "The mod couldn't be converted."});
  Object.assign(words.us, {"clash_gamefile": "{a} and {b} both change the same game file, {file}. The one from {b} is used, because {b} is lower in the list.", "clash_use": "Use the one from {a}", "tip_clash_use": "Moves {a} just below {b} in this mod set, so the {file} from {a} is used. If the two mods change other things too, {a} wins those as well.", "clash_use_done": "{name}: {a} is now below {b}, so the {file} from {a} is used."});
  // Settings' title switch (words.toml set_title_*, title_*: R.U.S.E. 2.0's gold title or the game's own)
  Object.assign(words.us, {"set_title_title": "The game's title", "set_title_help": "Your modded game shows its title as R.U.S.E. 2.0 in gold: on the main menu, on the loading screens and in the video as the game starts. It's made on your PC from your own game's files. Untick it to have the game's own R.U.S.E. title. The next Play builds the copy your way.", "title_gold": "Gold R.U.S.E. 2.0 title", "title_on_note": "The next Play gives your modded game the gold R.U.S.E. 2.0 title.", "title_off_note": "The next Play gives your modded game the game's own R.U.S.E. title.", "tip_title_gold": "Show R.U.S.E. 2.0 in gold on the menu and the loading screens of your modded game. Untick for the game's own title."});
  Object.assign(words.us, { lang_pick_title: "Choose your language", lang_from_steam: "Your game's language in Steam",
    lang_from_pc: "Your PC's language", lang_pick_close: "Close", tip_lang_open: "Change the language.",
    set_in_this: "In this set ({n})", set_none_yet: "No mods yet: tick them below.", set_add_mods: "Add mods from your library",
    lang_pick_help: "The Launcher in your language. You can change it any time with the language button at the top." });
  Object.assign(words.fr, { lang_pick_title: "Choisissez votre langue", lang_from_steam: "La langue de votre jeu sur Steam",
    lang_from_pc: "La langue de votre PC", lang_pick_close: "Fermer", tip_lang_open: "Changer la langue.",
    set_in_this: "Dans cet ensemble ({n})", set_none_yet: "Aucun mod pour l'instant : cochez-les ci-dessous.",
    set_add_mods: "Ajouter des mods de votre bibliothèque",
    lang_pick_help: "Le Launcher dans votre langue. Vous pouvez la changer à tout moment avec le bouton de langue en haut." });
  Object.assign(words.sc, { lang_pick_title: "选择你的语言", lang_from_steam: "你在 Steam 中的游戏语言",
    lang_from_pc: "你的电脑语言", lang_pick_close: "关闭", tip_lang_open: "更改语言。",
    lang_pick_help: "用你的语言显示 Launcher。随时可以用顶部的语言按钮更改。" });
  // fair play (words.toml; English only in the preview): the join code box, the badges, the trust tick
  Object.assign(words.us, { join_code: "Join code",
    tip_join: "Your modded game's join code, to send to the people you play with, and theirs compared with it",
    fair_title: "RUSE Guard: your join code",
    fair_help: "Send this code to the people you play with. The same code means the same game: the same game version, mods and mod versions. It changes when your mods change.",
    fair_paste: "Paste a friend's join code", fair_compare: "Compare", fair_full: "Check every file of the copy",
    fair_checking: "Checking the modded copy…",
    fair_not_built: "No join code yet: press Play once, and the code comes with the modded copy.",
    fair_changed: "No join code: the modded copy changed after it was built ({what}). Press Play to build it again.",
    fair_offline: "No join code: this copy is for offline play ({why}). It leaves multiplayer and co-op matches. Make a mod set without cheats and test tools to play with others.",
    fair_no_change: "No join code: these mods don't change how the game plays, so anyone can play with you.",
    fair_checked: "Every file checked: the copy is exactly as it was built.", fair_same: "Same game: you can play together.",
    fair_differs: "Not the same game. A match between these two would drift apart:", fair_copied: "Join code copied.",
    badge_cheat: "Cheat", tip_badge_cheat: "A cheat or a test tool: a modded copy with it is for offline play only",
    badge_scripts: "Runs scripts",
    tip_badge_scripts: "This mod changes the game's scripts. Scripts run inside the game and can do anything it can: Play waits until you tick that you trust its author.",
    mod_offline: "Offline only: {why}. A modded copy with it leaves multiplayer and co-op matches.",
    scripts_note: "This mod changes the game's scripts. They run inside the game and can do anything it can, like any program.",
    trust_author: "I trust this mod's author (Play waits for this tick)" });
  const myCode = "RUSE1:0C4F2V9R3DNQ6M8T1KXH4Q0Z9WJ2FP3ACVQ5RT7B9EGX0J";
  // Bug Watch's words (words.toml set_bugwatch_*, bugwatch_*, tip_bugwatch_*)
  Object.assign(words.us, { set_bugwatch_title: "Bug Watch", set_bugwatch_help: "Recommended: it helps us fix crashes and bugs faster. When it's on, the Studio and the Launcher count what you use and when something goes wrong, including the game's crashes and which mods were on, and send it to our developers once a day with the username you choose. No real names, no Steam account, no files. It's off unless you tick it, and you can untick it any time.", bugwatch_on_label: "Bug Watch (Recommended)", bugwatch_name_hint: "Your username", bugwatch_save: "Save username", bugwatch_code: "You're {name}. Your report code is {code}: put it in a bug report so we can find your crashes.", bugwatch_show: "Show what's sent", bugwatch_need_name: "Type a username first, then tick Bug Watch.", bugwatch_now_on: "Bug Watch is on. Thank you!", bugwatch_now_off: "Bug Watch is off: nothing more is counted or sent, and what was kept is deleted.", tip_bugwatch_on: "Send counts and crash reports to our developers once a day. Off unless you tick it.", tip_bugwatch_name: "The name our developers see with your counts and crashes. A # and four numbers are added so it's unique.", tip_bugwatch_save: "Keep this username (a new name gets new numbers).", tip_bugwatch_show: "See, word for word, what Bug Watch would send." });
  let fakeBugwatch = { available: true, on: false, name: "", code: "" };  // ?fake=bugoff hides the card, as bugwatch.ON = False does
  if (new URLSearchParams(location.search).get("fake") === "bugoff") fakeBugwatch.available = false;
  let fakeTerms = mode === "agree" ? 0 : 3;  // ?fake=agree: the first-start agreement hasn't been accepted yet
  // The first-start agreement + username words (words.toml agree_*, username_*), for the ?fake=agree preview
  Object.assign(words.us, { agree_title: "R.U.S.E. 2.0: user and licence agreement", agree_intro: "This covers RUSE Studio, RUSE Launcher and our online services. R.U.S.E. is a game by Eugen Systems, published by Ubisoft, and you need your own copy: the apps work only with a copy of the game you own. R.U.S.E. 2.0 is a free community project, not made, approved or supported by them.", agree_guard_title: "RUSE Guard: our anti-cheat (required)", agree_guard: "Why: to stop cheating in real R.U.S.E. multiplayer matches, so every match is fair. It acts only in multiplayer and co-op matches, never in single-player, skirmish against the computer, the campaign, replays, or while you make mods. As part of it, during those matches it checks your running programs against a list of known cheat tools: it reads only the programs' names, reports only a name that is on that list, and looks at nothing else. It never collects your files, your screen, your keystrokes or your computer's memory. A modded copy built with a cheat or test tool is for offline play only: taken into a multiplayer match, it surrenders and then stops the game, and the Launcher sends us the line the game's crash report carries about it; honest copies are never stopped. Using the Studio and Launcher means accepting RUSE Guard, including this check.", agree_full_toggle: "Read the full agreement", agree_full: "R.U.S.E. 2.0: user and licence agreement\nVersion 2, 31 October 2026\n\n(The full agreement text appears here in the app.)", agree_accept_note: "Accepting RUSE Guard is required to use the apps. This English text is the one that counts; other languages are translations.", agree_accept: "Accept and continue", username_title: "Choose your username", username_help: "A name our developers see with your RUSE Guard matches or your Bug Watch reports, so we can help you. A # and four numbers are added so it's unique, like Nick#4821. One name works for both apps, and you can change it in Settings.", username_save: "Save and continue", username_need: "Type a username to continue." });
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
  const modSets = () => [{ id: "vanilla", name: "Vanilla", description: "The game with no mods.", mods: [],
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
    // both change one game file whole (rusemod.gamefiles.overlaps): the lower one's is used, the other offered
    if (mods.includes("harbour-pack") && mods.includes("anchored-ships")) {
      const [first, last] = mods.filter((m) => m === "harbour-pack" || m === "anchored-ships");
      soft.push({ kind: "gamefile", hard: false, mods: [name(first), name(last)], what: "Sample.ppk: ships/battleship.png",
        message: `${name(first)} and ${name(last)} both change Sample.ppk: ships/battleship.png: ${name(last)}'s is used`,
        count: 1, a: name(first), b: name(last), move: first, below: last });
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
      homepage: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/tree/main/mods/airfield-capacity",
      download: "https://example.invalid/airfield-capacity-1.0.0.rusemod", size: 1315, sha256: "ae22dfd4ab5ff56254fff98e8d8a27b486f4ec5c821db83211c62b35aeb0f25a",
      game_build: "24087620", fingerprint: "", tags: ["air"] },
    { id: "passable-forests", name: "Passable Forests", version: "1.0.0", author: "", description: "Lets every tank, tank destroyer, AA vehicle, and mobile artillery/assault gun enter forest terrain the way recon vehicles already can, by removing the InitialFlagSet flags (11, 21, 55) that block forest entry. Confirmed in-game on the M4 Sherman before rolling out to the full roster.",
      homepage: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/tree/main/mods/passable-forests",
      download: "https://example.invalid/passable-forests-1.0.0.rusemod", size: 2744, sha256: "1fe29ca1b796b3e6034f1a4710d6ed0f10236f487ec88492a3550b19692d2102",
      game_build: "24087620", fingerprint: "", tags: ["movement"] },
    { id: "cheat-mod-v2", name: "Cheat Mod 2.0", version: "2.0.0", author: "", description: "Every unit AND every building costs $1 to build, every unit's ProductionTime is 0, and the global MinProductionTime floor is lowered to 0.01 seconds so 0-second production actually takes effect instead of being clamped back up to 1 second. Extends the example Cheat Mod (units-only $1 pricing) with building pricing and the confirmed-working instant-production fix.",
      homepage: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/tree/main/mods/cheat-mod-v2",
      download: "https://example.invalid/cheat-mod-v2-2.0.0.rusemod", size: 4918, sha256: "e010c5cc810fdc29a84704f4bc73dedd671132bd18adb9896e2867a03fae587c",
      game_build: "24087620", fingerprint: "", tags: ["cheat"] },
  ];
  const sizeText = (n) => n < 1e6 ? `${Math.max(1, Math.round(n / 1000))} KB` : `${(n / 1e6).toFixed(1)} MB`;
  const browseView = (search) => {
    const q = (search || "").toLowerCase();
    const have = Object.fromEntries(library.map((m) => [m.id, m.version]));
    const mods = listed.filter((m) => !q || `${m.id} ${m.name} ${m.author} ${m.description} ${m.tags.join(" ")}`.toLowerCase().includes(q))
      .map((m) => ({ ...m, state: !have[m.id] ? "new" : have[m.id] < m.version ? "update" : "installed",
        installed_version: have[m.id] || "", size_text: sizeText(m.size), cheat: m.tags.includes("cheat") }))
      .sort((a, b) => a.cheat - b.cheat);
    const page = "https://github.com/sneadtristen6/Ruse-Mods";
    if (mode === "firstoffline") return { mods: [], source: "none", as_of: "", page, problems: [],
      message: "The mod list couldn't be loaded (getaddrinfo failed), and there's no copy from before." };
    return { mods, source: mode === "offline" ? "cache" : "online", as_of: "2026-09-29 20:30", message: "", problems: [], page };
  };
  let chosen = !["first", "firstoffline"].includes(mode);  // the first run's "Choose your mods" was done or skipped
  let fakeCopies = null;  // the folder chosen for modded copies, or null: the recommended place
  let fakeTitle = true;   // the copies get R.U.S.E. 2.0's gold title (Settings)
  const copiesView = () => mode === "notfound"
    ? { path: fakeCopies, how: fakeCopies ? "chosen" : "recommended", recommended: null, drive: null, other_drive: false }
    : { path: fakeCopies || "D:\\RUSE-Instances", how: fakeCopies ? "chosen" : "recommended", recommended: "D:\\RUSE-Instances",
        drive: "D:", other_drive: Boolean(fakeCopies) };
  // the troubleshooter (rusemod.doctor): made-up findings, one of each level; Close R.U.S.E. works at once, Clear
  // them the second time (the first leaves a copy that's still held)
  const fixed = {};  // fix -> how many times it ran
  const finding = (key, level, say, data, fix) => ({ key, level, say, data: data || {}, fix: fix || null });
  const findings = () => [
    mode === "notfound" ? finding("game", "fail", "doc_game_missing", {}, "choose_game")
      : finding("game", "ok", "doc_game_ok", { path: "D:\\Steam\\steamapps\\common\\R.U.S.E" }),
    finding("steam", "info", "doc_steam_off"),
    fixed.close_game || mode === "notfound" ? finding("running", "ok", "doc_running_none")
      : finding("running", "warn", "doc_running_copy", { names: "RUSE.exe (4312)" }, "close_game"),
  ].concat(mode === "notfound" ? [] : [  // no game: no place for modded copies, so no checks of it
    // where copies go and why; a folder chosen on another drive gets the full-copy note too
    fakeCopies ? finding("drive", "ok", "doc_copies_chosen", { path: fakeCopies, fs: "NTFS", how: "chosen" })
      : finding("drive", "ok", "doc_copies_recommended", { path: "D:\\RUSE-Instances", fs: "NTFS", how: "recommended" }),
    ...(fakeCopies ? [finding("other_drive", "info", "doc_copies_other_drive", { path: fakeCopies, drive: "D:", recommended: "D:\\RUSE-Instances" })] : []),
    finding("space", "ok", "doc_space_ok", { gb: 182.4 }),
    fixed.clear_leftovers > 1 ? finding("leftovers", "ok", "doc_left_none")
      : finding("leftovers", "info", "doc_left", { names: (fixed.clear_leftovers ? "" : "my-set.old, ") + ".trash\\clashing.partial" },
        "clear_leftovers"),
    finding("readonly", "info", "doc_readonly", { n: 3 }),
    finding("write", "fail", "doc_write_fail", { path: fakeCopies || "D:\\RUSE-Instances", why: "Access is denied" }),
  ]);
  const doctorReport = (list) => ["RUSE Launcher 0.2.10, Windows 10.0.26200"].concat(list.map((f) => {
    const data = Object.entries(f.data).map(([k, v]) => `${k}=${v}`).join(", ");
    return `[${f.level}] ${f.key}: ${f.say}` + (data ? ` (${data})` : "");
  })).join("\n");
  // the clean game backup (rusemod.backup): none at first (?fake=backup: one already made, with the game's files
  // changed since; ?fake=oldbackup: one of an older build; ?fake=nospace: no room for one; ?fake=running: a restore
  // refused while R.U.S.E. runs). Its jobs run like the real ones: progress lines, then a result
  const BACKUPS = "D:\\RUSE-Backup";
  const backupOf = (b, date) => ({ path: `${BACKUPS}\\${b}`, build: b, made: date.replace(" ", "T") + ":00", date,
    files: 61, size: 5690000000, size_gb: 5.3, matches: b === build });
  const changedSince = mode === "backup" || mode === "running";  // another mod manager changed files since the backup
  let backups = changedSince ? [backupOf(build, "2026-09-28 18:05")]
    : mode === "oldbackup" ? [backupOf("24087620", "2026-08-02 11:40")] : [];
  let gameClean = !changedSince;
  const backupStatus = () => mode === "notfound" ? { found: false, backups: [], current: null, busy: "" }
    : { found: true, build, folder: BACKUPS, drive: "D:", backups: backups.slice(), current: backups.find((b) => b.matches) || null,
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
  let playing = null;
  const fakeConvertScan = () => ({ folder: "D:\\Mods\\Old Pacific Mod", name: "Old Pacific Mod",
    files: [{ path: "Data/PC/190852/ZZ_GladPatchableWin.dat", kb: 23810 }, { path: "Data/PC/190852/ZZ_Win.dat", kb: 412000 }],
    reference: mode === "firstbackup" ? "game" : "backup", reference_path: "D:\\RUSE-Backup\\24687178" });
  // owned copies, layer 2 (rusemod.ownedpass): "Sign in through Steam". ?fake=signin shows it switched on.
  const signin = { signed: false };
  const signinWords = {
    title: "Sign in through Steam",
    intro: "For online play, RUSE Guard and content downloads, R.U.S.E. 2.0 confirms you own R.U.S.E. by signing in through Steam. You sign in on Steam's own page in your browser; we never see your password, and your Steam ID is never stored.",
    sign_in: "Sign in through Steam", tip_sign_in: "Opens Steam's sign-in page in your browser. After you sign in, come back here.",
    waiting: "Waiting for Steam. Finish signing in in your browser, then come back to this window.",
    waiting_note: "This window checks every few seconds. You can close it and sign in later.",
    cancel: "Cancel", tip_cancel: "Stops waiting for this sign-in. Nothing is kept.",
    signed_in: "Signed in through Steam: you own R.U.S.E.", until: "Confirmed until {date}.",
    not_signed_in: "You're not signed in through Steam yet.",
    sign_out: "Sign out", tip_sign_out: "Forgets this sign-in on this PC. You can sign in again any time.",
    close: "Close", tip_close: "Closes this window.",
    err_private: "Steam didn't show us your games because your Steam profile's Game details are private.",
    err_not_owned: "This Steam account doesn't own R.U.S.E. R.U.S.E. 2.0 works only with copies people own.",
    err_steam: "Steam didn't answer properly, so we couldn't check. Try again in a few minutes.",
    err_bad_pass: "The sign-in came back but didn't check out, so nothing was kept. Try again in a few minutes.",
    err_expired: "This sign-in link ran out. Start the sign-in again.",
    err_reach: "We couldn't reach the sign-in server. Check your connection and try again.",
    off: "Signing in through Steam isn't switched on yet.",
  };
  const signinStatus = () => ({ on: mode === "signin", signed_in: signin.signed, owned: signin.signed,
    until: Math.floor(Date.now() / 1000) + 30 * 86400, reason: signin.signed ? "ok" : "none", words: signinWords, app_id: 21970 });
  window.pywebview = {
    api: {
      languages: async () => [{ code: "us", name: "English" }, { code: "fr", name: "Français" }, { code: "ger", name: "Deutsch" },
        { code: "ita", name: "Italiano" }, { code: "spa", name: "Español" }, { code: "pol", name: "Polski" },
        { code: "ru", name: "Русский" }, { code: "cz", name: "Čeština" }, { code: "jpn", name: "日本語" }, { code: "sc", name: "简体中文" },
        { code: "fa", name: "فارسی", rtl: true }],
      default_language: async () => "us",
      strings: async (lang) => wordsOf(lang),
      status: async () => mode === "notfound"
        ? { found: false, message: "We couldn't find R.U.S.E. Is it installed through Steam?" }
        : { found: true, game_dir: "D:\\Steam\\steamapps\\common\\R.U.S.E", build, drive: "D:",
            message: `Found R.U.S.E. on D: (build ${build})` },
      choose_game_folder: async () => ({ found: true, drive: "D:", build, message: `Found R.U.S.E. on D: (build ${build})` }),
      // where modded copies go (Settings): the recommended place until a folder is chosen, which here is on another
      // drive (so the full-copy note shows); Use the recommended place puts it back
      copies_folder: async () => copiesView(),
      choose_copies_folder: async () => { fakeCopies = "E:\\Games\\RUSE-Instances"; return copiesView(); },
      use_recommended_copies: async () => { fakeCopies = null; return copiesView(); },
      game_title: async () => ({ ruse20: fakeTitle }),
      set_game_title: async (on) => { fakeTitle = Boolean(on); return { ruse20: fakeTitle }; },
      bugwatch_status: async () => ({ ...fakeBugwatch }),
      bugwatch_on: async (name) => {
        const kept = /#\d{4}$/.test(name) ? name : `${name}#4821`;
        fakeBugwatch = { ...fakeBugwatch, on: true, name: kept, code: "Zx3k9QpL" };
        return { on: true, name: kept, code: "Zx3k9QpL" };
      },
      set_username: async (name) => {  // the agreement's guard-only path: a shared name/id, Bug Watch left off
        const num = String(1000 + Math.floor(Math.random() * 9000));
        fakeBugwatch = { ...fakeBugwatch, name: /#\d{4}$/.test(name) ? name : `${name}#${num}`, code: fakeBugwatch.code || "Zx3k9QpL" };
        return { name: fakeBugwatch.name, code: fakeBugwatch.code };
      },
      bugwatch_off: async () => { fakeBugwatch = { ...fakeBugwatch, on: false, name: "", code: "" }; return { on: false }; },
      bugwatch_next_send: async () => ({ today: { v: 1, id: "Zx3k9QpL2mVb7TnR4wYh8CdF5sGj1AeU", user: fakeBugwatch.name,
        app: "launcher", version: "0.4.8.9", day: new Date().toISOString().slice(0, 10), setup: { windows: "11", language: "us" },
        calls: { play: { n: 2, failed: 0, time: [0, 2, 0, 0, 0] } } }, waiting: [] }),
      bugwatch_seen: async () => ({ ok: true }),
      troubleshoot: async () => {
        await new Promise((done) => setTimeout(done, 600));  // the real checks take a moment
        const list = findings();
        return { findings: list, report: doctorReport(list) };
      },
      troubleshoot_fix: async (action) => {
        if (action !== "close_game" && action !== "clear_leftovers") throw new Error(`There's no fix called '${action}'.`);
        fixed[action] = (fixed[action] || 0) + 1;
        return action === "clear_leftovers" && fixed[action] === 1  // the first time one copy is still held
          ? { done: 1, left: ["1 in D:\\RUSE-Instances\\.trash: still held, removed on a later test"] } : { done: 1, left: [] };
      },
      app_version: async () => ({ app: "Launcher", version: "0.3.1" }),
      // the start-up log: here, the page's moment kept in window.fakeStartMarks (ms since the page began loading)
      start_mark: async (what) => { (window.fakeStartMarks = window.fakeStartMarks || {})[what] = performance.now(); return {}; },
      // ?fake=required: a required update (its box, installing by itself); ?fake=requiredoffline: one seen before, offline
      update_check: async () => mode === "requiredoffline"
        ? { available: false, required: true, offline: true, version: "9.9.9", current: "0.3.1",
            error: "GitHub couldn't be reached to look for updates (no connection)." }
        : mode === "update" || mode === "required"
        ? { available: true, version: "9.9.9", current: "0.3.1", installed: true, size: 60000000, required: mode === "required",
            changes: [
              { version: "9.9.9", before: "Mods with units from another nation crashed the game.",
                now: "They work in any match." },
              { version: "9.9.9", before: "", now: "A new look." }],
            page: "https://github.com/sneadtristen6/R.U.S.E-2.0-Project/releases" }
        : { available: false, version: "0.3.1", current: "0.3.1" },
      update_install: async () => { throw new Error("The preview can't install updates."); },
      update_page: async () => ({ opened: "" }),
      open_help: async (what) => ({ opened: what }),
      owned_check: async () => ({ ok: true, reasons: [], code: "" }),  // owned copies: the preview's game is fine
      owned_unlock: async () => ({ ok: true, reasons: [], code: "" }),
      owned_open: async (what) => ({ opened: what }),
      owned_pass_status: async () => signinStatus(),
      owned_sign_in_start: async () => signinStatus().on
        ? { on: true, code: "PREVIEW0000000000000000000000000000000000000", login_url: "https://ruse-owned.example/v1/steam/login", poll_every: 1, expires_in: 600 }
        : { on: false },
      owned_sign_in_poll: async () => { signin.signed = true; return { status: "owned", ...signinStatus() }; },
      owned_sign_out: async () => { signin.signed = false; return signinStatus(); },
      report_problem: async (message) => ({ opened: `report: ${message}` }),
      library: async () => used(),
      // fair play, switched off like the real launcher (rusemod.fairplay.ON) except in ?fake=fair (on),
      // ?fake=fairoffline (a copy built with a test tool), ?fake=fairchanged (a copy edited since its build), and
      // ?fake=agree (on, with the terms not yet accepted, so the first-start agreement shows)
      fair_play_on: async () => ({ on: /^(fair|agree)/.test(String(mode || "")) }),
      // the guard terms the agreement screen reads and sets (rusemod.guard; ?fake=agree starts with them unaccepted)
      guard_status: async () => ({ terms: fakeTerms, terms_version: 3, scan: false, on: true }),
      guard_accept_terms: async () => { fakeTerms = 3; return { terms: 3 }; },
      fair_play: async () => ({ built: true, code: ["fairoffline", "fairchanged"].includes(mode) ? null : myCode,
        why: mode === "fairoffline" ? "offline" : mode === "fairchanged" ? "changed" : null, fingerprint: "K7Q2-M9XD",
        mods: [["airfield-capacity", "1.0.0"], ["passable-forests", "1.0.0"]],
        offline: mode === "fairoffline" ? ["Money Test Tool is a cheat or a test tool"] : [], scripts: [], watch: true,
        problems: mode === "fairchanged" ? ["Data/PC/190852/ZZ_GladPatchableWin.dat changed after the build"] : [] }),
      compare_code: async (text) => {
        if (!text.trim().toUpperCase().startsWith("RUSE1:")) throw new Error("That isn't a R.U.S.E. join code (they start with RUSE1:).");
        return text.trim() === myCode ? { same: true, differences: [] }
          : { same: false, differences: ["They have passable-forests 1.1.0; you have 1.0.0.", "You have airfield-capacity 1.0.0; they don't."] };
      },
      trust_mod: async (id, yes) => {
        const mod = known(id);
        if (!mod) throw new Error(`There's no mod '${id}' in the library.`);
        mod.trusted = Boolean(yes);
        return lists({ mod: id });
      },
      mod_sets: async () => modSets(),
      add_mod: async (path) => fakeMod(path.split(/[\\/]/).pop()),
      add_mod_file: async () => fakeMod("Pacific Maps.zip"),
      // Convert an old mod (LauncherApi.convert_pick / convert_scan / convert): a made-up old mod's two packs
      convert_pick: async () => fakeConvertScan(),
      convert_scan: async () => fakeConvertScan(),
      convert: async (folder, name, version) => {
        if (!String(name || "").trim()) throw new Error("Give the mod a name first.");
        if (!/^\d+(\.\d+){0,2}$/.test(String(version || "").trim())) throw new Error("The version is numbers with dots, like 1.0.0.");
        const result = {}, id = slug(name);
        return backupJob(["── Data/PC/190852/ZZ_GladPatchableWin.dat ──", "  12 NDF change(s)",
          "── Data/PC/190852/ZZ_Win.dat ──", "  3 loc entry change(s)",
          "Total: 12 NDF change(s), 0 scenario NDF change(s), 3 loc entry change(s), 0 SDB layer(s), 0 raw file patch(es)"],
        "The old mod was converted and added to your library.", result, () => {
          library = library.filter((x) => x.id !== id);
          library.push({ id, name: name.trim(), version, authors: [], author: "", description: "", builds: [], used_in: 0 });
          library.sort((a, b) => a.name.localeCompare(b.name));
          Object.assign(result, lists({ mod: known(id), replaced: false, problems: [] }));
        });
      },
      remove_mod: async (id) => {
        const mod = known(id);
        if (!mod) throw new Error(`There's no mod called '${id}' in the library.`);
        library = library.filter((m) => m.id !== id);
        return lists({ mod });
      },
      // where things are kept (LauncherApi.where_files, show_folder): the library, and the Studio's in Documents
      where_files: async () => ({ library: "C:\\Users\\You\\AppData\\Local\\RUSE Mod Platform\\library",
        mods: "C:\\Users\\You\\Documents\\RUSE 2.0\\Mods", maps: "C:\\Users\\You\\Documents\\RUSE 2.0\\Maps",
        exports: "C:\\Users\\You\\Documents\\RUSE 2.0\\Exports", documents: true }),
      show_folder: async (what, id = "") => {
        if (id && !known(id)) throw new Error(`There's no mod called '${id}' in the library.`);
        const at = await window.pywebview.api.where_files();
        return { opened: id ? `${at.library}\\${id}` : at[what] };
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
      move_below: async (id, move, below) => {
        const s = sets.find((x) => x.id === id);
        const order = s.mods.filter((m) => m !== move);
        if (!order.includes(below) || order.length === s.mods.length) throw new Error("That mod isn't in this mod set any more.");
        order.splice(order.indexOf(below) + 1, 0, move);
        s.mods = order;
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
      language_choice: async () => ({ suggested: mode === "lang" ? "fr" : "us", from: mode === "lang" ? "steam" : "pc",
        chosen: Boolean(prefs.lang_chosen) || !(mode === "lang" || mode.startsWith("first")) }),
      first_run: async () => ({ show: !chosen && !library.length }),
      first_run_done: async () => { chosen = true; return { show: false }; },
      install_mods: async (ids) => {
        const picked = ids.map((id) => listed.find((x) => x.id === id));
        if (!picked.length || picked.some((m) => !m)) throw new Error("Tick the mods to install.");
        const failing = mode === "installfail" ? picked[picked.length - 1] : null;  // the last one fails its check
        const lines = [];
        picked.forEach((m, i) => {
          if (picked.length > 1) lines.push(`(${i + 1}/${picked.length}) ${m.name}`);
          lines.push(`Downloading ${m.name} ${m.version} (${sizeText(m.size)})…`);
          lines.push(m === failing ? `The file for ${m.name} isn't the one the mod list promises (its size or checksum differs), so it wasn't installed.`
            : `${m.name} ${m.version} is in the library.`);
        });
        const ok = picked.filter((m) => m !== failing);
        playing = { id: "install", step: 0, lines, failed: Boolean(failing),
          message: failing ? `${ok.length} of ${picked.length} mods were installed. Not installed: ${failing.name} (its size or checksum differs).`
            : picked.length === 1 ? `${picked[0].name} is in the library.` : `The ${picked.length} mods are in the library.`,
          then: () => { for (const m of ok) { library = library.filter((x) => x.id !== m.id); library.push({ id: m.id, name: m.name,
            version: m.version, authors: [], author: m.author, description: m.description, builds: m.game_build ? [m.game_build] : [],
            used_in: 0 }); } library.sort((a, b) => a.name.localeCompare(b.name)); } };
        return { job: "install" };
      },
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
      backup_status: async () => backupStatus(),
      backup_requested: async () => ({ make: mode === "firstbackup" && !backups.some((b) => b.matches) }),  // the installer asked
      backup_make: async (replace) => {
        if (backups.some((b) => b.matches) && !replace) throw new Error("There's already a backup of this build.");
        if (mode === "nospace") {
          return backupJob(["0%"], "There isn't enough free space on D:\\ for the backup: it needs 5.4 GB, and 2.1 GB is free. Free some space, then try again.", null);
        }
        return backupJob(steps(""), "The backup is made.", { path: `${BACKUPS}\\${build}`, build, files: 61, size: 5690000000, size_gb: 5.3 },
          () => { backups = [backupOf(build, "2026-09-30 22:15")].concat(backups.filter((b) => !b.matches)); gameClean = true; });
      },
      backup_check: async (deep) => backupJob(steps(""), "The game's files are checked.",
        { build_matches: true, build, backup_build: build, ...gameDiffers(), files: 61, hashed: deep ? 61 : 2 }),
      backup_restore: async () => {
        if (mode === "running") return backupJob(steps("check "), "R.U.S.E. is running: RUSE.exe (process 4312). Close the game, then restore.", null);
        const d = gameDiffers();
        return backupJob(steps("check ").concat(steps("")), "The game's files are restored.",
          { restored: d.changed.length + d.missing.length, set_aside: d.added.length, kept: d.changed.length, left: [], build,
            set_aside_to: d.added.length + d.changed.length ? `${BACKUPS}\\set-aside-2026-09-30-221503` : null }, () => { gameClean = true; });
      },
      steam_verify: async () => ({ opened: "steam://validate/21970" }),
      job: async (job, since) => {
        if (backupJobs[job]) return backupJobView(job, since);
        playing.step = Math.min(playing.step + 2, playing.lines.length);
        const done = playing.step >= playing.lines.length;
        if (done && playing.then) { playing.then(); playing.then = null; }
        return { id: "fake", state: done ? (playing.failed ? "failed" : "done") : "running", message: done ? playing.message : "",
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
