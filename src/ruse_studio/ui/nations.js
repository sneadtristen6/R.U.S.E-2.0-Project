// The Nations tab (StudioApi.nations_view / nation_flag_set / nation_reset, rusemod.nations): one of the game's seven
// nations given a new name and flag in the current mod, China in Italy's place say (the owner, 2026-10-08: "build the
// replace-a-nation feature for this patch"). Its name in the lobby and its army's name are changed in every language
// with All values' words box (app.js wordsPanel); its flag is a picture of the modder's (any picture the window can
// read: PNG, JPG, WebP...) fitted here to the flag's size, shone like the game's flags, its round shape kept the game's.
// Its units: the Units tab with that nation picked (New unit puts a unit in its build menus); what they say: each
// unit's page (Voice). Seen in the game (2026-10-08, Italy made China). Uses app.js's $, el, fill, say, problem, api,
// state, wordsPanel,
// showView, renderChips and refreshList.
(function () {
  "use strict";
  const N = { words: {}, lang: "base", data: null, open: null,
    flow: false, empty: new Set() };  // a new mod's Nations step (startflow.js): each nation kept or started empty
  const W = () => N.words;
  // the era library's eras and nations, by the Units tab's words for them (eraunits.js)
  const ERA_WORD = { WWI: "eras_era_ww1", WWII: "eras_era_ww2", "Cold War": "eras_era_cold", Modern: "eras_era_modern" };
  const NATION_WORD = { USA: "eras_nation_usa", Germany: "eras_nation_germany", UK: "eras_nation_uk",
    France: "eras_nation_france", Italy: "eras_nation_italy", USSR: "eras_nation_ussr", Russia: "eras_nation_russia",
    Japan: "eras_nation_japan", China: "eras_nation_china" };

  // the words for nation x in the Studio's language (the game's code names: English), the mod's when it has its own
  function inLang(list) {
    const lang = N.lang === "base" ? "us" : N.lang;
    const x = (list || []).find((y) => y.lang === lang) || (list || []).find((y) => y.lang === "us") || {};
    return { now: x.mine ?? x.game ?? "", game: x.game ?? "", mine: x.mine !== null && x.mine !== undefined && x.mine !== x.game };
  }

  async function render() {
    const w = W();
    $("nations-title").textContent = w.nations_title;
    $("nations-help").textContent = w.nations_help;
    $("nations-lobby").textContent = w.nations_lobby_note;
    let data;
    try { data = await api().nations_view(); } catch (err) { problem(err); return; }
    if (!$("nations-view") || $("nations-view").classList.contains("hidden")) return;  // another tab meanwhile
    N.data = data;
    $("nations-nomod").textContent = data.mod ? "" : w.no_mod;
    $("nations-nomod").classList.toggle("hidden", data.mod);
    $("nations-list").replaceChildren(...data.nations.map(card));
  }

  function flagImage(url, label, big) {
    const img = el("img", { src: url, alt: label, title: label, className: big ? "nation-flag big" : "nation-flag" });
    img.width = img.height = big ? 84 : 42;
    return img;
  }

  function card(x) {
    const w = W(), name = inLang(x.name), army = x.army ? inLang(x.army) : null;
    const changed = name.mine || (army && army.mine) || (x.flag && x.flag.own);
    const head = el("div", { className: "nation-head" },
      x.flag ? flagImage(x.flag.url, fill(w.nations_flag_of, { nation: name.now }), false) : el("span", { className: "nation-flag" }),
      el("div", { className: "nation-names" },
        el("strong", { textContent: name.now }),
        ...(name.mine ? [el("span", { className: "muted small", textContent: " " + fill(w.nations_was, { nation: name.game }) })] : []),
        ...(army ? [el("div", { className: "muted small", textContent: army.now })] : []),
        el("div", { className: "muted small", textContent: fill(w.nations_units_count, { n: x.units }) })));
    const toggle = el("button", { type: "button", className: "small", textContent: N.open === x.nation ? w.nations_close : w.nations_change,
      title: fill(w.tip_nations_change, { nation: name.now }) });
    toggle.addEventListener("click", () => { N.open = N.open === x.nation ? null : x.nation; render(); });
    if (N.flow) head.append(keepOrEmpty(x, name));
    head.append(toggle);
    const box = el("div", { className: "nation" + (changed ? " changed" : "") }, head);
    if (N.open === x.nation) box.append(details(x, name));
    return box;
  }

  // A new mod's Nations step: Keep its units (its build menus as in the game) or Start it empty (all its units out of
  // them, as Hide all does: StudioApi.nation_units_hide), beside its name and flag
  function keepOrEmpty(x, name) {
    const w = W(), group = el("span", { className: "flow-keep", role: "radiogroup" });
    for (const [key, word, tip] of [["keep", "flow_keep", "tip_flow_keep"], ["empty", "flow_empty", "tip_flow_empty"]]) {
      const r = el("input", { type: "radio", name: `flow-keep-${x.nation}`, value: key,
        checked: (key === "empty") === N.empty.has(x.nation), title: fill(w[tip], { nation: name.now }) });
      r.addEventListener("change", async () => {
        const empty = key === "empty";
        let res;
        try { res = await api().nation_units_hide(x.nation, empty, N.lang); } catch (err) { problem(err); render(); return; }
        if (empty) N.empty.add(x.nation); else N.empty.delete(x.nation);
        say(fill(empty ? w.nations_units_hidden : w.nations_units_shown, { nation: name.now })
          + (res && res.unlinked && res.unlinked.length ? " " + fill(w.nations_units_unlinked, { list: res.unlinked.join(", ") }) : ""), "ok");
      });
      group.append(el("label", { className: "small", title: fill(w[tip], { nation: name.now }) }, r, " " + w[word]));
    }
    return group;
  }

  // Its buildings and their units (board.js): each building a row like its build menu in the game
  function boardBlock(x, name) {
    const w = W(), holder = el("div", { className: "board" });
    window.BoardView.mount(holder, x.nation, name.now);
    return [el("h3", { textContent: w.board_head, title: w.tip_board_head }),
      el("p", { className: "muted small", textContent: fill(w.board_help, { nation: name.now }) }), holder];
  }

  function details(x, name) {
    const w = W(), has = Boolean(N.data && N.data.mod);
    const parts = [];
    if (window.BoardView) parts.push(...boardBlock(x, name));
    parts.push(el("h3", { textContent: w.nations_name_head, title: w.tip_nations_name_head }),
      el("p", { className: "muted small", textContent: w.nations_name_help }), wordsPanel(x.name_key, render));
    if (x.army_key) {
      parts.push(el("h3", { textContent: w.nations_army_head, title: w.tip_nations_army_head }),
        el("p", { className: "muted small", textContent: w.nations_army_help }), wordsPanel(x.army_key, render));
    }
    // the flag: the game's and the mod's side by side, a picture chosen and fitted here, or the game's back
    parts.push(el("h3", { textContent: w.nations_flag_head, title: w.tip_nations_flag_head }),
      el("p", { className: "muted small", textContent: w.nations_flag_help }));
    if (x.flag) {
      const pics = el("div", { className: "nation-flags" },
        el("figure", {}, flagImage(x.flag.game_url, w.nations_flag_game, true), el("figcaption", { className: "small muted", textContent: w.nations_flag_game })),
        ...(x.flag.own ? [el("figure", {}, flagImage(x.flag.url, w.nations_flag_mine, true), el("figcaption", { className: "small muted", textContent: w.nations_flag_mine }))] : []));
      const input = el("input", { type: "file", accept: "image/*" });
      input.hidden = true;
      const shine = el("input", { type: "checkbox", checked: true, title: w.tip_nations_shine });
      const pick = el("button", { type: "button", className: "small primary", textContent: w.nations_flag_pick,
        title: w.tip_nations_flag_pick, disabled: !has });
      pick.addEventListener("click", () => input.click());
      input.addEventListener("change", () => { const f = input.files[0]; input.value = ""; if (f) useFlag(x, f, shine.checked); });
      const back = el("button", { type: "button", className: "small ghost", textContent: w.nations_flag_back,
        title: w.tip_nations_flag_back, disabled: !has || !x.flag.own });
      back.addEventListener("click", async () => {
        try { await api().nation_reset(x.nation, "flag"); } catch (err) { problem(err); return; }
        say(fill(w.nations_flag_backed, { nation: name.now }), "ok");
        render();
      });
      // a picture dropped on the flags works as the button does
      pics.addEventListener("dragover", (e) => { if (has) e.preventDefault(); });
      pics.addEventListener("drop", (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (has && f) useFlag(x, f, shine.checked); });
      parts.push(pics, el("div", { className: "actions" }, pick, back,
        el("label", { className: "small", title: w.tip_nations_shine }, shine, " " + w.nations_shine)), input);
    } else {
      parts.push(el("p", { className: "muted small", textContent: w.nations_flag_none }));
    }
    // its units and what they say: where they're always changed
    const units = el("button", { type: "button", className: "small", textContent: fill(w.nations_units, { nation: name.now }),
      title: w.tip_nations_units });
    units.addEventListener("click", () => {
      state.nation = x.nation;
      showView("units");
      renderChips();
      refreshList();
    });
    parts.push(el("h3", { textContent: w.nations_units_head, title: w.tip_nations_units }),
      el("p", { className: "muted small", textContent: w.nations_units_help }), el("div", { className: "actions" }, units),
      unitsBlock(x, name));
    const all = el("button", { type: "button", className: "small ghost", textContent: w.nations_reset,
      title: w.tip_nations_reset, disabled: !has });
    all.addEventListener("click", async () => {
      try { await api().nation_reset(x.nation, "all"); } catch (err) { problem(err); return; }
      say(fill(w.nations_reset_done, { nation: name.game }), "ok");
      render();
    });
    parts.push(el("div", { className: "actions nation-reset" }, all));
    return el("div", { className: "nation-details" }, ...parts);
  }

  // All of a nation's units at once (StudioApi.nation_units / nation_units_hide / nation_fill_list / nation_fill; the
  // owner, 2026-10-10: "say someone wanted to take out Italy and put China in, how are they gonna remove all of
  // Italy's units and then put in Chinese units?"): its own units hidden from its build menus in one click, or shown
  // again; its menus filled from an era's units of another nation: one list, every unit ticked with its building
  // picked (his pick), the modder unticks any and presses Add, which runs as a job.
  function unitsBlock(x, name) {
    const w = W(), box = el("div", { className: "nation-units" });
    const fillBox = el("div", { className: "nation-fill" });
    const draw = async () => {
      let data;
      try { data = await api().nation_units(x.nation, N.lang); } catch (err) { problem(err); return; }
      const count = el("p", { className: "small", textContent: fill(w.nations_units_menus, { n: data.units.length,
        nation: name.now, hidden: data.hidden }) });
      const hide = el("button", { type: "button", className: "small", textContent: fill(w.nations_units_hide, { nation: name.now }),
        title: w.tip_nations_units_hide, disabled: !data.can || data.hidden === data.units.length });
      const show = el("button", { type: "button", className: "small ghost", textContent: w.nations_units_show,
        title: w.tip_nations_units_show, disabled: !data.can || !data.hidden });
      const set = async (on) => {
        let res;
        try { res = await api().nation_units_hide(x.nation, on, N.lang); } catch (err) { problem(err); return; }
        // the units researched from one now hidden: made buyable from the start (the game stops otherwise)
        say(fill(on ? w.nations_units_hidden : w.nations_units_shown, { nation: name.now })
          + (res && res.unlinked && res.unlinked.length ? " " + fill(w.nations_units_unlinked, { list: res.unlinked.join(", ") }) : ""), "ok");
        draw();
      };
      hide.addEventListener("click", () => set(true));
      show.addEventListener("click", () => set(false));
      // a building left with nothing to build (its own units all hidden, none of the mod's put in): the game shows the
      // building's construction menu when it's picked (seen 2026-10-10, Italy's artillery and anti-tank bases), so
      // it's said here with a way to give it its own units back
      const empty = (data.empty || []).map((f) => {
        const where = w["group_" + FACTORY_GROUP[f]] || String(f);
        const back = el("button", { type: "button", className: "small", textContent: fill(w.nations_empty_back, { nation: name.now }),
          title: fill(w.tip_nations_empty_back, { nation: name.now, building: where }), disabled: !data.can });
        back.addEventListener("click", async () => {
          try { await api().nation_units_hide(x.nation, false, N.lang, f); } catch (err) { problem(err); return; }
          say(fill(w.nations_empty_shown, { nation: name.now, building: where }), "ok");
          draw();
        });
        return el("li", {}, el("strong", { textContent: where }), " ", back);
      });
      const emptyBox = empty.length ? [el("div", { className: "notice warn nation-empty" },
        el("p", { className: "small", textContent: fill(w.nations_empty, { nation: name.now }) }),
        el("ul", { className: "small" }, ...empty))] : [];
      // fill from an era: the eras downloaded, each with the nations it has units of
      const era = el("select", { className: "small", title: w.tip_nations_fill });
      const from = el("select", { className: "small", title: w.tip_nations_fill });
      era.append(...data.eras.map((e) => el("option", { value: e.era, textContent: w[ERA_WORD[e.era]] || e.era })));
      const fillFrom = () => {
        const e = data.eras.find((y) => y.era === era.value);
        from.replaceChildren(...(e ? e.nations : []).map((n) => el("option", { value: n, textContent: w[NATION_WORD[n]] || n, selected: n === "China" })));
      };
      fillFrom();
      era.addEventListener("change", fillFrom);
      const list = el("button", { type: "button", className: "small", textContent: w.nations_fill_list,
        title: w.tip_nations_fill, disabled: !data.can || !data.eras.length });
      list.addEventListener("click", () => fillList(x, name, era.value, from.value, fillBox, "", draw));
      box.replaceChildren(el("h3", { textContent: w.nations_its_units, title: w.tip_nations_units_hide }), count,
        el("div", { className: "actions" }, hide, show),
        el("p", { className: "muted small", textContent: w.nations_units_hide_note }), ...emptyBox,
        el("h3", { textContent: fill(w.nations_fill_head, { nation: name.now }), title: w.tip_nations_fill }),
        el("p", { className: "muted small", textContent: data.eras.length ? w.nations_fill_help : w.nations_fill_no_eras }),
        el("div", { className: "actions" }, era, from, list), fillBox);
    };
    draw();
    return box;
  }

  // A build menu by its building, as the Units tab groups units (StudioApi.FACTORY_GROUPS), with two of its units
  const FACTORY_GROUP = { 8: "barracks", 10: "armor", 11: "antitank", 13: "artillery", 12: "prototype", 9: "airfield", 3: "turret" };
  function buildingLabel(m) {
    const w = W(), group = w["group_" + FACTORY_GROUP[m.factory]];
    return group ? `${group} (${m.units.slice(0, 2).join(", ")}…)` : factoryLabel(m);
  }

  // The list a fill would add: each unit ticked (one already in the mod: not offered again), its building picked.
  async function fillList(x, name, era, from, box, said = "", changed = null) {
    const w = W();
    let data;
    try { data = await api().nation_fill_list(x.nation, era, from, N.lang); } catch (err) { problem(err); return; }
    const rows = data.units.map((u) => {
      const tick = el("input", { type: "checkbox", checked: !u.added && u.factory !== null, disabled: u.added,
        title: w.tip_nations_fill_tick });
      const where = el("select", { className: "small", title: w.tip_nations_fill_building, disabled: u.added },
        ...data.menus.map((m) => el("option", { value: String(m.factory), textContent: buildingLabel(m), selected: m.factory === u.factory })));
      if (u.factory === null) where.value = "";
      where.addEventListener("change", () => { tick.checked = true; });
      return { u, tick, where, row: el("tr", {}, el("td", {}, tick),
        el("td", {}, el("strong", { textContent: u.name }), el("div", { className: "muted small", textContent: u.card })),
        el("td", {}, u.added ? el("span", { className: "muted small", textContent: w.nations_fill_added }) : where)) };
    });
    const add = el("button", { type: "button", className: "small primary", textContent: w.nations_fill_add,
      title: fill(w.tip_nations_fill_add, { nation: name.now }) });
    const note = el("p", { className: "small", role: "status", textContent: said });  // (the last Add's outcome)
    add.addEventListener("click", async () => {
      const picks = rows.filter((r) => r.tick.checked && !r.u.added && r.where.value !== "")
        .map((r) => ({ key: r.u.key, factory: Number(r.where.value) }));
      if (!picks.length) { note.textContent = w.nations_fill_none; return; }
      add.disabled = true;
      let job;
      try { job = await api().nation_fill(x.nation, picks); } catch (err) { add.disabled = false; problem(err); return; }
      let seen = 0;
      const added = [], skipped = [];
      for (;;) {
        let st;
        try { st = await api().job(job.job, seen); } catch (err) { problem(err); break; }
        seen = st.count;
        for (const line of st.lines) {
          const [what, unit, why] = line.split("\t");
          if (what === "added") added.push(unit); else if (what === "skipped") skipped.push(`${unit}: ${why}`);
        }
        note.textContent = fill(w.nations_fill_progress, { done: added.length + skipped.length, all: picks.length });
        if (st.state !== "running") break;
        await new Promise((ok) => setTimeout(ok, 700));
      }
      note.textContent = fill(w.nations_fill_done, { n: added.length, nation: name.now })
        + (skipped.length ? " " + fill(w.nations_fill_skipped, { list: skipped.join(" · ") }) : "");
      say(note.textContent, skipped.length ? "" : "ok");
      fillList(x, name, era, from, box, note.textContent, changed);
      if (changed) changed();  // (the buildings left empty, asked again)
    });
    box.replaceChildren(
      rows.length ? el("table", { className: "nation-fill-list" }, ...rows.map((r) => r.row))
        : el("p", { className: "muted small", textContent: w.nations_fill_empty }),
      ...(rows.some((r) => !r.u.added) ? [el("div", { className: "actions" }, add)] : []), note);
  }

  // a picture of the modder's as the nation's flag: fitted to the flag's size (filling it, centred), shone like the
  // game's flags (their top half lighter, their bottom half darker); the round shape is the game's (the build keeps
  // the flag's own alpha), so nothing outside the circle shows
  async function useFlag(x, file, shine) {
    const w = W(), fw = x.flag.width, fh = x.flag.height;
    let bitmap;
    try { bitmap = await createImageBitmap(file); } catch (err) { problem(new Error(w.nations_flag_unreadable)); return; }
    const canvas = document.createElement("canvas");
    canvas.width = fw; canvas.height = fh;
    const g = canvas.getContext("2d");
    const scale = Math.max(fw / bitmap.width, fh / bitmap.height);
    const dw = bitmap.width * scale, dh = bitmap.height * scale;
    g.imageSmoothingQuality = "high";
    g.drawImage(bitmap, (fw - dw) / 2, (fh - dh) / 2, dw, dh);
    // the game flag's own shape (its alpha), so the picture shown here is the one the game will show (the build keeps
    // the game's alpha whatever this picture's is)
    let shape = null;
    try {
      const game = await new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = x.flag.game_url; });
      const s = document.createElement("canvas");
      s.width = fw; s.height = fh;
      const sg = s.getContext("2d");
      sg.drawImage(game, 0, 0, fw, fh);
      shape = sg.getImageData(0, 0, fw, fh).data;
    } catch { /* the game's flag couldn't be drawn here: the picture is saved square, the build still cuts it */ }
    const img = g.getImageData(0, 0, fw, fh), d = img.data;
    for (let y = 0; y < fh; y++) {
      const top = y < fh / 2, t = top ? 0.22 * (1 - y / (fh / 2)) : 0;
      for (let xx = 0; xx < fw; xx++) {
        const i = (y * fw + xx) * 4;
        if (shine) for (let c = 0; c < 3; c++) d[i + c] = top ? d[i + c] + (255 - d[i + c]) * t : d[i + c] * 0.78;
        d[i + 3] = shape ? shape[i + 3] : 255;
      }
    }
    g.putImageData(img, 0, 0);
    try { await api().nation_flag_set(x.nation, canvas.toDataURL("image/png")); } catch (err) { problem(err); return; }
    say(fill(w.nations_flag_saved, { nation: inLang(x.name).now }), "ok");
    render();
  }

  window.NationsView = {
    open(words, lang) { N.words = words; N.lang = lang; render(); },
    setWords(words, lang) { N.words = words; N.lang = lang; render(); },
    modChanged() { N.empty.clear(); render(); },
    setFlow(on) { N.flow = Boolean(on); if (!$("nations-view").classList.contains("hidden")) render(); },
    // a unit's page in the Units tab, "Show on the board": its nation opened, its building's row brought into sight
    async openNation(n, factory) {
      N.open = n;
      showView("nations");  // (drawn once: two at once would race for the same flag pictures)
      for (let tries = 0; tries < 60; tries++) {  // (the board reads the build menus after the page is drawn)
        const line = $("nations-list").querySelector(`.board-line[data-factory="${factory}"]`);
        if (line) { line.closest(".board-row").scrollIntoView({ block: "start", behavior: "smooth" }); return; }
        await new Promise((ok) => setTimeout(ok, 150));
      }
    },
  };
})();
