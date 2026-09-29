// A made-up StudioApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=noindex shows the "no index yet" state, ?fake=nomod the Studio before any mod is picked). Only English, French
// and Chinese words are included here; the real Studio has all ten languages. It does nothing in the real Studio window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const words = {
    us: { language: "Language", game_names: "Game names", search: "Search", all: "All", ground: "Ground",
      infantry: "Infantry", air: "Air", buildings: "Buildings", units: "{n} units", parts: "Parts", uses: "Uses",
      own_part: "its own", shared_part: "shared with other units", used_by: "Used by", copy_address: "Copy address",
      no_index: "No game index yet. Build it once (about a minute).", build_index: "Build the index",
      pick_unit: "Pick a unit on the left.", mod: "Mod", new_mod: "New mod…", open_folder: "Open a mod folder…",
      mod_name: "Name of the new mod", create: "Create", cancel: "Cancel", close: "Close",
      no_mod: "Pick or make a mod to save changes in.", test_in_game: "Test in game", was: "was {v}", reset: "Undo",
      saved: "Saved in {file}", users_warning: "Changing this changes it for every unit that uses it ({n}).",
      shared_part_later: "Shared with other units: editing it comes later.",
      not_stable: "No stable address, so it can't be edited yet.", locked: "Ids and nation stay as they are.",
      edited: "edited" },
    fr: { language: "Langue", game_names: "Noms du jeu", search: "Rechercher", all: "Tous", ground: "Terrestre",
      infantry: "Infanterie", air: "Aérien", buildings: "Bâtiments", units: "{n} unités", parts: "Composants",
      uses: "Utilise", own_part: "le sien", shared_part: "partagé avec d'autres unités", used_by: "Utilisé par",
      copy_address: "Copier l'adresse", no_index: "Pas encore d'index du jeu.", build_index: "Construire l'index",
      pick_unit: "Choisissez une unité à gauche.", mod: "Mod", new_mod: "Nouveau mod…",
      open_folder: "Ouvrir un dossier de mod…", mod_name: "Nom du nouveau mod", create: "Créer", cancel: "Annuler",
      close: "Fermer", no_mod: "Choisissez ou créez un mod pour enregistrer les modifications.",
      test_in_game: "Tester en jeu", was: "avant : {v}", reset: "Annuler", saved: "Enregistré dans {file}",
      users_warning: "Le modifier le change pour toutes les unités qui l'utilisent ({n}).",
      shared_part_later: "Partagé avec d'autres unités : modifiable plus tard.",
      not_stable: "Pas d'adresse stable : pas encore modifiable.",
      locked: "Les identifiants et la nation restent tels quels.", edited: "modifié" },
    sc: { language: "语言", game_names: "游戏原名", search: "搜索", all: "全部", ground: "地面", infantry: "步兵",
      air: "空军", buildings: "建筑", units: "{n} 个单位", parts: "组件", uses: "使用", own_part: "自有",
      shared_part: "与其他单位共享", used_by: "被引用于", copy_address: "复制地址", no_index: "尚无游戏索引。",
      build_index: "建立索引", pick_unit: "请在左侧选择一个单位。", mod: "模组", new_mod: "新建模组…",
      open_folder: "打开模组文件夹…", mod_name: "新模组名称", create: "创建", cancel: "取消", close: "关闭",
      no_mod: "请选择或新建一个模组来保存修改。", test_in_game: "在游戏中测试", was: "原为 {v}", reset: "撤销",
      saved: "已保存到 {file}", users_warning: "修改后,所有使用它的单位都会改变({n})。",
      shared_part_later: "与其他单位共享:稍后支持编辑。", not_stable: "没有固定地址,暂时无法编辑。",
      locked: "编号和国家保持不变。", edited: "已修改" },
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
  const home = "C:/Users/You/AppData/Local/RUSE Mod Platform/mods/";
  const mods = [{ path: home + "pacific-test", name: "pacific-test" }];
  let current = mode === "nomod" ? null : mods[0].path;
  const edits = new Map();  // `${mod}|${address}|${prop}` -> value, like the mod's src/studio.rndf
  const editKey = (address, prop) => `${current}|${address}|${prop}`;
  if (current) edits.set(editKey(E + "M4_Sherman", "SeuilMort"), 14);

  const nameOf = (u, lang) => lang === "base" ? E.slice(17) + u.id : (u.names[lang] || u.names.us);
  const label = (prop, lang) => lang === "base" ? prop : ((labels[lang] || labels.us)[prop] || prop);
  const words_ = (lang) => words[lang] || words.us;
  const modsView = () => ({ mods: mods.slice(), current });

  // one object's values, as StudioApi.unit() gives them
  function view(address, lang, cls, name, editable, whyNot, users, rowsByGroup, parts, uses, usedBy) {
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
          edited: edits.has(editKey(address, prop)) ? edits.get(editKey(address, prop)) : null };
      }) });
    }
    return { address, class: cls, name, stable: true, shared: false, owners: [], groups: out, parts, uses,
      used_by: usedBy, editable, why_not: whyNot, users };
  }

  function unit(address, lang) {
    if (address === AMMO) {
      return view(AMMO, lang, "TAmmunition", "Ammo_75mm_M3", true, "", 3,
        [["weapon", [["Puissance", 40], ["PorteeMaximale", 2800], ["TempsEntreDeuxTirs", 3.5, { type: "float32" }]]]],
        [], [], [{ address: E + "M4_Sherman:WeaponManager.Turrets[class=TTurretTwoAxisDescriptor]", path: "Ammo" }]);
    }
    if (address.endsWith(":Weapon.Blast")) {
      return view(address, lang, "TDamageDescriptor", address.split(":").pop(), false, "shared_part_later", 0,
        [["weapon", [["Puissance", 6]]]], [], [], []);
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
      shared: false }, { address: E + u.id + ":Weapon.Blast", class: "TDamageDescriptor", shared: true }],
    [{ address: AMMO, class: "TAmmunition" }], [{ address: "$/GFX/Everything/Menu_Armour_US", path: "Units[3]" }]);
  }

  const jobs = {
    index: [["  ZZ_Win.dat"], "The game index is ready."],
    test: [["Building the modded copy of R.U.S.E. for pacific-test in D:\\RUSE-Instances\\studio-pacific-test…",
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
        const out = units.filter((u) => (kind === "all" || u.kind === kind) && (nation < 0 || u.nation === nation))
          .map((u) => ({ address: E + u.id, name: nameOf(u, lang), base_name: "Descriptor_Unit_" + u.id, kind: u.kind,
            nation: u.nation, nation_name: (nations[lang] || nations.us)[u.nation], factory: u.factory, slot: u.slot }))
          .filter((u) => !search || u.name.toLowerCase().includes(search.toLowerCase()));
        return { units: out, total: units.length };
      },
      unit: async (address, lang) => unit(address, lang),
      mods: async () => modsView(),
      new_mod: async (name) => {
        const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "my-mod";
        mods.push({ path: home + slug, name: slug });
        current = home + slug;
        return modsView();
      },
      choose_mod: async (path) => { current = path; return modsView(); },
      open_mod_folder: async () => {
        const path = "D:/Mods/pacific-maps";
        if (!mods.some((m) => m.path === path)) mods.push({ path, name: "pacific-maps" });
        current = path;
        return modsView();
      },
      edited: async () => [...new Set([...edits.keys()].filter((k) => k.startsWith(current + "|"))
        .map((k) => k.split("|")[1].split(":")[0]))],
      edit: async (address, prop, value) => {
        if (!current) throw new Error("Pick or make a mod first: changes are saved in a mod.");
        const r = unit(address, "us").groups.flatMap((g) => g.rows).find((x) => x.prop === prop);
        const whole = (v) => r.type === "float32" ? v : Math.sign(v) * Math.round(Math.abs(v));
        const v = Array.isArray(value) ? value.map(whole) : whole(value);
        const same = Array.isArray(v) ? v.every((x, i) => x === r.numbers[i]) : v === r.numbers[0];
        if (same) edits.delete(editKey(address, prop)); else edits.set(editKey(address, prop), v);
        return { saved: current + "/src/studio.rndf", value: v };
      },
      reset: async (address, prop) => { edits.delete(editKey(address, prop)); return { saved: current + "/src/studio.rndf" }; },
      test_in_game: async () => ({ job: "test" }),
      build_index: async () => ({ job: "index" }),
      job: async (id) => ({ state: "done", message: jobs[id][1], lines: jobs[id][0], count: jobs[id][0].length }),
    },
  };
  window.addEventListener("load", () => window.dispatchEvent(new Event("pywebviewready")));
})();
