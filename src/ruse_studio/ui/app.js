// The Studio screen: browse units, see one unit's values, parts and users, and change its numbers in a mod (saved at
// once in the mod's src/studio.rndf), then test it in the game. Talks to StudioApi (ruse_studio/api.py) through
// window.pywebview.api; open index.html?fake in a normal browser for made-up data.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { lang: "base", kind: "all", nation: -1, search: "", group: "all", selected: null, words: {}, languages: [],
  nationNames: [], mods: [], mod: null, edited: new Set(),
  page: null,     // the object shown: { address, via }; via = the named unit the modder came from
  mode: "own",    // a part several units share: change it for "own" (that unit only) or "shared" (all of them)
  view: "units",  // the tab: "units" or "maps" (maps.js)
  lastEdit: null };  // the last value changed this session, for Ctrl+Z: { address, prop, mode, via, label }
const KINDS = ["all", "ground", "infantry", "air", "buildings", "ammo"];  // ammo: what weapons fire (its own list)
const WHOLE = new Set(["int8", "int16", "uint16", "int32", "uint32", "int64"]);
const NEW = "\u0001new", OPEN = "\u0001open", EXPORT = "\u0001export";  // the mod menu's actions (never a folder path)

function api() { return window.pywebview.api; }

function fill(word, values) {
  return Object.entries(values || {}).reduce((s, [k, v]) => s.split(`{${k}}`).join(String(v)), word || "");
}

function el(tag, props, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props || {});
  for (const c of children) node.append(c);
  return node;
}

// The language is kept by the Studio (settings.json in the platform folder, api.set_pref): the window's own
// storage is lost every start (its address changes), and on an update or a reinstall.
async function loadLang() {
  try {
    const kept = (await api().prefs()).lang;
    if (kept) return kept;
  } catch { /* an older Studio: the window's storage */ }
  try { return localStorage.getItem("studio.lang") || "base"; } catch { return "base"; }
}

function saveLang(lang) {
  try { localStorage.setItem("studio.lang", lang); } catch { /* private window: fine */ }
  Promise.resolve().then(() => api().set_pref("lang", lang)).catch(() => {});
}

// --- the bar at the bottom: what just happened ---
function say(text, kind) {
  const bar = $("status"), w = state.words || {};
  bar.textContent = text || "";
  bar.className = "status" + (kind ? " " + kind : "");
  if (kind === "error" && text && w.report) {  // an error can go straight into a bug report (the player posts it)
    const report = el("button", { type: "button", className: "link", textContent: w.report, title: w.tip_report || "" });
    report.addEventListener("click", () => api().report_problem(text).catch(() => {}));
    bar.append(" ", report);
  }
}

function problem(err) {
  say((err && err.message) || String(err), "error");
}

// --- words ---
async function setLanguage(lang) {
  state.lang = lang;
  knownFlags = null;  // the flags' meanings are in the language
  saveLang(lang);
  state.words = await api().strings(lang);
  renderUpdate();
  state.nationNames = await api().nations(lang);
  const w = state.words;
  $("tab-units").textContent = w.units_tab;
  $("tab-maps").textContent = w.maps_tab;
  $("tab-settings").textContent = w.settings_tab;
  if (state.view === "maps" && window.MapView) window.MapView.setWords(w, lang);
  $("lang-label").textContent = w.language;
  $("mod-label").textContent = w.mod;
  $("test").textContent = w.test_in_game;
  renderCheck();
  $("new-mod-name").placeholder = w.mod_name;
  $("new-mod-create").textContent = w.create;
  $("new-mod-cancel").textContent = w.cancel;
  $("export-version-label").textContent = w.version;
  $("export-author-label").textContent = w.author;
  $("export-description-label").textContent = w.description;
  $("export-go").textContent = w.export;
  $("export-cancel").textContent = w.cancel;
  $("export-help").textContent = w.export_help;
  $("test-log-close").textContent = w.close;
  // tooltips: one sentence on every control, from words.toml (tip_*)
  const tips = { "tab-units": "tip_tab_units", "tab-maps": "tip_tab_maps", "tab-settings": "tip_tab_settings", mod: "tip_mod", test: "tip_test", lang: "tip_lang",
    "update-now": "tip_update_now", "update-info": "tip_update_info", "new-mod-create": "tip_create_mod",
    "new-mod-cancel": "tip_cancel", "export-go": "tip_export", "export-cancel": "tip_cancel", "test-log-close": "tip_close",
    "build-index": "tip_build_index", search: "tip_search" };
  for (const [id, key] of Object.entries(tips)) $(id).title = w[key] || "";
  $("lang").replaceChildren(...state.languages.map((l) =>
    el("option", { value: l.code, textContent: l.code === "base" ? w.game_names : l.name, selected: l.code === lang })));
  $("search").placeholder = w.search;
  $("no-index-text").textContent = state.oldIndex ? w.old_index : w.no_index;
  $("build-index").textContent = w.build_index;
  if ($("pick")) $("pick").textContent = w.pick_unit;  // gone once a unit is shown
  renderMods();
  renderChips();
  if ($("no-index").classList.contains("hidden")) {
    await refreshList();
    if (state.page) await showUnit(state.page.address, state.page.via);
  }
}

// --- the mod being edited ---
function renderMods() {
  const w = state.words;
  const options = [];
  if (!state.mod) options.push(el("option", { value: "", textContent: w.no_mod, disabled: true, selected: true }));
  for (const m of state.mods) options.push(el("option", { value: m.path, textContent: m.name, title: m.path,
    selected: m.path === state.mod }));
  options.push(el("option", { value: NEW, textContent: w.new_mod }), el("option", { value: OPEN, textContent: w.open_folder }),
    el("option", { value: EXPORT, textContent: w.export_mod, disabled: !state.mod }));
  $("mod").replaceChildren(...options);
  $("test").disabled = !state.mod || $("test").dataset.running === "1";
}

function useMods(res) {
  state.mods = res.mods;
  state.mod = res.current;
  renderMods();
  checkMod();
}

// --- the mod check (StudioApi.check_mod): every file of the mod read as the build reads it, as soon as the mod is
// picked and again before Test in game, so a mistake is found before the game refuses the mod. A bar under the
// header names each one; a broken map file can be set aside (renamed, never lost) with one click. ---
const fillText = (text, values) => String(text || "").replace(/\{(\w+)\}/g, (_, k) => values[k] ?? "");

async function checkMod() {
  if (!state.mod) { state.problems = []; renderCheck(); return true; }
  try {
    state.problems = (await api().check_mod()).problems || [];
  } catch (err) { problem(err); return false; }
  renderCheck();
  return !state.problems.length;
}

function renderCheck() {
  const w = state.words, bar = $("check-bar"), list = state.problems || [];
  bar.classList.toggle("hidden", !list.length);
  if (!list.length) { bar.replaceChildren(); return; }
  bar.replaceChildren(el("span", { className: "check-title", textContent: fillText(w.check_title, { n: list.length }) }),
    ...list.map((p) => {
      const row = el("div", { className: "check-row" }, el("span", { textContent: p.problem }));
      if (p.set_aside) {
        const button = el("button", { type: "button", className: "small", textContent: w.check_set_aside, title: w.tip_check_set_aside });
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            const res = await api().set_aside(p.file);
            state.problems = res.problems || [];
            renderCheck();
            say(fillText(w.check_aside_done, { file: res.kept }), "ok");
            if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();  // the map starts clean
          } catch (err) { problem(err); button.disabled = false; }
        });
        row.append(button);
      }
      if (p.rename_to) {  // a map folder named after the map's title: rename it to the pack name the build reads
        const button = el("button", { type: "button", className: "small", textContent: fillText(w.check_rename, { name: p.rename_to }),
          title: w.tip_check_rename });
        button.addEventListener("click", async () => {
          button.disabled = true;
          try {
            state.problems = (await api().rename_map_folder(p.file.split("/")[1], p.rename_to)).problems || [];
            renderCheck();
            if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();
          } catch (err) { problem(err); button.disabled = false; }
        });
        row.append(button);
      }
      return row;
    }));
}

async function modChanged() {
  state.lastEdit = null;  // the change was in the other mod
  await refreshMarks();
  if (state.page) await showUnit(state.page.address, state.page.via);
  if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();  // a map's strokes are the mod's
}

async function pickMod(e) {
  const value = e.target.value;
  renderMods();  // the menu shows the mod being edited until something else is picked
  try {
    if (value === NEW) {
      $("new-mod").classList.remove("hidden");
      $("new-mod-name").focus();
      return;
    }
    if (value === EXPORT) { await openExport(); return; }
    useMods(value === OPEN ? await api().open_mod_folder() : await api().choose_mod(value));
    await modChanged();
  } catch (err) { problem(err); }
}

async function createMod(e) {
  e.preventDefault();
  const name = $("new-mod-name").value.trim();
  if (!name) return;
  try {
    useMods(await api().new_mod(name));
    $("new-mod").classList.add("hidden");
    $("new-mod-name").value = "";
    say(`${state.words.mod}: ${state.mod}`, "ok");
    await modChanged();
  } catch (err) { problem(err); }
}

// --- the mod as one file (Export mod…): version, author and description, then the window's "save as" dialog
async function openExport() {
  const info = await api().mod_info();
  $("export-version").value = info.version || "0.1.0";
  $("export-author").value = info.author || "";
  $("export-description").value = info.description || "";
  $("export-mod").classList.remove("hidden");
  $("export-version").focus();
}

async function exportMod(e) {
  e.preventDefault();
  const version = $("export-version").value.trim();
  if (!version) return;
  try {
    const { job } = await api().export_mod(version, $("export-author").value.trim(), $("export-description").value.trim());
    if (!job) return;  // the dialog was cancelled
    $("export-mod").classList.add("hidden");
    const log = $("test-log");
    log.textContent = "";
    $("test-panel").classList.remove("hidden");
    follow(job, log, (ok, message) => { if (message) say(message, ok ? "ok" : "error"); });
  } catch (err) { problem(err); }
}

async function refreshMarks() {
  try { state.edited = new Set(await api().edited()); } catch (err) { problem(err); return; }
  for (const b of $("unit-list").querySelectorAll("button")) mark(b);
}

function mark(button) {
  if (button.dataset.new === "1") return;  // a unit made in this mod is marked new, whatever else was changed on it
  const on = state.edited.has(button.dataset.address);
  button.classList.toggle("edited", on);
  const badge = button.querySelector(".badge");
  if (on && !badge) button.prepend(el("span", { className: "badge edited", textContent: state.words.edited }));
  if (!on && badge) badge.remove();
}

// --- the list on the left ---
function renderChips() {
  const w = state.words;
  $("kinds").replaceChildren(...KINDS.map((k) => {
    const b = el("button", { type: "button", className: "chip", textContent: w[k], title: w.tip_kind });
    b.setAttribute("aria-pressed", String(state.kind === k));
    b.addEventListener("click", () => { state.kind = k; state.group = "all"; renderChips(); refreshList(); });
    return b;
  }));
  const nations = state.kind === "ammo" ? [] : [-1, 0, 1, 2, 3, 4, 5, 6];  // ammunition has no nation
  $("nations").replaceChildren(...nations.map((n) => {
    const b = el("button", { type: "button", className: "chip", title: w.tip_nation,
      textContent: n < 0 ? w.all : state.nationNames[n] || String(n) });
    b.setAttribute("aria-pressed", String(state.nation === n));
    b.addEventListener("click", () => { state.nation = n; renderChips(); refreshList(); });
    return b;
  }));
}

// What the units listed are for: a building's job (HQ, money, factory, fort, fake) or the factory that builds a unit.
function renderGroups(groups) {
  const w = state.words, pick = $("unit-group");
  pick.classList.toggle("hidden", !groups.length);
  pick.title = w.tip_group;
  pick.setAttribute("aria-label", w.tip_group);
  pick.replaceChildren(el("option", { value: "all", textContent: w.group_all }),
    ...groups.map((g) => el("option", { value: g, textContent: w["group_" + g] || g })));
  pick.value = groups.includes(state.group) ? state.group : "all";
}

async function refreshList() {
  let res;
  try {
    res = await api().units(state.lang, state.kind, state.nation, state.search, state.group || "all");
    state.edited = new Set(await api().edited());
  } catch (err) { problem(err); return; }
  $("count").textContent = state.words.units.replace("{n}", res.units.length);
  renderGroups(res.groups || []);
  $("unit-list").replaceChildren(...res.units.map((u) => {
    const sub = u.kind === "ammo"
      ? (u.nations.length ? u.nations.join(", ") + " · " : "") +
        (u.users.length ? fill(state.words.fired_by, { names: u.users.slice(0, 3).join(", ") +
          (u.users.length > 3 ? ", …" : "") }) : state.words.fired_by_nobody) +
        (u.name !== u.base_name ? ` · ${u.base_name}` : "")
      : `${u.nation_name} · ${state.words[u.kind]}` + (u.name !== u.base_name ? ` · ${u.base_name}` : "");
    const b = el("button", { type: "button", title: state.words.tip_open_unit },
      el("span", { className: "name", textContent: u.name }),
      el("span", { className: "sub", textContent: sub }));
    b.dataset.address = u.address;
    if (u.new) {
      b.dataset.new = "1";
      b.prepend(el("span", { className: "badge new", textContent: state.words.new_mark }));
    }
    b.setAttribute("aria-current", String(u.address === state.selected));
    b.addEventListener("click", () => showUnit(u.address));
    mark(b);
    return el("li", {}, b);
  }));
}

// --- one unit ---
function sameNumbers(a, b) {
  return a.length === b.length && a.every((x, i) => x === b[i]);
}

function numberBox(r, value, label) {
  const bool = r.type === "bool";
  const box = el("input", { type: bool ? "checkbox" : "number", disabled: !state.mod, title: state.words.tip_value });
  if (bool) box.checked = Boolean(value);
  else {
    box.value = String(value);
    box.step = WHOLE.has(r.type) ? "1" : "any";
    box.inputMode = WHOLE.has(r.type) ? "numeric" : "decimal";
  }
  box.setAttribute("aria-label", label);
  return box;
}

function readBox(box) {
  if (box.type === "checkbox") return box.checked ? 1 : 0;
  return box.value.trim() === "" ? NaN : Number(box.value);
}

function asList(r, x) {
  return x === null || x === undefined ? null : r.list ? x : [x];
}

// What a row shows in the current mode: `base` is what the value was before this kind of change (the game's value, or
// for "only this unit", what all of them got), `mine` this kind of change, if any.
function rowState(r, mode) {
  if (mode === "own") return { base: asList(r, r.edited) || r.numbers, mine: asList(r, r.edited_own) };
  return { base: r.numbers, mine: asList(r, r.edited) };
}

function row(u, r, mode) {
  const w = state.words;
  const th = el("th", { textContent: r.label });
  if (state.lang !== "base" && r.label !== r.prop) th.append(el("small", { textContent: r.prop }));
  if (!r.editable) return el("tr", {}, th, el("td", { textContent: r.values.join(" · ") }));
  if (FLAG_LISTS.has(r.prop)) return flagRow(u, r, mode, th);
  const via = state.page.via;
  const st = rowState(r, mode);
  const shown = st.mine || st.base;
  const boxes = shown.map((n, i) => numberBox(r, n, r.list ? `${r.label} [${i}]` : r.label));
  // A list whose values are all the same (a unit's five prices, one per battle date) gets one box that changes them
  // all, so a modder can't change one of five by accident; "set each" shows every box.
  let one = r.list && shown.length > 1 && r.type !== "bool" && shown.every((n) => n === shown[0])
    ? numberBox(r, shown[0], `${r.label} (${w.all_values.replace("{n}", shown.length)})`) : null;
  const holder = el("div", { className: "boxes" }, ...(one ? [one] : boxes));
  if (one) {
    const each = el("button", { type: "button", className: "link", textContent: w.each_value, title: w.tip_each_value });
    each.addEventListener("click", () => {
      boxes.forEach((b) => { b.value = one.value; });
      one = null;
      holder.replaceChildren(...boxes);
      boxes[0].focus();
    });
    holder.append(el("span", { className: "muted small", textContent: w.all_values.replace("{n}", shown.length) }), each);
  }
  const was = el("div", { className: "was" });
  const cell = el("td", {}, holder, was);
  if (r.prop === "ProductionPrice" && r.list) cell.append(el("div", { className: "muted small", textContent: w.price_dates }));
  const tr = el("tr", {}, th, cell);
  const setMine = (value) => {
    st.mine = value;
    const stored = value === null ? null : r.list ? value : value[0];
    if (mode === "own") r.edited_own = stored; else r.edited = stored;
  };

  const showWas = () => {
    tr.classList.toggle("edited", st.mine !== null);
    if (st.mine === null) { was.replaceChildren(); return; }
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_reset });
    undo.addEventListener("click", async () => {
      try {
        await api().reset(u.address, r.prop, mode, via);
        if (isLastEdit(u.address, r.prop, mode, via)) state.lastEdit = null;  // nothing left for Ctrl+Z to take back
        setMine(null);
        boxes.forEach((b, i) => {
          if (b.type === "checkbox") b.checked = Boolean(st.base[i]); else b.value = String(st.base[i]);
          b.setAttribute("aria-invalid", "false");
        });
        if (one) { one.value = String(st.base[0]); one.setAttribute("aria-invalid", "false"); }
        showWas();
        await refreshMarks();
        say("");
      } catch (err) { problem(err); }
    });
    const before = st.base === r.numbers ? r.values : st.base.map(String);
    was.replaceChildren(el("span", { textContent: w.was.replace("{v}", before.join(" · ")) }), undo);
  };

  const save = async (box) => {
    const numbers = one ? boxes.map(() => readBox(one)) : boxes.map(readBox);
    const bad = numbers.findIndex((n) => !Number.isFinite(n));
    if (one) one.setAttribute("aria-invalid", String(bad >= 0));
    else boxes.forEach((b, i) => b.setAttribute("aria-invalid", String(i === bad)));
    if (bad >= 0) { box.focus(); return; }
    try {
      const res = await api().edit(u.address, r.prop, r.list ? numbers : numbers[0], mode, via);
      const value = r.list ? res.value : [res.value];
      value.forEach((n, i) => { if (boxes[i].type !== "checkbox") boxes[i].value = String(n); });
      if (one) one.value = String(value[0]);
      setMine(sameNumbers(value, st.base) ? null : value);
      state.lastEdit = { address: u.address, prop: r.prop, mode, via, label: r.label };  // what Ctrl+Z takes back
      showWas();
      await refreshMarks();
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
  };
  for (const box of boxes) box.addEventListener("change", () => save(box));
  if (one) one.addEventListener("change", () => save(one));
  showWas();
  return tr;
}

// A unit's flags (InitialFlagSet): a set of numbers of any length. Shown as chips with a cross to take one out, and
// an "Add" picker listing every flag the game's units carry (what it does, when known, and who has it).
const FLAG_LISTS = new Set(["InitialFlagSet"]);
let knownFlags = null;  // from api.flags(), once per language

function flagRow(u, r, mode, th) {
  const w = state.words;
  const via = state.page.via;
  const st = rowState(r, mode);
  let current = (st.mine || st.base).slice();
  const chips = el("div", { className: "flags" });
  const was = el("div", { className: "was" });
  const cell = el("td", {}, chips, was);
  const tr = el("tr", {}, th, cell);
  const meaning = (n) => {
    const k = knownFlags && knownFlags.find((f) => f.flag === n);
    if (!k) return String(n);
    const who = k.count ? fill(w.flag_used_by, { n: k.count, names: k.examples.join(", ") }) : "";
    return [k.meaning, who].filter(Boolean).join(" · ");
  };
  const setMine = (value) => {
    st.mine = value;
    if (mode === "own") r.edited_own = value; else r.edited = value;
  };
  const save = async (next) => {
    try {
      const res = await api().edit(u.address, r.prop, next, mode, via);
      current = res.value.slice();
      setMine(sameNumbers(current, st.base) ? null : current);
      render();
      await refreshMarks();
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
  };
  const render = () => {
    tr.classList.toggle("edited", st.mine !== null);
    chips.replaceChildren(...current.map((n) => {
      const chip = el("span", { className: "flag", title: meaning(n) }, String(n));
      if (state.mod) {
        const x = el("button", { type: "button", className: "x", textContent: "×", title: w.flag_remove });
        x.addEventListener("click", () => save(current.filter((m) => m !== n)));
        chip.append(x);
      }
      return chip;
    }));
    if (state.mod) {
      const pick = el("select", { title: w.flag_add });
      pick.append(el("option", { value: "", textContent: w.flag_add }));
      for (const f of knownFlags || []) {
        if (current.includes(f.flag)) continue;
        pick.append(el("option", { value: String(f.flag), textContent: `${f.flag}` + (f.meaning ? ` · ${f.meaning}` : "") +
          ` (${fill(w.flag_count, { n: f.count })})` }));
      }
      pick.append(el("option", { value: "?", textContent: w.flag_add_number }));
      pick.addEventListener("change", () => {
        if (pick.value === "?") {
          const typed = window.prompt(w.flag_add_number, "");
          const n = Number(typed);
          if (typed !== null && typed.trim() !== "" && Number.isInteger(n) && n >= 0 && n < 4294967296) save([...current, n]);
          else pick.value = "";
        } else if (pick.value !== "") save([...current, Number(pick.value)]);
      });
      chips.append(pick);
    }
    was.replaceChildren();
    if (st.mine !== null) {
      const undo = el("button", { type: "button", className: "link", textContent: w.reset });
      undo.addEventListener("click", async () => {
        try {
          await api().reset(u.address, r.prop, mode, via);
          current = st.base.slice();
          setMine(null);
          render();
          await refreshMarks();
          say("");
        } catch (err) { problem(err); }
      });
      was.append(el("span", { textContent: w.was.replace("{v}", st.base.join(" · ")) }), undo);
    }
  };
  if (knownFlags) render();
  else api().flags(state.lang).then((res) => { knownFlags = res.flags; render(); }).catch((err) => { problem(err); render(); });
  return tr;
}

// A unit's weapons and what each fires: one dropdown per weapon, listing every ammunition (the mod's copies first).
function weaponsGroup(u) {
  const w = state.words;
  const group = el("div", { className: "group hidden" }, el("h2", { textContent: w.weapons }));
  api().weapons(u.address, state.lang).then((res) => {
    if (!res.weapons.length) return;
    const table = el("table");
    res.weapons.forEach((wp, i) => {
      const th = el("th", { textContent: fill(w.weapon_n, { n: i + 1 }) }, el("small", { textContent: wp.name }));
      const pick = el("select", { disabled: !state.mod, title: w.fires });
      for (const c of res.choices) {
        pick.append(el("option", { value: c.address, textContent: (c.new ? `${w.new_mark} ` : "") + c.name +
          (c.nations.length ? ` (${c.nations.join(", ")})` : ""),
          selected: c.address === wp.ammo.address }));
      }
      const open = el("button", { type: "button", className: "link", textContent: w.open_ammo });
      open.addEventListener("click", () => showUnit(pick.value));
      const was = el("div", { className: "was" });
      // the muzzle flash and sound this weapon plays (they follow the ammo: api.set_ammo)
      const shot = el("div", { className: "muted small", textContent: wp.shot ? fill(w.shot, { fx: wp.shot }) : "" });
      const tr = el("tr", { className: wp.edited ? "edited" : "" }, th, el("td", {}, el("div", { className: "boxes" }, pick, open), was, shot));
      const showWas = (edited) => {
        tr.classList.toggle("edited", edited);
        was.replaceChildren();
        if (!edited) return;
        const undo = el("button", { type: "button", className: "link", textContent: w.reset });
        undo.addEventListener("click", () => { pick.value = wp.game_ammo; pick.dispatchEvent(new Event("change")); });
        const game = res.choices.find((c) => c.address === wp.game_ammo);
        was.append(el("span", { textContent: w.was.replace("{v}", game ? game.name : wp.game_ammo) }), undo);
      };
      pick.addEventListener("change", async () => {
        try {
          const saved = await api().set_ammo(u.address, wp.address, pick.value);
          showWas(saved.edited);
          const now = (await api().weapons(u.address, state.lang)).weapons.find((x) => x.address === wp.address);
          shot.textContent = now && now.shot ? fill(w.shot, { fx: now.shot }) : "";
          await refreshMarks();
          say(w.saved.replace("{file}", saved.saved), "ok");
        } catch (err) { problem(err); }
      });
      showWas(wp.edited);
      table.append(tr);
    });
    group.append(table, el("p", { className: "muted small", textContent: w.weapons_help }));
    group.classList.remove("hidden");
  }).catch(problem);
  return group;
}

// A copy of an ammunition, for a weapon of its own (its numbers are changed on its page, then a weapon picks it)
function newAmmoForm(u) {
  const w = state.words;
  const open = el("button", { type: "button", className: "ghost", textContent: w.copy_ammo });
  const form = el("form", { className: "new-unit hidden" });
  const name = el("input", { autocomplete: "off", maxLength: 60, required: true, placeholder: w.copy_name });
  name.setAttribute("aria-label", w.copy_name);
  const create = el("button", { type: "submit", className: "primary", textContent: w.create });
  const cancel = el("button", { type: "button", className: "ghost", textContent: w.cancel });
  cancel.addEventListener("click", () => { form.classList.add("hidden"); open.classList.remove("hidden"); });
  form.append(el("label", {}, el("span", { textContent: w.copy_name }), name),
    el("p", { className: "muted small", textContent: w.copy_ammo_help }),
    el("div", { className: "actions" }, create, cancel));
  open.addEventListener("click", () => { open.classList.add("hidden"); form.classList.remove("hidden"); name.focus(); });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!name.value.trim()) return;
    create.disabled = true;
    try {
      const res = await api().new_ammo(u.address, name.value.trim());
      if (state.kind === "ammo") await refreshList();
      await showUnit(res.address);
      say(w.copy_made.replace("{name}", res.name), "ok");
    } catch (err) { problem(err); create.disabled = false; }
  });
  return el("div", { className: "copy" }, open, form);
}

// A part several units share: say who, and let the modder pick for whom a change is.
function shareChoice(u) {
  const w = state.words;
  const names = u.share.owners.map((o) => o.name);
  const shown = names.length > 8 ? names.slice(0, 8).join(", ") + ", …" : names.join(", ");
  const box = el("div", { className: "notice share" },
    el("p", { textContent: w.shared_by.replace("{n}", names.length).replace("{names}", shown) }));
  if (!u.share.via) {
    box.append(el("p", { className: "small", textContent: w.no_via }));
    return box;
  }
  const choice = el("div", { className: "choice", role: "radiogroup" }, el("span", { textContent: w.change_for }));
  for (const [mode, text] of [["own", w.only_unit.replace("{name}", u.share.via.name)],
    ["shared", w.all_units.replace("{n}", names.length)]]) {
    const input = el("input", { type: "radio", name: "share-mode", value: mode, checked: state.mode === mode,
      title: w.tip_change_for });
    input.addEventListener("change", () => { state.mode = mode; showUnit(state.page.address, state.page.via); });
    choice.append(el("label", { title: w.tip_change_for }, input, " " + text));
  }
  box.append(choice);
  return box;
}

// --- new units: a copy of the unit shown, with its own name, price and build menu ---
function factoryLabel(f) {
  const more = f.count - f.units.length;
  return f.units.join(", ") + (more > 0 ? ` ${state.words.more_units.replace("{n}", more)}` : "");
}

function newUnitForm(u) {
  const w = state.words;
  const open = el("button", { type: "button", className: "ghost", textContent: w.new_unit, title: w.tip_new_unit });
  const form = el("form", { className: "new-unit hidden" });
  const name = el("input", { autocomplete: "off", maxLength: 60, required: true, placeholder: w.new_unit_name,
    title: w.tip_unit_name });
  name.setAttribute("aria-label", w.new_unit_name);
  const priceRow = u.groups.flatMap((g) => g.rows).find((r) => r.prop === "ProductionPrice");
  const first = priceRow ? [].concat(priceRow.edited ?? priceRow.numbers)[0] : 0;
  const price = el("input", { type: "number", min: "0", step: "1", inputMode: "numeric", required: true,
    value: String(first), title: w.tip_price });
  price.setAttribute("aria-label", w.price);
  const same = el("input", { type: "radio", name: "menu", value: "same", checked: true, title: w.tip_menu });
  const other = el("input", { type: "radio", name: "menu", value: "other", title: w.tip_menu });
  const nation = el("select", { disabled: true, title: w.tip_menu }), factory = el("select", { disabled: true, title: w.tip_menu });
  nation.setAttribute("aria-label", w.nation);
  factory.setAttribute("aria-label", w.factory);
  let menus = null;
  const fillFactories = () => {
    const n = menus.nations.find((x) => x.nation === Number(nation.value));
    factory.replaceChildren(...(n ? n.factories : []).map((f) =>
      el("option", { value: String(f.factory), textContent: factoryLabel(f) })));
  };
  const menuChoice = () => {
    nation.disabled = factory.disabled = !other.checked;
    if (other.checked && !menus) {
      api().menus(state.lang).then((res) => {
        menus = res;
        nation.replaceChildren(...menus.nations.map((n) =>
          el("option", { value: String(n.nation), textContent: n.name, selected: n.nation === u.nation })));
        fillFactories();
      }).catch(problem);
    }
  };
  same.addEventListener("change", menuChoice);
  other.addEventListener("change", menuChoice);
  nation.addEventListener("change", fillFactories);
  const create = el("button", { type: "submit", className: "primary", textContent: w.create, title: w.tip_create_unit });
  const cancel = el("button", { type: "button", className: "ghost", textContent: w.cancel, title: w.tip_cancel });
  cancel.addEventListener("click", () => { form.classList.add("hidden"); open.classList.remove("hidden"); });
  form.append(
    el("label", {}, el("span", { textContent: w.new_unit_name }), name),
    el("label", {}, el("span", { textContent: w.price }), price),
    el("div", { className: "menu-choice" }, el("span", { textContent: w.build_menu }),
      el("label", {}, same, " " + w.same_menu.replace("{name}", u.name)),
      el("label", {}, other, " " + w.other_menu),
      el("div", { className: "menu-picks" }, el("label", {}, el("span", { textContent: w.nation }), nation),
        el("label", {}, el("span", { textContent: w.factory }), factory))),
    el("div", { className: "actions" }, create, cancel));
  open.addEventListener("click", () => {
    open.classList.add("hidden");
    form.classList.remove("hidden");
    name.focus();
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const cost = Number(price.value);
    if (!name.value.trim() || !Number.isFinite(cost)) return;
    create.disabled = true;
    try {
      const pick = other.checked && menus;
      const res = await api().new_unit(u.address, name.value.trim(), cost,
        pick ? Number(nation.value) : -1, pick ? Number(factory.value) : -1);
      await refreshList();
      await showUnit(res.address);
      say(w.unit_made.replace("{name}", res.name), "ok");
    } catch (err) { problem(err); create.disabled = false; }
  });
  return el("div", { className: "copy" }, open, form);
}

function copyNotice(u) {
  const w = state.words;
  const source = el("button", { type: "button", className: "link", textContent: u.new.source_name, title: w.tip_source });
  source.addEventListener("click", () => showUnit(u.new.source));
  const [before, after] = w.copy_of.split("{name}");
  const box = el("div", { className: "notice new" }, el("p", {}, before, source, after || ""));
  if (!state.mod) return box;
  const label = u.class === "TAmmunition" ? w.delete_copy : w.delete_unit;
  const del = el("button", { type: "button", className: "ghost danger", textContent: label, title: w.tip_delete_unit });
  const sure = el("div", { className: "actions hidden" }, el("span", { textContent: w.really_delete.replace("{name}", u.name) }));
  const yes = el("button", { type: "button", className: "ghost danger", textContent: label, title: w.tip_delete_unit });
  const no = el("button", { type: "button", className: "ghost", textContent: w.cancel, title: w.tip_cancel });
  no.addEventListener("click", () => { sure.classList.add("hidden"); del.classList.remove("hidden"); });
  del.addEventListener("click", () => { del.classList.add("hidden"); sure.classList.remove("hidden"); yes.focus(); });
  yes.addEventListener("click", async () => {
    yes.disabled = true;
    try {
      const res = await api().delete_unit(u.address);
      await refreshList();
      await showUnit(res.source);
      knownFlags = null;
      say(w.unit_deleted.replace("{name}", u.name), "ok");
    } catch (err) { problem(err); yes.disabled = false; }
  });
  sure.append(yes, no);
  box.append(del, sure);
  return box;
}

async function showUnit(address, via) {
  via = via || "";
  if (!state.page || state.page.via !== via) state.mode = "own";  // a new way in: "only this unit" first
  state.selected = address;
  for (const b of $("unit-list").querySelectorAll("button")) {
    b.setAttribute("aria-current", String(b.dataset.address === (via || address)));  // the unit we're inside
  }
  let u;
  try { u = await api().unit(address, state.lang, via); } catch (err) { problem(err); return; }
  state.page = { address, via };
  const inside = u.named ? u.address : via;  // the named unit its parts are opened from
  const mode = u.share ? (u.share.via ? state.mode : "shared") : "";
  const w = state.words;
  const copy = el("button", { type: "button", textContent: w.copy_address, title: w.tip_copy_address });
  copy.addEventListener("click", () => navigator.clipboard && navigator.clipboard.writeText(u.address));
  const parts = [el("h1", { textContent: u.name }),
    el("div", { className: "address" }, el("code", { textContent: u.address }), copy),
    el("div", { className: "meta", textContent: u.class })];
  if (u.new) parts.push(copyNotice(u));
  if (!u.editable) parts.push(el("p", { className: "notice", textContent: w[u.why_not] || u.why_not }));
  else if (!state.mod) parts.push(el("p", { className: "notice", textContent: w.no_mod }));
  else if (u.can_copy) parts.push(newUnitForm(u));
  else if (u.can_copy_ammo) parts.push(newAmmoForm(u));
  if (u.editable && u.users) parts.push(el("p", { className: "notice warn",
    textContent: w.users_warning.replace("{n}", u.users) }));
  if (u.editable && u.share) parts.push(shareChoice(u));
  for (const g of u.groups) {
    const table = el("table");
    for (const r of g.rows) table.append(row(u, r, mode));
    const group = el("div", { className: "group" }, el("h2", { textContent: g.name }), table);
    if (u.editable && g.rows.some((r) => r.locked)) group.append(el("p", { className: "muted small", textContent: w.locked }));
    parts.push(group);
  }
  if (u.has_weapons && u.editable) parts.push(weaponsGroup(u));
  if (u.parts.length) {
    const list = el("ul", { className: "parts" });
    for (const p of u.parts) {
      const b = el("button", { type: "button", title: w.tip_part }, `${p.address.split(":").pop()}  ·  ${p.class}`,
        el("span", { className: "badge" + (p.shared ? " shared" : ""), textContent: p.shared ? w.shared_part : w.own_part }));
      b.addEventListener("click", () => showUnit(p.address, inside));
      list.append(el("li", {}, b));
    }
    parts.push(el("div", { className: "group" }, el("h2", { textContent: w.parts }), list));
  }
  if (u.uses.length) {
    const list = el("ul", { className: "parts" });
    for (const p of u.uses) {
      const b = el("button", { type: "button", title: w.tip_part }, `${p.address.split("/").pop()}  ·  ${p.class}`);
      b.addEventListener("click", () => showUnit(p.address));
      list.append(el("li", {}, b));
    }
    parts.push(el("div", { className: "group" }, el("h2", { textContent: w.uses }), list));
  }
  if (u.used_by.length) {
    const list = el("ul", { className: "parts" });
    for (const r of u.used_by) list.append(el("li", { className: "muted small", textContent: `${r.address}  (${r.path})` }));
    parts.push(el("div", { className: "group" }, el("h2", { textContent: w.used_by }), list));
  }
  $("detail").replaceChildren(...parts);
}

// --- test the mod in the game ---
async function follow(jobId, log, done) {
  let seen = 0;
  const tick = async () => {
    let j;
    try { j = await api().job(jobId, seen); } catch (err) { problem(err); done(false); return; }
    for (const line of j.lines) log.textContent += line + "\n";
    log.scrollTop = log.scrollHeight;
    seen = j.count;
    if (j.state === "running") { setTimeout(tick, 500); return; }
    log.textContent += j.message + "\n";
    log.scrollTop = log.scrollHeight;
    done(j.state === "done", j.message);
  };
  tick();
}

async function testInGame() {
  if (!await checkMod()) { say(state.words.check_stop, "error"); return; }
  const button = $("test");
  button.disabled = true;
  button.dataset.running = "1";
  const log = $("test-log");
  log.textContent = "";
  $("test-panel").classList.remove("hidden");
  const finish = (ok, message) => {
    button.dataset.running = "0";
    button.disabled = !state.mod;
    if (message) say(message, ok ? "ok" : "error");
  };
  try {
    const { job } = await api().test_in_game();
    follow(job, log, finish);
  } catch (err) { problem(err); finish(false); }
}

// --- no index yet ---
async function showNoIndex(status) {
  const w = state.words;
  $("no-index").classList.remove("hidden");
  state.oldIndex = Boolean(status.old);
  $("no-index-text").textContent = status.old ? w.old_index : w.no_index;
  const button = $("build-index");
  button.textContent = w.build_index;
  button.disabled = !status.can_build;
  button.onclick = async () => {
    button.disabled = true;
    const log = $("build-log");
    log.classList.remove("hidden");
    const { job } = await api().build_index();
    follow(job, log, async (ok) => {
      if (ok) { $("no-index").classList.add("hidden"); await setLanguage(state.lang); }
      else button.disabled = false;
    });
  };
}

// --- keys in the Units view: / or Ctrl+F to the search box, Esc clears it, Up and Down walk the list (and open
// what they land on), Ctrl+Z takes back the last value changed this session ---
function isLastEdit(address, prop, mode, via) {
  const l = state.lastEdit;
  return Boolean(l && l.address === address && l.prop === prop && l.mode === mode && l.via === via);
}

async function undoLastEdit() {
  const last = state.lastEdit;
  if (!last) return;
  try {
    await api().reset(last.address, last.prop, last.mode, last.via);
    state.lastEdit = null;
    await refreshMarks();
    if (state.page) await showUnit(state.page.address, state.page.via);  // drawn again: the row shows the old value
    say(fill(state.words.undone, { name: last.label }), "ok");
  } catch (err) { problem(err); }
}

let moveTimer = null;
function moveSelection(dir) {
  const buttons = [...$("unit-list").querySelectorAll("button[data-address]")];
  if (!buttons.length) return;
  const at = buttons.findIndex((b) => b.getAttribute("aria-current") === "true");
  const next = buttons[Math.min(buttons.length - 1, Math.max(0, at + dir))];
  if (!next || next.getAttribute("aria-current") === "true") return;
  for (const b of buttons) b.setAttribute("aria-current", String(b === next));
  next.scrollIntoView({ block: "nearest" });
  clearTimeout(moveTimer);  // held down: open where it stops, not every step on the way
  moveTimer = setTimeout(() => showUnit(next.dataset.address), 120);
}

function unitKeys(e) {
  if (state.view !== "units" || !$("no-index").classList.contains("hidden")) return;
  const a = document.activeElement, tag = a ? a.tagName : "", inSearch = a === $("search");
  const inText = !inSearch && (tag === "TEXTAREA" || (tag === "INPUT" && !["number", "range", "checkbox", "radio", "button"].includes(a.type)));
  const inField = inSearch || inText || tag === "SELECT" || (tag === "INPUT" && a.type === "number");
  const ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && !e.altKey && e.code === "KeyZ") { if (inText || inSearch) return; e.preventDefault(); undoLastEdit(); return; }
  if (ctrl && !e.altKey && e.code === "KeyF") { e.preventDefault(); $("search").focus(); $("search").select(); return; }
  if (ctrl || e.altKey) return;
  if (e.key === "/" && !inField) { e.preventDefault(); $("search").focus(); $("search").select(); return; }
  if (!inSearch && inField) return;
  if (e.key === "Escape" && inSearch) {
    if ($("search").value) { $("search").value = ""; state.search = ""; refreshList(); } else $("search").blur();
    return;
  }
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); moveSelection(e.key === "ArrowDown" ? 1 : -1); return; }
  if (e.key === "Enter" && inSearch) {
    const current = $("unit-list").querySelector('button[aria-current="true"]') || $("unit-list").querySelector("button");
    if (current) { e.preventDefault(); showUnit(current.dataset.address); }
  }
}

// --- the tabs: units, or maps (maps.js, a module: it may still be loading) ---
function showView(view) {
  state.view = view;
  $("units-view").classList.toggle("hidden", view !== "units");
  $("maps-view").classList.toggle("hidden", view !== "maps");
  $("settings-view").classList.toggle("hidden", view !== "settings");
  $("tab-units").setAttribute("aria-selected", String(view === "units"));
  $("tab-maps").setAttribute("aria-selected", String(view === "maps"));
  $("tab-settings").setAttribute("aria-selected", String(view === "settings"));
  if (view === "settings") { renderSettings(); return; }
  if (view !== "maps") return;
  const open = () => window.MapView.open(api(), state.words, state.lang).catch(problem);
  if (window.MapView) open();
  else window.addEventListener("mapview-ready", open, { once: true });
}

// --- Settings: one entry per section (its words are set_<id>_title / _help); a new setting is one more entry and
// its section in index.html. What they change is kept by the app (settings.json), not by the window.
const SETTINGS = [
  { id: "language", render() {} },  // the language list is filled at start (renderLanguages) and saved on change
  { id: "keys", render() { if (window.MapView && window.MapView.renderKeysPanel) window.MapView.renderKeysPanel(api(), state.words); } },
  { id: "game", async render() {
    const w = state.words, g = await api().game_folder();
    $("set-game-path").textContent = g.message || (g.path ? fill(w.set_game_path, { path: g.path }) : w.set_game_none);
    $("set-game-change").textContent = w.set_game_change;
  } },
  { id: "updates", async render() {
    const w = state.words, u = state.update || {};
    if (!state.version) state.version = (await api().game_folder()).version;
    $("set-updates-text").textContent = u.available ? fill(w.update_out || "", { app: APP_NAME, version: u.version })
      : u.error ? u.error : fill(w.set_updates_latest, { version: state.version || "" });
    $("set-updates-check").textContent = w.set_updates_check;
  } },
  { id: "help", render() {
    const w = state.words;
    for (const [id, word] of [["help-wiki", "help_wiki"], ["help-discussions", "help_discussions"], ["help-report", "report_problem"]]) {
      $(id).textContent = w[word];
      $(id).title = w["tip_" + word] || "";
    }
  } },
];

function renderSettings() {
  const w = state.words;
  $("settings-title").textContent = w.settings_title;
  for (const s of SETTINGS) {
    $(`set-${s.id}-title`).textContent = w[`set_${s.id}_title`] || s.id;
    const help = $(`set-${s.id}-help`);
    if (help) help.textContent = w[`set_${s.id}_help`] || "";
    Promise.resolve(s.render()).catch(problem);
  }
}

// The map view's "Change keys…" opens Settings at the keys.
window.openSettings = (id) => {
  showView("settings");
  const at = $(`set-${id}`);
  if (at) at.scrollIntoView({ block: "start" });
};

// --- a newer release (rusemod/update.py): offered in the header; Update downloads it, checks it and installs it,
// then the app closes and the installer opens it again ---
const APP_NAME = "RUSE Studio";

async function checkUpdate() {
  try { state.update = await api().update_check(); } catch { state.update = null; }
  renderUpdate();
}

function renderUpdate() {
  const u = state.update, w = state.words, bar = $("update-bar");
  if (!u || !u.available || !w.update_out) { bar.classList.add("hidden"); return; }
  $("update-text").textContent = state.updateNote
    || fill(w.update_out, { app: APP_NAME, version: u.version }) + (u.installed ? "" : " " + w.update_repo);
  $("update-now").textContent = w.update_now;
  $("update-now").classList.toggle("hidden", !u.installed);
  $("update-now").disabled = Boolean(state.updating);
  $("update-info").textContent = w.whats_new;
  bar.classList.remove("hidden");
}

async function installUpdate() {
  const w = state.words;
  state.updating = true;
  state.updateNote = fill(w.update_progress, { pct: "" });
  renderUpdate();
  let job;
  try {
    ({ job } = await api().update_install());
  } catch (err) {
    state.updating = false;
    state.updateNote = fill(w.update_failed, { why: (err && err.message) || String(err) });
    renderUpdate();
    return;
  }
  let seen = 0;
  const tick = async () => {
    let j;
    try { j = await api().job(job, seen); } catch { return; }  // the app is closing for the installer
    seen = j.count;
    const last = j.lines[j.lines.length - 1];
    if (last) state.updateNote = last === "installing" ? fill(w.update_installing, { app: APP_NAME })
      : fill(w.update_progress, { pct: last });
    if (j.state === "running") { renderUpdate(); setTimeout(tick, 400); return; }
    if (j.state === "failed") { state.updating = false; state.updateNote = fill(w.update_failed, { why: j.message }); }
    else state.updateNote = fill(w.update_installing, { app: APP_NAME });
    renderUpdate();
  };
  tick();
}

async function start() {
  $("tab-units").addEventListener("click", () => showView("units"));
  $("tab-maps").addEventListener("click", () => showView("maps"));
  $("tab-settings").addEventListener("click", () => showView("settings"));
  $("set-game-change").addEventListener("click", async () => {
    const g = await api().choose_game_folder().catch(problem);
    if (g) renderSettings();
    if (g && g.message) $("set-game-path").textContent = g.message;
  });
  $("help-wiki").addEventListener("click", () => api().open_help("wiki").catch(problem));
  $("help-discussions").addEventListener("click", () => api().open_help("discussions").catch(problem));
  $("help-report").addEventListener("click", () => api().report_problem("").catch(problem));
  $("set-updates-check").addEventListener("click", async () => {
    $("set-updates-text").textContent = state.words.set_updates_checking;
    try { state.update = await api().update_check(); } catch (err) { state.update = { error: (err && err.message) || String(err) }; }
    renderUpdate();
    renderSettings();
  });
  state.languages = await api().languages();
  state.lang = await loadLang();
  if (!state.languages.some((l) => l.code === state.lang)) state.lang = "base";
  $("lang").addEventListener("change", (e) => setLanguage(e.target.value));
  $("mod").addEventListener("change", pickMod);
  $("new-mod").addEventListener("submit", createMod);
  $("new-mod-cancel").addEventListener("click", () => $("new-mod").classList.add("hidden"));
  $("export-mod").addEventListener("submit", exportMod);
  $("export-cancel").addEventListener("click", () => $("export-mod").classList.add("hidden"));
  $("test").addEventListener("click", testInGame);
  $("test-log-close").addEventListener("click", () => $("test-panel").classList.add("hidden"));
  let timer = null;
  $("unit-group").addEventListener("change", (e) => { state.group = e.target.value; refreshList(); });
  $("search").addEventListener("input", (e) => {
    state.search = e.target.value;
    clearTimeout(timer);
    timer = setTimeout(refreshList, 150);
  });
  window.addEventListener("keydown", unitKeys);
  const res = await api().mods();
  state.mods = res.mods;
  state.mod = res.current;
  const status = await api().status();
  if (!status.ready) {
    state.words = await api().strings(state.lang);
    await showNoIndex(status);
  }
  $("update-now").addEventListener("click", installUpdate);
  $("update-info").addEventListener("click", () => api().update_page().catch(() => {}));
  await setLanguage(state.lang);
  checkUpdate();
}

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start().catch(problem);
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
