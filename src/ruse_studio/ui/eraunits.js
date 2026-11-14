// Era units in the Units tab (StudioApi.era_units_list / era_unit_page / era_unit_add / era_unit_remove,
// ruse_studio.era_units): the era filter above the kinds picks Vanilla (the game's own units, the list as always) or an
// era (WWI, WWII+, Cold War, Modern: RUSE 2.0's units, each another maker's free model, credited, fitted and marked).
// An era's units are listed and filtered like the game's (kind, nation, type, search); none is in the mod until added
// (the owner, 2026-10-08). An era unit's page shows its model's picture and credit, and adds it to the mod: it starts
// from the values of any game unit of its kind (the library's suggestion first; the owner: "what if they don't want to
// make it the same as a Sherman?"), with the name, price, size, build menu and the unit it's researched from given;
// then it's a new unit like any other, its page open to change every value. Uses app.js's $, el, fill, say, problem,
// api, state, renderChips, refreshList, renderGroups, showUnit and factoryLabel, and its research helpers (researchAsk,
// researchTold, timeUnit, timeShown, timeSeconds, timeUnitPicker).
// The Horse Squad (StudioApi.horse_squad_add, ruse_studio.horse_squad) is listed in WWII+ beside them, downloaded or
// not ("built": nothing of it is downloaded; the owner, 2026-11-12: "Yes, like era units"): its page credits its maker,
// and Add to my mod makes its horses and riders from the modder's own game first, the steps shown as they go.
(function () {
  "use strict";
  const ERAS = [["vanilla", "era_vanilla"], ["WWI", "eras_era_ww1"], ["WWII", "eras_era_ww2"],
    ["Cold War", "eras_era_cold"], ["Modern", "eras_era_modern"]];
  const NATION_WORD = { USA: "eras_nation_usa", Germany: "eras_nation_germany", UK: "eras_nation_uk",
    France: "eras_nation_france", Italy: "eras_nation_italy", USSR: "eras_nation_ussr", Russia: "eras_nation_russia",
    Japan: "eras_nation_japan", China: "eras_nation_china" };
  const CHINA = 7;  // the nation chip for China, which has no game nation of its own
  // why a unit to research it from is suggested (StudioApi.era_unit_start's research.why)
  const WHY = { start: "eras_research_why_start", in_place_of: "eras_research_why_in_place_of",
    dearest: "eras_research_why_dearest" };
  // the board's word for each of the game's buildings that make units (board.js ROW_GROUP)
  const BUILDING_WORD = { 8: "group_barracks", 13: "group_artillery", 10: "group_armor", 11: "group_antitank",
    9: "group_airfield", 12: "group_prototype" };
  const NEW_GROUP = "new";  // era_unit_start / era_unit_add's group for a group of its own (groups.py NEW)
  const HORSE = "horse-squad";  // the Horse Squad's key (horse_squad.KEY): its name in the Studio's language
  // what horse_squad_add's job is doing, by its lines (horse_squad.STEPS)
  const HORSE_STEPS = { build: "eras_horse_step_build", unit: "eras_horse_step_unit",
    riflemen: "eras_horse_step_riflemen", bazooka: "eras_horse_step_bazooka" };
  const W = () => state.words;
  const round3 = (x) => String(Math.round(x * 1000) / 1000);
  const nationOf = (n) => W()[NATION_WORD[n]] || n;
  const eraOf = (era) => W()[(ERAS.find(([k]) => k === era) || [])[1]] || era;
  const unitName = (u) => (u.built && u.key === HORSE ? W().eras_horse_name : u.name);
  const clock = (ms) => {  // m:ss since it started
    const s = Math.max(0, Math.round(ms / 1000));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
  };

  // the era filter, above the kinds; the era note under the chips
  function renderEraChips() {
    const w = W();
    $("eras").replaceChildren(...ERAS.map(([key, word]) => {
      const b = el("button", { type: "button", className: "chip", textContent: w[word], title: w.tip_era_chip });
      b.setAttribute("aria-pressed", String(state.era === key));
      b.addEventListener("click", () => {
        if (state.era === key) return;
        state.era = key;
        state.group = "all";
        if (key !== "vanilla" && !["all", "ground", "air"].includes(state.kind)) state.kind = "all";
        if (key === "vanilla" && state.nation === CHINA) state.nation = -1;
        renderChips();
        refreshList();
      });
      return b;
    }));
    $("era-note").textContent = state.era === "vanilla" ? "" : w.eras_note;
    $("era-note").classList.toggle("hidden", state.era === "vanilla");
    updateDownloaded();
  }

  // an era not on this PC yet: downloaded from RUSE 2.0's GitHub when the modder presses Download (each file checked
  // by the Studio before it's used); a downloaded era updates itself when a newer one is out (the owner, 2026-10-08:
  // "have the studio auto-update with them")
  const coming = {};  // era -> its download's job, while it runs
  const sizeOf = (n) => (n >= 1e9 ? `${(n / 1e9).toFixed(1)} GB` : `${Math.max(1, Math.round(n / 1e6))} MB`);

  async function sections() {
    if (!state.eraSections) {
      try { state.eraSections = await api().era_sections(false); } catch (err) {
        problem(err);
        return { sections: [], message: "" };
      }
    }
    return state.eraSections;
  }

  async function downloadPanel(era) {
    const w = W();
    const list = await sections();
    const s = list.sections.find((x) => x.era === era);
    if (!s) {
      return el("div", { className: "notice" }, el("p", { textContent: list.message
        ? fill(w.eras_no_list, { why: list.message }) : fill(w.eras_none_yet, { era: eraOf(era) }) }));
    }
    const go = el("button", { type: "button", className: "primary", textContent: fill(w.eras_download, { era: eraOf(era) }),
      title: w.tip_eras_download });
    const status = el("p", { className: "small muted" });
    go.addEventListener("click", () => follow(era, go, status));
    if (coming[era]) follow(era, go, status);  // already coming: follow it here
    return el("div", { className: "notice" },
      el("p", { textContent: fill(w.eras_not_downloaded, { era: eraOf(era), n: s.units, size: sizeOf(s.size) }) }),
      el("div", { className: "actions" }, go), status);
  }

  async function follow(era, button, status) {
    const w = W();
    if (button) button.disabled = true;
    let job = coming[era];
    if (!job) {
      try { job = (await api().era_download(era)).job; } catch (err) {
        problem(err);
        if (button) button.disabled = false;
        return;
      }
      coming[era] = job;
    }
    let seen = 0;
    const tick = async () => {
      let j;
      try { j = await api().job(job, seen); } catch (err) { problem(err); delete coming[era]; return; }
      seen = j.count;
      const last = j.lines[j.lines.length - 1];
      if (status && last === "unpack") status.textContent = w.eras_unpacking;
      else if (status && last) {
        const [done, total] = last.split("/").map(Number);
        status.textContent = fill(w.eras_downloading, { done: sizeOf(done), total: sizeOf(total) });
      }
      if (j.state === "running") { setTimeout(tick, 500); return; }
      delete coming[era];
      state.eraSections = null;
      if (j.state === "done") {
        say(fill(w.eras_download_done, { era: eraOf(era) }), "ok");
        if (state.era === era) refreshList();
      } else {
        say(j.message, "error");
        if (button) button.disabled = false;
        if (status) status.textContent = "";
      }
    };
    tick();
  }

  let checked = false;
  async function updateDownloaded() {  // once a start: the downloaded eras with a newer version out
    if (checked) return;
    checked = true;
    let res;
    try { res = await api().era_sections(true); } catch { return; }
    for (const s of res.sections.filter((x) => x.state === "update")) {
      say(fill(W().eras_updating, { era: eraOf(s.era) }), "ok");
      follow(s.era, null, null);
    }
  }

  async function refreshEraList() {
    const w = W();
    let res;
    try {  // (the Horse Squad's type in the Studio's language: the game's word for it; an era unit's its library's)
      res = await api().era_units_list(state.era, state.kind, state.nation, state.search, state.group || "all",
        state.lang);
      if ((state.group || "").startsWith("type:") && !(res.types || []).includes(state.group.slice(5))) {
        state.group = "all";  // a type picked in another language: show them all again (as app.js refreshList)
        res = await api().era_units_list(state.era, state.kind, state.nation, state.search, "all", state.lang);
      }
    } catch (err) { problem(err); return; }
    $("era-note").classList.toggle("hidden", !res.installed);  // the models' note only over models
    $("count").textContent = w.units.replace("{n}", res.units.length);
    renderGroups([], res.types || []);
    const rows = res.units.map((u) => {
      const b = el("button", { type: "button", title: w.tip_open_unit },
        el("span", { className: "name", textContent: unitName(u) }),
        el("span", { className: "sub", textContent: [nationOf(u.nation), u.card,
          ...(u.built ? [fill(w.eras_horse_by, { author: u.by || "" })] : []),
          ...(u.added ? [w.eras_in_mod_badge] : [])].filter(Boolean).join(" · ") }));
      b.dataset.address = "era:" + u.key;
      if (u.added) b.prepend(el("span", { className: "badge new", textContent: state.words.new_mark }));
      b.setAttribute("aria-current", String(state.selected === "era:" + u.key));
      b.addEventListener("click", () => showEraPage(u.key));
      return el("li", {}, b);
    });
    if (!res.installed) {  // the era's own units not on this PC: its download, under what needs none (the Horse Squad)
      const era = state.era;
      const panel = await downloadPanel(era);
      if (state.era === era) $("unit-list").replaceChildren(...rows, el("li", {}, panel));
      return;
    }
    $("unit-list").replaceChildren(...rows);
  }

  async function showEraPage(key) {
    const w = W();
    state.selected = "era:" + key;
    for (const b of $("unit-list").querySelectorAll("button")) {
      b.setAttribute("aria-current", String(b.dataset.address === state.selected));
    }
    let p;
    try { p = await api().era_unit_page(key, state.lang); } catch (err) { problem(err); return; }
    state.page = null;
    state.eraPage = key;
    const facts = [eraOf(p.era), nationOf(p.nation), p.card].filter(Boolean);
    if (p.in_place_of) facts.push(fill(w.eras_in_place_of, { name: p.in_place_of }));
    const c = p.credit || {};
    const parts = [el("h1", { textContent: unitName(p) }), el("p", { className: "unit-desc", textContent: facts.join(" · ") })];
    if (p.built) {  // made for RUSE 2.0, from the modder's own game when added: its maker, and what adding it does
      parts.push(el("p", { className: "small", textContent: fill(w.eras_horse_made_by, { author: c.author || "" }) }),
        el("p", { className: "notice", textContent: w.eras_horse_what }));
    } else {
      const credit = el("p", { className: "small" },
        el("span", { textContent: fill(w.eras_model_by, { author: c.author || "", licence: c.licence || "" }) + " " }),
        el("a", { href: c.url || "#", target: "_blank", rel: "noopener", textContent: c.title || "", title: w.tip_eras_credit }),
        ...(c.extra ? [el("span", { textContent: ` · ${c.extra}` })] : []));
      if (p.picture) parts.push(el("img", { src: p.picture, alt: p.name, className: "era-picture" }));
      parts.push(credit);
      if (!p.has_model) parts.push(el("p", { className: "notice warn", textContent: w.eras_game_model }));
      else if (!p.fits) parts.push(el("p", { className: "notice warn", textContent: w.eras_no_fit }));
    }
    if (!state.mod) parts.push(el("p", { className: "notice", textContent: w.no_mod }));
    else if (p.added && !p.building) parts.push(addedBox(p));  // (the Horse Squad being made: its steps, not Take out)
    else parts.push(await addForm(p));
    $("detail").replaceChildren(...parts);
    if (p.built && p.building) {  // being added already (this page was left, or opened again): follow it here
      if (!horseJob || horseJob.id !== p.building) horseJob = { id: p.building, began: Date.now() };
      followHorse();
    }
  }

  // the Horse Squad being added: horse_squad_add's job, followed by one loop whichever page is shown; its steps are
  // said under its Add to my mod while its page is open, and its page opens when it's done (the page still shown)
  let horseJob = null;  // { id, began }
  let horseLoop = false;
  async function followHorse() {
    if (horseLoop || !horseJob) return;
    horseLoop = true;
    const job = horseJob;
    let seen = 0, step = "build";
    const shown = () => ({ status: $("detail").querySelector("[data-horse-status]"),
      add: $("detail").querySelector("[data-horse-add]") });
    for (;;) {
      let j;
      try { j = await api().job(job.id, seen); } catch (err) {
        problem(err);
        break;
      }
      seen = j.count;
      for (const line of j.lines) if (HORSE_STEPS[line]) step = line;
      const { status, add } = shown();
      if (add) add.disabled = true;
      if (status) status.textContent = fill(W()[HORSE_STEPS[step]], { time: clock(Date.now() - job.began) });
      if (j.state === "running") { await new Promise((r) => setTimeout(r, 500)); continue; }
      if (j.state === "done") {
        const res = j.result || {};
        say(fill(W().eras_added, { name: res.name || W().eras_horse_name }), "ok");
        horseJob = null;
        horseLoop = false;
        if (state.eraPage === HORSE && res.address) await openMade(res.address);
        else if (state.era !== "vanilla" && state.view === "units") await refreshList();
        return;
      }
      say(j.message, "error");  // refused in words (the game couldn't give what it needs): nothing was made
      await moveFix();  // (a path longer than Windows takes: the quick fix beside the words)
      break;
    }
    horseJob = null;
    horseLoop = false;
    const { status, add } = shown();
    if (status) status.textContent = "";
    if (add) add.disabled = false;
  }

  // A folder too deep for Windows (its 259 characters, with its long paths off): the refusal's words say what to do by
  // hand, and this box beside them does it in one click (StudioApi.home_move_offer, home_move; ruse_studio.homemove;
  // the owner, 2026-11-13: "tell the modder, provide a quick fix that auto does it if they dont want to do it
  // manually"): everything copied to a short folder, checked, switched to, the Studio started again, nothing deleted.
  async function moveFix() {
    const w = W();
    let o;
    try { o = await api().home_move_offer(); } catch (err) { problem(err); return; }
    const old = $("detail").querySelector("[data-home-move]");
    if (old) old.remove();
    if (!o.needed || !o.can) return;
    const status = el("p", { className: "small", textContent: "" });
    const go = el("button", { type: "button", className: "primary", textContent: fill(w.home_move_button, { to: o.to }),
      title: fill(w.tip_home_move, { to: o.to }) });
    const box = el("div", { className: "notice warn" },
      el("h3", { textContent: w.home_move_title }),
      el("p", { textContent: w.home_move_why }),
      el("p", { className: "small", textContent: fill(w.home_move_what, { from: o.from, to: o.to, n: o.count,
        size: o.size_text }) }),
      ...(o.files ? [el("p", { className: "small", textContent: fill(w.home_move_files, { files: o.files, to: o.to }) })] : []),
      el("p", { className: "small", textContent: w.home_move_close_launcher }),
      el("div", { className: "actions" }, go), status);
    go.addEventListener("click", async () => {
      go.disabled = true;
      let job;
      try { job = (await api().home_move()).job; } catch (err) { problem(err); go.disabled = false; return; }
      let seen = 0;
      for (;;) {
        let j;
        try { j = await api().job(job, seen); } catch (err) { problem(err); go.disabled = false; return; }
        seen = j.count;
        if (j.lines.length) status.textContent = j.lines[j.lines.length - 1];
        if (j.state === "running") { await new Promise((r) => setTimeout(r, 500)); continue; }
        if (j.state === "done") {
          const r = j.result || {};
          say(fill(r.restarting ? w.home_move_done : w.home_move_done_start_again,
            { to: r.to || o.to, old: (r.old || []).join(", ") }), "ok");
          return;
        }
        say(j.message, "error");  // nothing switched: the words say why, the copy taken away
        go.disabled = false;
        return;
      }
    });
    box.dataset.homeMove = "1";
    $("detail").append(box);
  }

  // in the mod already: to its page (every value changed there), or out of the mod again
  function addedBox(p) {
    const w = W();
    const open = el("button", { type: "button", className: "primary", textContent: w.eras_open_page, title: w.tip_eras_open_page });
    open.addEventListener("click", () => openMade(p.added));
    const out = el("button", { type: "button", className: "ghost danger", textContent: w.eras_take_out, title: w.tip_eras_take_out });
    const ask = el("div", { className: "hidden" });  // the warning, when units are researched from it (app.js researchAsk)
    // the units researched from it go as the modder chose in Settings > Research: warned first, refused (the Studio
    // says why), or re-linked to the unit it was researched from
    const remove = async (researched) => {
      out.disabled = true;
      try {
        const res = await api().era_unit_remove(p.key, researched);
        if (res.ask) {
          researchAsk(ask, unitName(p), res.ask, () => remove("anyway"), () => showEraPage(p.key));
          return;
        }
        researchTold(res, fill(w.eras_removed, { name: unitName(p) }));
        await refreshList();
        await showEraPage(p.key);
      } catch (err) { problem(err); out.disabled = false; }
    };
    out.addEventListener("click", () => remove(null));
    return el("div", { className: "notice new" }, el("p", { textContent: w.eras_in_mod_as }),
      el("div", { className: "actions" }, open, out), ask);
  }

  async function openMade(address) {
    state.era = "vanilla";
    state.group = "all";
    if (state.nation === CHINA) state.nation = -1;
    renderChips();
    await refreshList();
    await showUnit(address);
  }

  // add it: its name, the game unit it starts from (any of its kind), its price, its size, its build menu and the unit
  // it's researched from. Its size: 1 is as long as the start unit, the suggestion its real size (the owner,
  // 2026-10-09: "the units we add should be scaled proportionally with how big the units are ... in real life").
  // Researched from: any unit of the build menu picked, the mod's new ones too, or none (the owner: "If it's advanced,
  // I want it to be hidden behind the research ... it has to be super customizable"); the unit page's Upgrade box
  // changes it later. Its group: the row of that building's build list it goes in, the units it may be researched
  // from that group's. A start unit, build menu or group picked asks the Studio again (era_unit_start).
  async function addForm(p) {
    const w = W();
    const form = el("form", { className: "new-unit" });
    const name = el("input", { autocomplete: "off", maxLength: 60, required: true, value: unitName(p), title: w.tip_eras_name });
    name.setAttribute("aria-label", w.new_unit_name);
    // (the Generic Horse starts from the US rifle squad only: its horses and riders are made for that squad's soldiers.
    // One Generic Horse, never one per country: the owner, 2026-11-13, "So it does not need to be per country". Its
    // nation is the build menu picked below; once added, the Nations tab's board moves it like any unit)
    const start = el("select", { title: p.built ? w.tip_eras_horse_start : w.tip_eras_start_from, disabled: Boolean(p.built) });
    start.setAttribute("aria-label", w.eras_start_from);
    const groups = [[w.eras_suggested, p.start.filter((s) => s.suggested)],
      [w.eras_start_same, p.start.filter((s) => !s.suggested && s.same_type)],
      [w.eras_start_other, p.start.filter((s) => !s.suggested && !s.same_type)]];
    for (const [label, list] of groups) {
      if (!list.length) continue;
      const g = el("optgroup", { label });
      g.append(...list.map((s) => el("option", { value: s.address,
        textContent: `${s.name} · ${state.nationNames[s.nation] || s.nation}` })));
      start.append(g);
    }
    const price = el("input", { type: "number", min: "0", step: "1", inputMode: "numeric", required: true,
      value: String(p.price), title: w.tip_eras_price });
    price.setAttribute("aria-label", w.price);

    // its size (only with a model of its own: without one it shows the start unit's model)
    const size = el("input", { type: "number", min: "0.05", max: "20", step: "any", inputMode: "decimal", required: true,
      title: w.tip_eras_size });
    size.setAttribute("aria-label", w.eras_size);
    const sizeNote = el("span");
    const sizeSlide = el("div");  // the slider with its points (app.js sizeSlider): Tiny, Game size, Real life, Huge
    let exact = null;  // the size suggested, as the Studio worked it out (the box shows it rounded)
    const showSize = (value, info) => {
      exact = value;
      size.value = round3(value);
      const startName = start.selectedOptions[0] ? start.selectedOptions[0].textContent.split(" · ")[0] : "";
      sizeSlide.replaceChildren(sizeSlider(size, { tiny: 0.05, huge: 20, game: 1, start: startName,
        real: info.real ? Math.min(20, Math.max(0.05, info.clamped === null ? value : info.clamped)) : null }));
      const real = info.real ? fill(info.what === "span" ? w.eras_size_real_span : w.eras_size_real_width, { m: info.real_m }) : "";
      sizeNote.textContent = info.real
        ? (info.clamped === null ? real : `${real} ${fill(w.eras_size_clamped, { raw: round3(info.clamped), size: round3(value) })}`)
        : ["no_real", "no_scale"].includes(info.why) ? w.eras_size_unknown : info.why === "no_model" ? "" : w.eras_size_unread;
    };

    const nation = el("select", { title: w.tip_eras_nation }), factory = el("select", { title: w.tip_eras_factory });
    nation.setAttribute("aria-label", w.nation);
    factory.setAttribute("aria-label", w.factory);
    let menus = { nations: [] };
    try { menus = await api().menus(state.lang); } catch (err) { problem(err); }
    const first = p.game_nation ?? (menus.nations[0] ? menus.nations[0].nation : 0);
    nation.append(...menus.nations.map((n) => el("option", { value: String(n.nation), textContent: n.name, selected: n.nation === first })));
    const fillF = () => {
      const n = menus.nations.find((x) => x.nation === Number(nation.value));
      factory.replaceChildren(...(n ? n.factories : []).map((f) => el("option", { value: String(f.factory),
        textContent: factoryLabel(f), selected: f.factory === p.factory })));
    };
    fillF();

    // its group: the row of the building's build list it goes in (era_unit_start's "group", groups.py; the owner,
    // 2026-10-31: at most 6 units to a group, a 7th refused; 11-01: at most 10 groups to a building), one of the
    // building's groups or a group of its own; while that has no room, or while one is to be picked ("pick": a unit with
    // no card type, the owner's pick 11-01), Add to my mod is off and says why
    const groupPick = el("select", { title: w.tip_eras_group });
    groupPick.setAttribute("aria-label", w.eras_group);
    const groupBox = el("label", {}, el("span", { textContent: w.eras_group }), groupPick);
    const goesIn = el("p", { className: "small" });
    const groupWhy = el("p", { className: "notice warn small hidden" });
    const addTip = p.built ? w.tip_eras_horse_add : w.tip_eras_add;
    const add = el("button", { type: "submit", className: "primary", textContent: w.eras_add, title: addTip });
    const horseStatus = el("p", { className: "small muted" });  // the Horse Squad's steps while it's made (followHorse)
    if (p.built) {
      add.dataset.horseAdd = "1";
      horseStatus.dataset.horseStatus = "1";
    }
    let offer = null, groupPicked = false;  // the group shown; whether the modder picked it
    const buildingOf = () => w[BUILDING_WORD[Number(factory.value)]]
      || (factory.selectedOptions[0] ? factory.selectedOptions[0].textContent : "");
    const showGroup = (g) => {  // null: a build menu that isn't one of the board's buildings (no groups)
      offer = g || null;
      groupBox.classList.toggle("hidden", !offer);
      goesIn.classList.toggle("hidden", !offer);
      let why = "";
      if (offer) {
        const own = offer.root === null, pick = Boolean(offer.pick);
        const values = { building: buildingOf(), name: offer.name, n: offer.count, most: offer.most,
          groups: offer.groups, most_groups: offer.most_groups };
        groupPick.title = fill(w.tip_eras_group, values);
        groupPick.replaceChildren(...(pick ? [el("option", { value: "", textContent: w.eras_group_pick, disabled: true })] : []),
          ...offer.choices.map((c) => el("option", { value: c.root,
            textContent: fill(c.full ? w.eras_group_choice_full : w.eras_group_choice, { name: c.name, n: c.count,
              most: offer.most }) })),
          el("option", { value: NEW_GROUP,
            textContent: fill(offer.groups >= offer.most_groups ? w.eras_group_own_full : w.eras_group_own, values) }));
        groupPick.value = pick ? "" : own ? NEW_GROUP : offer.root;
        goesIn.textContent = pick ? "" : fill(own ? w.eras_goes_in_own : w.eras_goes_in, values);
        goesIn.classList.toggle("hidden", pick);
        if (pick) why = w.eras_group_pick_why;
        else if (offer.full) why = fill(own ? w.eras_group_own_full_why : w.eras_group_full_why, values);
      }
      groupWhy.textContent = why;
      groupWhy.classList.toggle("hidden", !why);
      add.disabled = Boolean(why) || Boolean(p.built && horseJob);  // (the Horse Squad: off while it's being made)
      add.title = why || addTip;
    };

    // researched from: the build menu's units, or none (buyable from the start), with its research price and time
    const research = el("select", { title: w.tip_eras_research_from });
    research.setAttribute("aria-label", w.eras_research_from);
    const researchNote = el("p", { className: "muted small" });
    const rPrice = el("input", { type: "number", min: "0", step: "1", inputMode: "numeric", required: true, value: "50",
      title: w.tip_eras_research_price });
    rPrice.setAttribute("aria-label", w.eras_research_price);
    const rTime = el("input", { type: "number", min: "0", step: "1", inputMode: "numeric", required: true,
      value: timeShown(50, timeUnit()), title: w.tip_eras_research_time });  // 50 seconds, in the unit picked
    rTime.setAttribute("aria-label", w.eras_research_time);
    const rUnit = timeUnitPicker(rTime);  // seconds or minutes (app.js): the game keeps whole seconds
    let picked = false;  // the modder picked one: kept while the build menu still offers it
    const lockCosts = () => {  // nothing to research: its price and time are locked, and say why
      for (const [box, tip] of [[rPrice, w.tip_eras_research_price], [rTime, w.tip_eras_research_time],
        [rUnit, w.tip_research_time_unit]]) {
        box.disabled = !research.value;
        box.title = research.value ? tip : research.disabled ? w.tip_eras_research_off : w.tip_eras_research_locked;
      }
    };
    const showResearch = (r) => {
      const kept = picked && (research.value === "" || r.choices.some((c) => c.address === research.value))
        ? research.value : null;
      const want = kept ?? (r.suggested || "");
      research.replaceChildren(el("option", { value: "", textContent: w.eras_research_none, selected: want === "" }),
        ...r.choices.map((c) => el("option", { value: c.address, textContent: c.name, selected: c.address === want })));
      research.value = want;
      research.disabled = !r.offered;
      research.title = r.offered ? w.tip_eras_research_from : w.tip_eras_research_off;
      researchNote.textContent = !r.offered ? w.tip_eras_research_off
        : r.suggested && want === r.suggested && WHY[r.why] ? w[WHY[r.why]] : "";
      lockCosts();
    };
    research.addEventListener("change", () => { picked = true; researchNote.textContent = ""; lockCosts(); });

    // another start unit, build menu or group: its price, size, group and research asked for again (the last asked
    // wins); another build menu has groups of its own, so its group is the one of its kind again
    let asked = 0;
    const again = async (newStart) => {
      const n = ++asked;
      let o;
      try {
        o = await api().era_unit_start(p.key, start.value, Number(nation.value), Number(factory.value), state.lang,
          groupPicked && offer ? groupPick.value : null);
      } catch (err) { problem(err); return; }
      if (n !== asked) return;
      if (newStart) {
        price.value = String(o.price);
        showSize(o.size, o.size_info);
      }
      showGroup(o.group);
      showResearch(o.research);
    };
    start.addEventListener("change", () => again(true));
    nation.addEventListener("change", () => { fillF(); groupPicked = false; again(false); });
    factory.addEventListener("change", () => { groupPicked = false; again(false); });
    groupPick.addEventListener("change", () => { groupPicked = true; again(false); });
    showSize(p.size, p.size_info);
    showGroup(p.group);
    showResearch(p.research);
    if (Number(nation.value) !== p.game_nation || Number(factory.value) !== p.factory) again(false);  // not the page's menu

    form.append(
      el("label", {}, el("span", { textContent: w.new_unit_name }), name),
      el("label", {}, el("span", { textContent: w.eras_start_from }), start),
      el("p", { className: "muted small", textContent: p.built ? w.eras_horse_start_help : w.eras_start_help }),
      el("label", {}, el("span", { textContent: w.price }), price),
      ...(p.has_model ? [el("label", {}, el("span", { textContent: w.eras_size }), size), sizeSlide,
        el("p", { className: "muted small" }, `${w.eras_size_help} `, sizeNote)] : []),
      el("div", { className: "menu-picks" }, el("span", { textContent: w.build_menu }),
        el("label", {}, el("span", { textContent: w.nation }), nation),
        el("label", {}, el("span", { textContent: w.factory }), factory)),
      groupBox, goesIn, groupWhy,
      el("label", {}, el("span", { textContent: w.eras_research_from }), research),
      researchNote,
      el("div", { className: "menu-picks" },
        el("label", {}, el("span", { textContent: w.eras_research_price }), rPrice),
        el("label", {}, el("span", { textContent: w.eras_research_time }), rTime), rUnit),
      el("div", { className: "actions" }, add), ...(p.built ? [horseStatus] : []));
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const cost = Number(price.value);
      const sized = size.value === round3(exact) ? exact : Number(size.value);
      const from = research.value || null, rp = Number(rPrice.value);
      const rt = timeSeconds(rTime.value.trim() === "" ? NaN : Number(rTime.value), rUnit.value);  // whole seconds
      if (!name.value.trim() || !Number.isFinite(cost) || (p.has_model && !Number.isFinite(sized))) return;
      if (from && (!Number.isFinite(rp) || !Number.isFinite(rt))) return;
      if (offer && (offer.full || offer.pick)) return;  // no room in its group, or none picked (Add is off, saying why)
      add.disabled = true;
      if (p.built) {  // the Horse Squad: its horses and riders made from the modder's own game first, a job followed
        try {
          const res = await api().horse_squad_add(Number(nation.value), Number(factory.value), name.value.trim(), cost,
            from, from ? rp : null, from ? rt : null, offer ? groupPick.value : null);
          if (!horseJob || horseJob.id !== res.job) horseJob = { id: res.job, began: Date.now() };
          followHorse();
        } catch (err) {
          problem(err);
          add.disabled = Boolean(offer && (offer.full || offer.pick));
          await moveFix();  // (its folder too deep for Windows: the quick fix beside the words)
        }
        return;
      }
      try {
        const res = await api().era_unit_add(p.key, Number(nation.value), Number(factory.value), start.value,
          name.value.trim(), cost, p.has_model ? sized : null, from, from ? rp : null, from ? rt : null,
          offer ? groupPick.value : null);  // the group shown (null: a build menu that isn't one of the board's)
        say(fill(w.eras_added, { name: res.name }), "ok");
        if (res.model_note === "no_fit") say(w.eras_no_fit, "warn");
        else if (res.model_note && res.model_note !== "no_model") say(res.model_note, "warn");
        await openMade(res.address);
      } catch (err) { problem(err); add.disabled = Boolean(offer && (offer.full || offer.pick)); }
    });
    return form;
  }

  window.EraUnits = { renderChips: renderEraChips, refreshList: refreshEraList, showPage: showEraPage, CHINA };
  if ($("eras") && state.words && state.words.era_vanilla) renderEraChips();  // the page started before this file came
})();
