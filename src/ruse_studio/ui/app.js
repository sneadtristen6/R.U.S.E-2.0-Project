// The Studio screen: browse units, see one unit's values, parts and users, and change its numbers in a mod (saved at
// once in the mod's src/studio.rndf), then test it in the game. Talks to StudioApi (ruse_studio/api.py) through
// window.pywebview.api; open index.html?fake in a normal browser for made-up data.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { lang: "base", kind: "all", nation: -1, search: "", selected: null, words: {}, languages: [],
  nationNames: [], mods: [], mod: null, edited: new Set() };
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
    if (state.selected) await showUnit(state.selected);
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
  if (state.selected) await showUnit(state.selected);
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

function row(u, r) {
  const w = state.words;
  const th = el("th", { textContent: r.label });
  if (state.lang !== "base" && r.label !== r.prop) th.append(el("small", { textContent: r.prop }));
  if (!r.editable) return el("tr", {}, th, el("td", { textContent: r.values.join(" · ") }));
  const current = r.edited === null || r.edited === undefined ? r.numbers : r.list ? r.edited : [r.edited];
  const boxes = current.map((n, i) => numberBox(r, n, r.list ? `${r.label} [${i}]` : r.label));
  const was = el("div", { className: "was" });
  const tr = el("tr", {}, th, el("td", {}, el("div", { className: "boxes" }, ...boxes), was));

  const showWas = () => {
    const edited = r.edited !== null && r.edited !== undefined;
    tr.classList.toggle("edited", edited);
    if (!edited) { was.replaceChildren(); return; }
    const undo = el("button", { type: "button", className: "link", textContent: w.reset });
    undo.addEventListener("click", async () => {
      try {
        await api().reset(u.address, r.prop);
        r.edited = null;
        boxes.forEach((b, i) => {
          if (b.type === "checkbox") b.checked = Boolean(r.numbers[i]); else b.value = String(r.numbers[i]);
          b.setAttribute("aria-invalid", "false");
        });
        showWas();
        await refreshMarks();
        say("");
      } catch (err) { problem(err); }
    });
    was.replaceChildren(el("span", { textContent: w.was.replace("{v}", r.values.join(" · ")) }), undo);
  };

  const save = async (box) => {
    const numbers = boxes.map(readBox);
    const bad = numbers.findIndex((n) => !Number.isFinite(n));
    boxes.forEach((b, i) => b.setAttribute("aria-invalid", String(i === bad)));
    if (bad >= 0) { box.focus(); return; }
    try {
      const res = await api().edit(u.address, r.prop, r.list ? numbers : numbers[0]);
      const value = r.list ? res.value : [res.value];
      value.forEach((n, i) => { if (boxes[i].type !== "checkbox") boxes[i].value = String(n); });
      r.edited = sameNumbers(value, r.numbers) ? null : r.list ? value : value[0];
      showWas();
      await refreshMarks();
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
  };
  for (const box of boxes) box.addEventListener("change", () => save(box));
  showWas();
  return tr;
}

async function showUnit(address) {
  state.selected = address;
  for (const b of $("unit-list").querySelectorAll("button")) {
    b.setAttribute("aria-current", String(b.dataset.address === address));
  }
  let u;
  try { u = await api().unit(address, state.lang); } catch (err) { problem(err); return; }
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
  for (const g of u.groups) {
    const table = el("table");
    for (const r of g.rows) table.append(row(u, r));
    const group = el("div", { className: "group" }, el("h2", { textContent: g.name }), table);
    if (u.editable && g.rows.some((r) => r.locked)) group.append(el("p", { className: "muted small", textContent: w.locked }));
    parts.push(group);
  }
  if (u.parts.length) {
    const list = el("ul", { className: "parts" });
    for (const p of u.parts) {
      const b = el("button", { type: "button" }, `${p.address.split(":").pop()}  ·  ${p.class}`,
        el("span", { className: "badge" + (p.shared ? " shared" : ""), textContent: p.shared ? w.shared_part : w.own_part }));
      b.addEventListener("click", () => showUnit(p.address));
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

async function start() {
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
