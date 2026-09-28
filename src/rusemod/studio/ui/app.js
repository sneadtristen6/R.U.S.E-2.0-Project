// The Studio v0.1 screen: browse units, see one unit's values, parts and users. Talks to StudioApi
// (studio/api.py) through window.pywebview.api; open index.html?fake in a normal browser for made-up data.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { lang: "base", kind: "all", nation: -1, search: "", selected: null, words: {}, languages: [],
  nationNames: [] };
const KINDS = ["all", "ground", "infantry", "air", "buildings"];

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

async function setLanguage(lang) {
  state.lang = lang;
  saveLang(lang);
  state.words = await api().strings(lang);
  state.nationNames = await api().nations(lang);
  const w = state.words;
  $("lang-label").textContent = w.language;
  const select = $("lang");
  select.replaceChildren(...state.languages.map((l) =>
    el("option", { value: l.code, textContent: l.code === "base" ? w.game_names : l.name, selected: l.code === lang })));
  $("search").placeholder = w.search;
  if ($("pick")) $("pick").textContent = w.pick_unit;  // gone once a unit is shown
  renderChips();
  await refreshList();
  if (state.selected) await showUnit(state.selected);
}

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
  const res = await api().units(state.lang, state.kind, state.nation, state.search);
  $("count").textContent = state.words.units.replace("{n}", res.units.length);
  $("unit-list").replaceChildren(...res.units.map((u) => {
    const b = el("button", { type: "button" },
      el("span", { className: "name", textContent: u.name }),
      el("span", { className: "sub", textContent: `${u.nation_name} · ${state.words[u.kind]}` +
        (u.name !== u.base_name ? ` · ${u.base_name}` : "") }));
    b.dataset.address = u.address;
    b.setAttribute("aria-current", String(u.address === state.selected));
    b.addEventListener("click", () => showUnit(u.address));
    return el("li", {}, b);
  }));
}

async function showUnit(address) {
  state.selected = address;
  for (const b of $("unit-list").querySelectorAll("button")) {
    b.setAttribute("aria-current", String(b.dataset.address === address));
  }
  const u = await api().unit(address, state.lang);
  const w = state.words;
  const copy = el("button", { type: "button", textContent: w.copy_address });
  copy.addEventListener("click", () => navigator.clipboard && navigator.clipboard.writeText(u.address));
  const parts = [el("h1", { textContent: u.name }),
    el("div", { className: "address" }, el("code", { textContent: u.address }), copy),
    el("div", { className: "meta", textContent: u.class }),
    el("div", {}, el("button", { type: "button", className: "primary", disabled: true, textContent: w.copy_unit }),
      el("span", { className: "note", textContent: w.coming_next }))];
  for (const g of u.groups) {
    const table = el("table");
    for (const r of g.rows) {
      const th = el("th", { textContent: r.label });
      if (state.lang !== "base" && r.label !== r.prop) th.append(el("small", { textContent: r.prop }));
      table.append(el("tr", {}, th, el("td", { textContent: r.values.join(" · ") })));
    }
    parts.push(el("div", { className: "group" }, el("h2", { textContent: g.name }), table));
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
  if (u.used_by.length) {
    const list = el("ul", { className: "parts" });
    for (const r of u.used_by) list.append(el("li", { className: "muted small", textContent: `${r.address}  (${r.path})` }));
    parts.push(el("div", { className: "group" }, el("h2", { textContent: w.used_by }), list));
  }
  $("detail").replaceChildren(...parts);
}

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
    let seen = 0;
    const tick = async () => {
      const j = await api().job(job, seen);
      for (const line of j.lines) log.textContent += line + "\n";
      log.scrollTop = log.scrollHeight;
      seen = j.count;
      if (j.state === "running") return setTimeout(tick, 500);
      log.textContent += j.message + "\n";
      if (j.state === "done") { $("no-index").classList.add("hidden"); await setLanguage(state.lang); }
      else button.disabled = false;
    };
    tick();
  };
}

async function start() {
  state.languages = await api().languages();
  state.lang = loadLang();
  if (!state.languages.some((l) => l.code === state.lang)) state.lang = "base";
  state.words = await api().strings(state.lang);
  $("lang").addEventListener("change", (e) => setLanguage(e.target.value));
  let timer = null;
  $("search").addEventListener("input", (e) => {
    state.search = e.target.value;
    clearTimeout(timer);
    timer = setTimeout(refreshList, 150);
  });
  const status = await api().status();
  if (!status.ready) {
    await showNoIndex(status);
    return;
  }
  await setLanguage(state.lang);
}

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start();
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
