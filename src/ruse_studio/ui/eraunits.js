// Era units in the Units tab (StudioApi.era_units_list / era_unit_page / era_unit_add / era_unit_remove,
// ruse_studio.era_units): the era filter above the kinds picks Vanilla (the game's own units, the list as always) or an
// era (WWI, WWII+, Cold War, Modern: RUSE 2.0's units, each another maker's free model, credited, fitted and marked).
// An era's units are listed and filtered like the game's (kind, nation, type, search); none is in the mod until added
// (the owner, 2026-10-08). An era unit's page shows its model's picture and credit, and adds it to the mod: it starts
// from the values of any game unit of its kind (the library's suggestion first; the owner: "what if they don't want to
// make it the same as a Sherman?"), with the name, price and build menu given; then it's a new unit like any other,
// its page open to change every value. Uses app.js's $, el, fill, say, problem, api, state, renderChips, refreshList,
// renderGroups, showUnit and factoryLabel.
(function () {
  "use strict";
  const ERAS = [["vanilla", "era_vanilla"], ["WWI", "eras_era_ww1"], ["WWII", "eras_era_ww2"],
    ["Cold War", "eras_era_cold"], ["Modern", "eras_era_modern"]];
  const NATION_WORD = { USA: "eras_nation_usa", Germany: "eras_nation_germany", UK: "eras_nation_uk",
    France: "eras_nation_france", Italy: "eras_nation_italy", USSR: "eras_nation_ussr", Russia: "eras_nation_russia",
    Japan: "eras_nation_japan", China: "eras_nation_china" };
  const CHINA = 7;  // the nation chip for China, which has no game nation of its own
  const W = () => state.words;
  const nationOf = (n) => W()[NATION_WORD[n]] || n;
  const eraOf = (era) => W()[(ERAS.find(([k]) => k === era) || [])[1]] || era;

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
  }

  async function refreshEraList() {
    const w = W();
    let res;
    try {
      res = await api().era_units_list(state.era, state.kind, state.nation, state.search, state.group || "all");
    } catch (err) { problem(err); return; }
    if (!res.library) {
      $("era-note").textContent = w.eras_no_library;
      $("era-note").classList.remove("hidden");
    }
    $("count").textContent = w.units.replace("{n}", res.units.length);
    renderGroups([], res.types || []);
    $("unit-list").replaceChildren(...res.units.map((u) => {
      const b = el("button", { type: "button", title: w.tip_open_unit },
        el("span", { className: "name", textContent: u.name }),
        el("span", { className: "sub", textContent: `${nationOf(u.nation)} · ${u.card}` +
          (u.added ? ` · ${w.eras_in_mod_badge}` : "") }));
      b.dataset.address = "era:" + u.key;
      if (u.added) b.prepend(el("span", { className: "badge new", textContent: state.words.new_mark }));
      b.setAttribute("aria-current", String(state.selected === "era:" + u.key));
      b.addEventListener("click", () => showEraPage(u.key));
      return el("li", {}, b);
    }));
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
    const facts = [eraOf(p.era), nationOf(p.nation), p.card];
    if (p.in_place_of) facts.push(fill(w.eras_in_place_of, { name: p.in_place_of }));
    const c = p.credit || {};
    const credit = el("p", { className: "small" },
      el("span", { textContent: fill(w.eras_model_by, { author: c.author || "", licence: c.licence || "" }) + " " }),
      el("a", { href: c.url || "#", target: "_blank", rel: "noopener", textContent: c.title || "", title: w.tip_eras_credit }),
      ...(c.extra ? [el("span", { textContent: ` · ${c.extra}` })] : []));
    const parts = [el("h1", { textContent: p.name }), el("p", { className: "unit-desc", textContent: facts.join(" · ") })];
    if (p.picture) parts.push(el("img", { src: p.picture, alt: p.name, className: "era-picture" }));
    parts.push(credit);
    if (!p.has_model) parts.push(el("p", { className: "notice warn", textContent: w.eras_game_model }));
    else if (!p.fits) parts.push(el("p", { className: "notice warn", textContent: w.eras_no_fit }));
    if (!state.mod) parts.push(el("p", { className: "notice", textContent: w.no_mod }));
    else if (p.added) parts.push(addedBox(p));
    else parts.push(await addForm(p));
    $("detail").replaceChildren(...parts);
  }

  // in the mod already: to its page (every value changed there), or out of the mod again
  function addedBox(p) {
    const w = W();
    const open = el("button", { type: "button", className: "primary", textContent: w.eras_open_page, title: w.tip_eras_open_page });
    open.addEventListener("click", () => openMade(p.added));
    const out = el("button", { type: "button", className: "ghost danger", textContent: w.eras_take_out, title: w.tip_eras_take_out });
    out.addEventListener("click", async () => {
      out.disabled = true;
      try {
        await api().era_unit_remove(p.key);
        say(fill(w.eras_removed, { name: p.name }), "ok");
        await refreshList();
        await showEraPage(p.key);
      } catch (err) { problem(err); out.disabled = false; }
    });
    return el("div", { className: "notice new" }, el("p", { textContent: w.eras_in_mod_as }),
      el("div", { className: "actions" }, open, out));
  }

  async function openMade(address) {
    state.era = "vanilla";
    state.group = "all";
    if (state.nation === CHINA) state.nation = -1;
    renderChips();
    await refreshList();
    await showUnit(address);
  }

  // add it: its name, the game unit it starts from (any of its kind), its price and its build menu
  async function addForm(p) {
    const w = W();
    const form = el("form", { className: "new-unit" });
    const name = el("input", { autocomplete: "off", maxLength: 60, required: true, value: p.name, title: w.tip_eras_name });
    name.setAttribute("aria-label", w.new_unit_name);
    const start = el("select", { title: w.tip_eras_start_from });
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
    start.addEventListener("change", async () => {
      try { price.value = String((await api().era_start_price(start.value)).price); } catch (err) { problem(err); }
    });
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
    nation.addEventListener("change", fillF);
    const add = el("button", { type: "submit", className: "primary", textContent: w.eras_add, title: w.tip_eras_add });
    form.append(
      el("label", {}, el("span", { textContent: w.new_unit_name }), name),
      el("label", {}, el("span", { textContent: w.eras_start_from }), start),
      el("p", { className: "muted small", textContent: w.eras_start_help }),
      el("label", {}, el("span", { textContent: w.price }), price),
      el("div", { className: "menu-picks" }, el("span", { textContent: w.build_menu }),
        el("label", {}, el("span", { textContent: w.nation }), nation),
        el("label", {}, el("span", { textContent: w.factory }), factory)),
      el("div", { className: "actions" }, add));
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const cost = Number(price.value);
      if (!name.value.trim() || !Number.isFinite(cost)) return;
      add.disabled = true;
      try {
        const res = await api().era_unit_add(p.key, Number(nation.value), Number(factory.value), start.value,
          name.value.trim(), cost);
        say(fill(w.eras_added, { name: res.name }), "ok");
        if (res.model_note === "no_fit") say(w.eras_no_fit, "warn");
        else if (res.model_note && res.model_note !== "no_model") say(res.model_note, "warn");
        await openMade(res.address);
      } catch (err) { problem(err); add.disabled = false; }
    });
    return form;
  }

  window.EraUnits = { renderChips: renderEraChips, refreshList: refreshEraList, showPage: showEraPage, CHINA };
  if ($("eras") && state.words && state.words.era_vanilla) renderEraChips();  // the page started before this file came
})();
