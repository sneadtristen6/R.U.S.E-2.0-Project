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
      shared_by: "Shared by {n}: {names}", change_for: "Change it for", only_unit: "only {name} (it gets its own copy)",
      all_units: "all {n} of them", no_via: "Open it from one of their pages to change it for that one only.",
      not_stable: "No stable address, so it can't be edited yet.", locked: "Ids and nation stay as they are.",
      edited: "edited", units_tab: "Units", maps_tab: "Maps",
      pick_map: "Pick a map to see its ground in 3D.", map_loading: "Loading the map…", detail_high: "Full detail",
      detail_low: "Light", water: "Water", map_help: "Drag to turn · right-drag to move · wheel to zoom",
      map_stats: "{points} points, {triangles} triangles",
      no_viewer: "The map view couldn't load its 3D library (it needs the internet the first time).",
      ground_loading: "Loading the real ground textures… {progress}", shape_ground: "Shape the ground",
      brush_hill: "Hill", brush_raise: "Raise", brush_lower: "Lower", brush_crater: "Crater", brush_plateau: "Plateau",
      brush_flatten: "Flatten", brush_smooth: "Smooth", brush_size: "Size", brush_strength: "Strength",
      brush_look: "Look around", brush_undo: "Undo",
      brush_help: "Click or drag on the ground to paint · middle-drag to turn · right-drag to move · wheel to zoom",
      brush_count: "Strokes on this map: {n}", brush_note: "Saved in the mod. \"Test in game\" builds it into the map.",
      all_values: "all {n}", each_value: "set each",
      price_dates: "One price per battle date: the host picks the date (1939, 1942, 1945, Total War) when setting up a battle.",
      new_unit: "New unit…", new_unit_name: "Name of the new unit (shown in every language)",
      price: "Price (every battle date)", build_menu: "Build menu", same_menu: "The same as {name}",
      other_menu: "Another one", nation: "Nation", factory: "Factory (shown by the units in it)",
      more_units: "and {n} more", copy_of: "A copy of {name}, made in this mod.", delete_unit: "Delete this unit",
      really_delete: "Delete {name}? Its changes go with it.", new_mark: "new",
      unit_made: "{name} is in the mod. Test in game to see it in its build menu.",
      unit_deleted: "{name} was deleted from the mod." },
    fr: { language: "Langue", game_names: "Noms du jeu", search: "Rechercher", all: "Tous", ground: "Terrestre",
      infantry: "Infanterie", air: "Aérien", buildings: "Bâtiments", units: "{n} unités", parts: "Composants",
      uses: "Utilise", own_part: "le sien", shared_part: "partagé avec d'autres unités", used_by: "Utilisé par",
      copy_address: "Copier l'adresse", no_index: "Pas encore d'index du jeu.", build_index: "Construire l'index",
      pick_unit: "Choisissez une unité à gauche.", mod: "Mod", new_mod: "Nouveau mod…",
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
      map_loading: "Chargement de la carte…", detail_high: "Détail complet", detail_low: "Allégé", water: "Eau",
      map_help: "Glisser pour tourner · clic droit pour déplacer · molette pour zoomer",
      map_stats: "{points} points, {triangles} triangles",
      no_viewer: "La vue de carte n'a pas pu charger sa bibliothèque 3D (il faut Internet la première fois).",
      ground_loading: "Chargement des vraies textures du sol… {progress}", shape_ground: "Modeler le terrain",
      brush_hill: "Colline", brush_raise: "Surélever", brush_lower: "Abaisser", brush_crater: "Cratère",
      brush_plateau: "Plateau", brush_flatten: "Aplanir", brush_smooth: "Adoucir", brush_size: "Taille",
      brush_strength: "Force", brush_look: "Regarder", brush_undo: "Annuler",
      brush_help: "Cliquez ou glissez sur le sol pour peindre · glisser du milieu pour tourner · clic droit pour déplacer · molette pour zoomer",
      brush_count: "Coups de pinceau sur cette carte : {n}",
      brush_note: "Enregistré dans le mod. « Tester en jeu » l'intègre à la carte.", all_values: "les {n}",
      each_value: "régler chacun",
      price_dates: "Un prix par date de bataille : l'hôte choisit la date (1939, 1942, 1945, Guerre totale) en préparant la partie.",
      new_unit: "Nouvelle unité…", new_unit_name: "Nom de la nouvelle unité (affiché dans toutes les langues)",
      price: "Prix (à chaque date de bataille)", build_menu: "Menu de production", same_menu: "Le même que {name}",
      other_menu: "Un autre", nation: "Nation", factory: "Usine (indiquée par ses unités)", more_units: "et {n} autres",
      copy_of: "Une copie de {name}, créée dans ce mod.", delete_unit: "Supprimer cette unité",
      really_delete: "Supprimer {name} ? Ses modifications disparaissent aussi.", new_mark: "nouveau",
      unit_made: "{name} est dans le mod. Testez en jeu pour le voir dans son menu de production.",
      unit_deleted: "{name} a été supprimé du mod." },
    sc: { language: "语言", game_names: "游戏原名", search: "搜索", all: "全部", ground: "地面", infantry: "步兵",
      air: "空军", buildings: "建筑", units: "{n} 个单位", parts: "组件", uses: "使用", own_part: "自有",
      shared_part: "与其他单位共享", used_by: "被引用于", copy_address: "复制地址", no_index: "尚无游戏索引。",
      build_index: "建立索引", pick_unit: "请在左侧选择一个单位。", mod: "模组", new_mod: "新建模组…",
      open_folder: "打开模组文件夹…", mod_name: "新模组名称", create: "创建", cancel: "取消", close: "关闭",
      no_mod: "请选择或新建一个模组来保存修改。", test_in_game: "在游戏中测试", was: "原为 {v}", reset: "撤销",
      saved: "已保存到 {file}", users_warning: "修改后,所有使用它的单位都会改变({n})。",
      shared_by: "{n} 个单位共用:{names}", change_for: "修改范围", only_unit: "仅 {name}(为其创建独立副本)",
      all_units: "全部 {n} 个", no_via: "从其中一个单位的页面打开,即可只修改那一个。", not_stable: "没有固定地址,暂时无法编辑。",
      locked: "编号和国家保持不变。", edited: "已修改", units_tab: "单位", maps_tab: "地图",
      pick_map: "选择一张地图，以 3D 查看其地形。", map_loading: "正在加载地图…", detail_high: "完整细节", detail_low: "简化",
      water: "水面", map_help: "拖动旋转 · 右键拖动平移 · 滚轮缩放", map_stats: "{points} 个点，{triangles} 个三角形",
      no_viewer: "地图视图无法加载 3D 库（首次需要联网）。", ground_loading: "正在加载真实地面纹理… {progress}",
      shape_ground: "塑造地形", brush_hill: "山丘", brush_raise: "抬高", brush_lower: "降低", brush_crater: "弹坑", brush_plateau: "高台",
      brush_flatten: "压平", brush_smooth: "平滑", brush_size: "大小", brush_strength: "强度", brush_look: "查看", brush_undo: "撤销",
      brush_help: "在地面上点击或拖动来绘制 · 中键拖动旋转 · 右键拖动平移 · 滚轮缩放", brush_count: "此地图上的笔画：{n}",
      brush_note: "已保存到模组。“在游戏中测试”会将其构建进地图。",
      all_values: "全部 {n} 个", each_value: "逐个设置", price_dates: "每个战役年代一个价格：房主在创建游戏时选择年代（1939、1942、1945、全面战争）。",
      new_unit: "新单位…", new_unit_name: "新单位的名称(所有语言均显示)", price: "价格(所有战役年代)", build_menu: "生产菜单",
      same_menu: "与 {name} 相同", other_menu: "另一个", nation: "国家", factory: "工厂(按其中的单位显示)", more_units: "及另外 {n} 个",
      copy_of: "在此模组中创建的 {name} 的副本。", delete_unit: "删除此单位", really_delete: "删除 {name}?它的修改也会一并删除。",
      new_mark: "新", unit_made: "{name} 已加入模组。在游戏中测试即可在生产菜单中看到它。", unit_deleted: "已从模组中删除 {name}。" },
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
  const mods = [{ path: home + "pacific-test", name: "pacific-test" }];
  let current = mode === "nomod" ? null : mods[0].path;
  const edits = new Map();  // `${mod}|${address}|${prop}|${how}|${via}` -> value, like the mod's src/studio.rndf
  const terrains = new Map();  // `${mod}|${map pack}` -> strokes, like the mod's maps/<pack>/terrain.toml
  const editKey = (address, prop, how, via) => `${current}|${address}|${prop}|${how || ""}|${how === "own" ? via : ""}`;
  if (current) edits.set(editKey(E + "M4_Sherman", "SeuilMort"), 14);
  if (current) newUnits.push({ mod: current, id: "Super_Sherman", source: E + "M4_Sherman", name: "Super Sherman",
    price: 55, nation: 0, factory: 10 });
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
  const fakeMaps = [
    { pack: "TwoIslands", names: ["(6) Centre de gravite"], paths: ["TwoIslands"], file: "DataMapTwoIslands_v09.dat" },
    { pack: "SuperCrossroads4", names: ["(4) Blitz"], paths: ["SuperCrossroads4"], file: "DataMapSuperCrossroads4_v09.dat" },
    { pack: "M02_Tunisie", names: ["M02_Tunisie_chapter1", "M02_Tunisie_chapter2"], paths: ["M02_Tunisie_chapter1"],
      file: "DataMapM02_Tunisie_v09.dat" },
  ].map((m) => ({ ...m, found: true }));

  async function packed(typed) {
    const stream = new Blob([typed]).stream().pipeThrough(new CompressionStream("deflate"));
    const bytes = new Uint8Array(await new Response(stream).arrayBuffer());
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
    return btoa(s);
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
        const path = "D:/Mods/pacific-maps";
        if (!mods.some((m) => m.path === path)) mods.push({ path, name: "pacific-maps" });
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
      build_index: async () => ({ job: "index" }),
      job: async (id) => ({ state: "done", message: jobs[id][1], lines: jobs[id][0], count: jobs[id][0].length }),
      maps: async () => ({ maps: fakeMaps }),
      map_view: async (pack, lod) => fakeGround(pack, lod || "lowdef"),
      map_ground: async () => ({ url: null }),  // the made-up island has only its colours
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
