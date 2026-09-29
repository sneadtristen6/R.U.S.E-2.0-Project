// The Studio screen: browse units, see one unit's values, parts and users, and change its numbers in a mod (saved at
// once in the mod's src/studio.rndf), then test it in the game. Talks to StudioApi (ruse_studio/api.py) through
// window.pywebview.api; open index.html?fake in a normal browser for made-up data.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { lang: "base", kind: "all", nation: -1, search: "", selected: null, words: {}, languages: [],
  nationNames: [], mods: [], mod: null, edited: new Set(),
  page: null,     // the object shown: { address, via }; via = the named unit the modder came from
  mode: "own",    // a part several units share: change it for "own" (that unit only) or "shared" (all of them)
  view: "units" };  // the tab: "units" or "maps" (maps.js)
const KINDS = ["all", "ground", "infantry", "air", "buildings"];
const WHOLE = new Set(["int8", "int16", "uint16", "int32", "uint32", "int64"]);
const NEW = "\u0001new", OPEN = "\u0001open";  // the mod menu's two actions (never a folder path)

function api() { return window.pywebview.api; }

function el(tag, props, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props || {});
  for (const c of children) node.append(c);
  return node;
}

function loadLang() {
  try { return localStorage.getItem("studio.lang") || "base"; } catch { return "base"; }
}

function saveLang(lang) {
  try { localStorage.setItem("studio.lang", lang); } catch { /* private window: fine */ }
}

// --- the bar at the bottom: what just happened ---
function say(text, kind) {
  const bar = $("status");
  bar.textContent = text || "";
  bar.className = "status" + (kind ? " " + kind : "");
}

function problem(err) {
  say((err && err.message) || String(err), "error");
}

// --- words ---
async function setLanguage(lang) {
  state.lang = lang;
  saveLang(lang);
  state.words = await api().strings(lang);
  state.nationNames = await api().nations(lang);
  const w = state.words;
  $("tab-units").textContent = w.units_tab;
  $("tab-maps").textContent = w.maps_tab;
  if (state.view === "maps" && window.MapView) window.MapView.setWords(w);
  $("lang-label").textContent = w.language;
  $("mod-label").textContent = w.mod;
  $("test").textContent = w.test_in_game;
  $("new-mod-name").placeholder = w.mod_name;
  $("new-mod-create").textContent = w.create;
  $("new-mod-cancel").textContent = w.cancel;
  $("test-log-close").textContent = w.close;
  $("lang").replaceChildren(...state.languages.map((l) =>
    el("option", { value: l.code, textContent: l.code === "base" ? w.game_names : l.name, selected: l.code === lang })));
  $("search").placeholder = w.search;
  $("no-index-text").textContent = w.no_index;
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
  options.push(el("option", { value: NEW, textContent: w.new_mod }), el("option", { value: OPEN, textContent: w.open_folder }));
  $("mod").replaceChildren(...options);
  $("test").disabled = !state.mod || $("test").dataset.running === "1";
}

function useMods(res) {
  state.mods = res.mods;
  state.mod = res.current;
  renderMods();
}

async function modChanged() {
  await refreshMarks();
  if (state.page) await showUnit(state.page.address, state.page.via);
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

async function refreshMarks() {
  try { state.edited = new Set(await api().edited()); } catch (err) { problem(err); return; }
  for (const b of $("unit-list").querySelectorAll("button")) mark(b);
}

function mark(button) {
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
    const b = el("button", { type: "button", className: "chip", textContent: w[k] });
    b.setAttribute("aria-pressed", String(state.kind === k));
    b.addEventListener("click", () => { state.kind = k; renderChips(); refreshList(); });
    return b;
  }));
  const nations = [-1, 0, 1, 2, 3, 4, 5, 6];
  $("nations").replaceChildren(...nations.map((n) => {
    const b = el("button", { type: "button", className: "chip",
      textContent: n < 0 ? w.all : state.nationNames[n] || String(n) });
    b.setAttribute("aria-pressed", String(state.nation === n));
    b.addEventListener("click", () => { state.nation = n; renderChips(); refreshList(); });
    return b;
  }));
}

async function refreshList() {
  let res;
  try {
    res = await api().units(state.lang, state.kind, state.nation, state.search);
    state.edited = new Set(await api().edited());
  } catch (err) { problem(err); return; }
  $("count").textContent = state.words.units.replace("{n}", res.units.length);
  $("unit-list").replaceChildren(...res.units.map((u) => {
    const b = el("button", { type: "button" },
      el("span", { className: "name", textContent: u.name }),
      el("span", { className: "sub", textContent: `${u.nation_name} · ${state.words[u.kind]}` +
        (u.name !== u.base_name ? ` · ${u.base_name}` : "") }));
    b.dataset.address = u.address;
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
  const box = el("input", { type: bool ? "checkbox" : "number", disabled: !state.mod });
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
    const each = el("button", { type: "button", className: "link", textContent: w.each_value });
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
    const undo = el("button", { type: "button", className: "link", textContent: w.reset });
    undo.addEventListener("click", async () => {
      try {
        await api().reset(u.address, r.prop, mode, via);
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
    const input = el("input", { type: "radio", name: "share-mode", value: mode, checked: state.mode === mode });
    input.addEventListener("change", () => { state.mode = mode; showUnit(state.page.address, state.page.via); });
    choice.append(el("label", {}, input, " " + text));
  }
  box.append(choice);
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
  const copy = el("button", { type: "button", textContent: w.copy_address });
  copy.addEventListener("click", () => navigator.clipboard && navigator.clipboard.writeText(u.address));
  const parts = [el("h1", { textContent: u.name }),
    el("div", { className: "address" }, el("code", { textContent: u.address }), copy),
    el("div", { className: "meta", textContent: u.class })];
  if (!u.editable) parts.push(el("p", { className: "notice", textContent: w[u.why_not] || u.why_not }));
  else if (!state.mod) parts.push(el("p", { className: "notice", textContent: w.no_mod }));
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
  if (u.parts.length) {
    const list = el("ul", { className: "parts" });
    for (const p of u.parts) {
      const b = el("button", { type: "button" }, `${p.address.split(":").pop()}  ·  ${p.class}`,
        el("span", { className: "badge" + (p.shared ? " shared" : ""), textContent: p.shared ? w.shared_part : w.own_part }));
      b.addEventListener("click", () => showUnit(p.address, inside));
      list.append(el("li", {}, b));
    }
    parts.push(el("div", { className: "group" }, el("h2", { textContent: w.parts }), list));
  }
  if (u.uses.length) {
    const list = el("ul", { className: "parts" });
    for (const p of u.uses) {
      const b = el("button", { type: "button" }, `${p.address.split("/").pop()}  ·  ${p.class}`);
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
  $("no-index-text").textContent = w.no_index;
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

// --- the tabs: units, or maps (maps.js, a module: it may still be loading) ---
function showView(view) {
  state.view = view;
  $("units-view").classList.toggle("hidden", view !== "units");
  $("maps-view").classList.toggle("hidden", view !== "maps");
  $("tab-units").setAttribute("aria-selected", String(view === "units"));
  $("tab-maps").setAttribute("aria-selected", String(view === "maps"));
  if (view !== "maps") return;
  const open = () => window.MapView.open(api(), state.words).catch(problem);
  if (window.MapView) open();
  else window.addEventListener("mapview-ready", open, { once: true });
}

async function start() {
  $("tab-units").addEventListener("click", () => showView("units"));
  $("tab-maps").addEventListener("click", () => showView("maps"));
  state.languages = await api().languages();
  state.lang = loadLang();
  if (!state.languages.some((l) => l.code === state.lang)) state.lang = "base";
  $("lang").addEventListener("change", (e) => setLanguage(e.target.value));
  $("mod").addEventListener("change", pickMod);
  $("new-mod").addEventListener("submit", createMod);
  $("new-mod-cancel").addEventListener("click", () => $("new-mod").classList.add("hidden"));
  $("test").addEventListener("click", testInGame);
  $("test-log-close").addEventListener("click", () => $("test-panel").classList.add("hidden"));
  let timer = null;
  $("search").addEventListener("input", (e) => {
    state.search = e.target.value;
    clearTimeout(timer);
    timer = setTimeout(refreshList, 150);
  });
  const res = await api().mods();
  state.mods = res.mods;
  state.mod = res.current;
  const status = await api().status();
  if (!status.ready) {
    state.words = await api().strings(state.lang);
    await showNoIndex(status);
  }
  await setLanguage(state.lang);
}

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start().catch(problem);
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
