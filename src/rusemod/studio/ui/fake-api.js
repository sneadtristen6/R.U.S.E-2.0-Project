// A made-up StudioApi, for working on the screens in a normal browser: open index.html?fake
// (?fake=noindex shows the "no index yet" state). Only English, French and Chinese words are included here; the real
// Studio has all ten languages. It does nothing in the real Studio window.
"use strict";

(function () {
  const mode = new URLSearchParams(location.search).get("fake");
  if (mode === null) return;
  const words = {
    us: { language: "Language", game_names: "Game names", search: "Search", all: "All", ground: "Ground",
      infantry: "Infantry", air: "Air", buildings: "Buildings", units: "{n} units", parts: "Parts", own_part: "its own",
      shared_part: "shared with other units", used_by: "Used by", copy_address: "Copy address",
      copy_unit: "Copy this unit into a mod", coming_next: "coming next",
      no_index: "No game index yet. Build it once (about a minute).", build_index: "Build the index",
      pick_unit: "Pick a unit on the left." },
    fr: { language: "Langue", game_names: "Noms du jeu", search: "Rechercher", all: "Tous", ground: "Terrestre",
      infantry: "Infanterie", air: "Aérien", buildings: "Bâtiments", units: "{n} unités", parts: "Composants",
      own_part: "le sien", shared_part: "partagé avec d'autres unités", used_by: "Utilisé par",
      copy_address: "Copier l'adresse", copy_unit: "Copier cette unité dans un mod", coming_next: "bientôt",
      no_index: "Pas encore d'index du jeu.", build_index: "Construire l'index", pick_unit: "Choisissez une unité à gauche." },
    sc: { language: "语言", game_names: "游戏原名", search: "搜索", all: "全部", ground: "地面", infantry: "步兵",
      air: "空军", buildings: "建筑", units: "{n} 个单位", parts: "组件", own_part: "自有", shared_part: "与其他单位共享",
      used_by: "被引用于", copy_address: "复制地址", copy_unit: "将此单位复制到模组", coming_next: "即将推出",
      no_index: "尚无游戏索引。", build_index: "建立索引", pick_unit: "请在左侧选择一个单位。" },
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
      DescriptorId: "Id", ClassNameForDebug: "Debug name", NameInMenuToken: "Name (text key)" },
    fr: { SeuilMort: "Points de vie", VitesseLineaire: "Vitesse", ProductionPrice: "Prix", ProductionTime: "Temps de production",
      DetectionBase: "Portée de vision", Factory: "Usine", PositionInMenu: "Position dans le menu", Nationalite: "Nation",
      DescriptorId: "Identifiant", ClassNameForDebug: "Nom de débogage", NameInMenuToken: "Nom (clé de texte)" },
    sc: { SeuilMort: "生命值", VitesseLineaire: "速度", ProductionPrice: "价格", ProductionTime: "生产时间",
      DetectionBase: "视野范围", Factory: "工厂", PositionInMenu: "菜单位置", Nationalite: "国家", DescriptorId: "编号",
      ClassNameForDebug: "调试名称", NameInMenuToken: "名称(文本键)" },
  };
  const groups = {
    us: { identity: "Identity", cost: "Cost", combat: "Combat", movement: "Movement", vision: "Vision", menu: "Build menu" },
    fr: { identity: "Identité", cost: "Coût", combat: "Combat", movement: "Déplacement", vision: "Vision", menu: "Menu de production" },
    sc: { identity: "标识", cost: "成本", combat: "战斗", movement: "移动", vision: "视野", menu: "生产菜单" },
  };
  const E = "$/GFX/Everything/Descriptor_Unit_";
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
  const nameOf = (u, lang) => lang === "base" ? E.slice(17) + u.id : (u.names[lang] || u.names.us);
  const label = (prop, lang) => lang === "base" ? prop : ((labels[lang] || labels.us)[prop] || prop);
  const words_ = (lang) => words[lang] || words.us;
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
      unit: async (address, lang) => {
        const u = units.find((x) => E + x.id === address) || units[0];
        const g = groups[lang] || groups.us;
        const row = (prop, group, values) => ({ prop, label: label(prop, lang), group, values });
        const nationName = (nations[lang] || nations.base)[u.nation];
        return {
          address: E + u.id, class: u.kind === "air" ? "TAvionDescriptor" : u.kind === "infantry" ? "TInfanterieDescriptor" : "TUniteAuSolDescriptor",
          name: nameOf(u, lang), stable: true, shared: false, owners: [],
          groups: [
            { key: "identity", name: g.identity, rows: [row("Nationalite", "identity", [`${u.nation} (${nationName})`]),
              row("DescriptorId", "identity", ["187"]), row("ClassNameForDebug", "identity", ["Unit_" + u.id]),
              row("NameInMenuToken", "identity", [lang === "base" ? u.key : `${u.key} (${nameOf(u, lang)})`])] },
            { key: "cost", name: g.cost, rows: [row("ProductionPrice", "cost", Array(5).fill(String(u.price))),
              row("ProductionTime", "cost", ["20"])] },
            { key: "combat", name: g.combat, rows: [row("SeuilMort", "combat", [String(u.hp)])] },
            { key: "movement", name: g.movement, rows: [row("VitesseLineaire", "movement", [String(u.speed)])] },
            { key: "vision", name: g.vision, rows: [row("DetectionBase", "vision", ["2500"])] },
            { key: "menu", name: g.menu, rows: [row("Factory", "menu", [String(u.factory)]),
              row("PositionInMenu", "menu", [String(u.slot)])] },
          ],
          parts: [{ address: E + u.id + ":WeaponManager.Turrets[0]", class: "TTurretTwoAxisDescriptor", shared: false },
            { address: "$/GFX/Everything/Ammo_75mm_M3", class: "TAmmunition", shared: true }],
          used_by: [{ address: "$/GFX/Everything/Menu_Armour_US", path: "Units[3]" }],
        };
      },
      build_index: async () => ({ job: "fake" }),
      job: async () => ({ state: "done", message: "The game index is ready.", lines: ["  ZZ_Win.dat"], count: 1 }),
    },
  };
  window.addEventListener("load", () => window.dispatchEvent(new Event("pywebviewready")));
})();
