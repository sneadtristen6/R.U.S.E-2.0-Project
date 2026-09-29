// A made-up LauncherApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=notfound shows the "game not found" state, ?fake=empty a launcher with no mods yet). Only English, French
// and Chinese words are included here; the real launcher has all ten languages. It does nothing in the real window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const words = {
    us: { language: "Language", looking: "Looking for R.U.S.E.…", choose_folder: "Choose folder…", mod_sets: "Mod sets",
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
    fr: { language: "Langue", looking: "Recherche de R.U.S.E.…", choose_folder: "Choisir le dossier…",
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
    sc: { language: "语言", looking: "正在查找 R.U.S.E.…", choose_folder: "选择文件夹…", mod_sets: "模组组合", vanilla: "原版",
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
  let library = mode === "empty" ? [] : [
    { id: "half-price-buildings", name: "Half-price buildings", version: "1.0.0", authors: ["RUSE Mod Platform"],
      author: "RUSE Mod Platform", description: "Every building costs half.", builds: [build], used_in: 1 },
    { id: "ruse2-core", name: "RUSE 2.0 Core", version: "0.4.1", authors: ["DomesticNukes", "Tristen"],
      author: "DomesticNukes, Tristen", description: "Balance, new units and tactics for RUSE 2.0.", builds: ["24670294"], used_in: 1 },
    { id: "ruse2-china", name: "RUSE 2.0 China", version: "0.1.0", authors: [], author: "", description: "", builds: [], used_in: 1 },
  ];
  let sets = mode === "empty" ? [] : [
    { id: "half-price", name: "Half-price test", description: "Every building costs half.", mods: ["half-price-buildings"] },
    { id: "ruse2", name: "RUSE 2.0", description: "Balance, new units and China (draft).", mods: ["ruse2-core", "ruse2-china"] },
    { id: "old", name: "Old test", description: "", mods: ["old-units"] },
    { id: "hand-written", name: "Hand-written", description: "", mods: ["D:/mods/pacific-maps", "ruse2-core"] },
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
  const checkMods = (mods) => {
    if (!mods || !mods.length) throw new Error("Tick at least one mod for this mod set.");
    for (const m of mods) { const why = resolve(m); if (why) throw new Error(`This mod set can't be saved: ${why}.`); }
  };
  const fakeMod = (name) => {
    const id = name.toLowerCase().replace(/\.zip$/, "").replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "mod";
    if (id.endsWith("exe")) throw new Error(`${name} isn't a mod: add a mod folder (with mod.toml in it) or a .zip of one.`);
    const replaced = Boolean(known(id));
    library = library.filter((m) => m.id !== id);
    const mod = { id, name: name.replace(/\.zip$/, ""), version: replaced ? "1.1.0" : "1.0.0", authors: ["you"], author: "you",
      description: "Added from a file.", builds: [build], used_in: 0 };
    library.push(mod);
    library.sort((a, b) => a.name.localeCompare(b.name));
    return lists({ mod, replaced });
  };
  const script = [
    "Building the modded copy of R.U.S.E. for Half-price test in D:\\RUSE-Instances\\half-price…",
    "load order: half-price-buildings",
    "  note     left 4 debug-info copies as shipped (everything_debuginfo.cpp.gladndfbin, …)",
    "0 error(s), 0 warning(s), 3 note(s)",
    "changed: genglad\\patchable\\gfx\\everything.cpp.gladndfbin",
    "fingerprint: S1HP-X6PM",
    "modded copy ready: D:\\RUSE-Instances\\half-price  {'linked': 37, 'copied': 23, 'written': 1}",
    "Starting R.U.S.E. from the modded copy…",
  ];
  const listed = [
    { id: "half-price-buildings", name: "Half-price buildings", version: "1.0.0", author: "RUSE Mod Platform",
      description: "Every building costs half.", homepage: "https://github.com/sneadtristen6/Ruse-Mod-Platform",
      download: "https://example.invalid/half.rusemod", size: 2048, sha256: "0".repeat(64), game_build: build,
      fingerprint: "S1HP-X6PM", tags: ["economy", "test"] },
    { id: "ruse2-core", name: "RUSE 2.0 Core", version: "0.5.0", author: "DomesticNukes, Tristen",
      description: "Balance, new units and tactics for RUSE 2.0.", homepage: "", download: "https://example.invalid/core.rusemod",
      size: 4300000, sha256: "0".repeat(64), game_build: "24670294", fingerprint: "K7Q2-M9XD", tags: ["overhaul"] },
    { id: "airfield-capacity", name: "Airfield Capacity", version: "1.0.0", author: "",
      description: "Airfields hold 128 planes instead of 8.", homepage: "", download: "https://example.invalid/air.rusemod",
      size: 1200, sha256: "0".repeat(64), game_build: "24087620", fingerprint: "", tags: ["air"] },
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
      delete_set: async (id) => {
        sets = sets.filter((x) => x.id !== id);
        return lists({ set: "vanilla" });
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
