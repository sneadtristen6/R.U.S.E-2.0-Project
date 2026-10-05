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
  start: "change",     // the Units tab's way in (renderStart): "change" a unit, or start a "new" one from it
  focusModel: null,    // a new unit just made: its page opens at Import model (lookBox)
  lastEdit: null };  // the last value changed this session, for Ctrl+Z: { address, prop, mode, via, label }
const KINDS = ["all", "ground", "infantry", "air", "buildings", "ammo"];  // ammo: what weapons fire (its own list)
const WHOLE = new Set(["int8", "int16", "uint16", "int32", "uint32", "int64"]);
const NEW = "\u0001new", OPEN = "\u0001open", EXPORT = "\u0001export", SHARE = "\u0001share";  // the mod menu's actions (never a folder path)

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
  try { return localStorage.getItem("studio.lang"); } catch { return null; }
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
  if (text) {  // every message can be closed (owner, 2026-10-02: a failed test's message stayed with no way out)
    const close = el("button", { type: "button", className: "status-close", textContent: "×",
      title: w.tip_status_close || "", ariaLabel: w.close || "Close" });
    close.addEventListener("click", () => say(""));
    bar.append(close);
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
  $("lang-name").textContent = lang === "base" ? w.game_names
    : (state.languages.find((l) => l.code === lang) || {}).name || "";
  renderLangPick();
  $("mod-label").textContent = w.mod;
  $("test").textContent = w.test_in_game;
  $("troubleshoot").textContent = w.doc_button;
  $("troubleshoot").title = w.doc_intro;
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
  $("test-log-copy").textContent = w.doc_copy;
  // tooltips: one sentence on every control, from words.toml (tip_*)
  const tips = { "tab-units": "tip_tab_units", "tab-maps": "tip_tab_maps", "tab-settings": "tip_tab_settings", mod: "tip_mod", test: "tip_test", "lang-open": "tip_lang_open",
    "update-now": "tip_update_now", "update-info": "tip_update_info", "new-mod-create": "tip_create_mod",
    "new-mod-cancel": "tip_cancel", "export-go": "tip_export", "export-cancel": "tip_cancel", "test-log-close": "tip_close", "test-log-copy": "tip_copy_log",
    "build-index": "tip_build_index", search: "tip_search", "set-game-change": "tip_game_change",
    "backup-make": "tip_backup_make", "backup-check": "tip_backup_check", "backup-restore": "tip_backup_restore",
    "backup-deep": "tip_backup_deep", "set-updates-check": "tip_updates_check" };
  for (const [id, key] of Object.entries(tips)) $(id).title = w[key] || "";
  $("search").placeholder = w.search;
  $("no-index-text").textContent = state.oldIndex ? w.old_index : w.no_index;
  $("build-index").textContent = w.build_index;
  renderMods();
  renderStart();  // and the hint on the right, gone once a unit is shown
  renderChips();
  if (state.view === "settings") renderSettings();  // the language is picked there: its own words change at once
  if ($("no-index").classList.contains("hidden")) {
    await refreshList();
    if (state.page) await showUnit(state.page.address, state.page.via);
  }
}

// --- the mod (Units tab) and the map (Maps tab) being edited: kept apart, each its own menu (StudioApi.mods(kind)) ---
const PICKER = { mod: "mod", map: "map-project" };

function renderMods() {
  const w = state.words;
  for (const kind of ["mod", "map"]) {
    const current = kind === "mod" ? state.mod : state.map, list = kind === "mod" ? state.mods : state.maps || [];
    const options = [];
    if (!current) options.push(el("option", { value: "", textContent: kind === "mod" ? w.no_mod : w.no_map, disabled: true, selected: true }));
    for (const m of list) options.push(el("option", { value: m.path, textContent: m.name, title: m.path,
      selected: m.path === current }));
    options.push(el("option", { value: NEW, textContent: kind === "mod" ? w.new_mod : w.new_map }),
      el("option", { value: OPEN, textContent: w.open_folder }),
      el("option", { value: EXPORT, textContent: kind === "mod" ? w.export_mod : w.export_map, disabled: !current }),
      el("option", { value: SHARE, textContent: w.share_mod }));
    $(PICKER[kind]).replaceChildren(...options);
  }
  $("mod").title = w.tip_pick_mod || "";
  $("map-project").title = w.tip_pick_map || "";
  $("map-project-label").textContent = w.map_project || "Map changes";
  $("test").disabled = !(state.mod || state.map) || $("test").dataset.running === "1";
}

function useMods(res) {
  if ((res.kind || "mod") === "map") {
    state.maps = res.mods;
    state.map = res.current;
    renderMods();
    return;
  }
  if (res.current !== state.mod) state.exported = null;  // "Share your mod" shows the file of the mod being edited
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

async function pickMod(e, kind = "mod") {
  const value = e.target.value;
  renderMods();  // the menu shows the mod being edited until something else is picked
  try {
    if (value === NEW) {
      state.newKind = kind;
      $("new-mod-name").placeholder = kind === "map" ? state.words.map_name : state.words.mod_name;
      $("new-mod").classList.remove("hidden");
      $("new-mod-name").focus();
      return;
    }
    if (value === EXPORT) { await openExport(kind); return; }
    if (value === SHARE) { await openShare(state.exported); return; }
    useMods(value === OPEN ? await api().open_mod_folder(kind) : await api().choose_mod(value, kind));
    if (kind === "map") { if (window.MapView && window.MapView.modChanged) window.MapView.modChanged(); }
    else await modChanged();
  } catch (err) { problem(err); }
}

async function createMod(e) {
  e.preventDefault();
  const name = $("new-mod-name").value.trim(), kind = state.newKind || "mod";
  if (!name) return;
  try {
    useMods(await api().new_mod(name, kind));
    $("new-mod").classList.add("hidden");
    $("new-mod-name").value = "";
    say(`${kind === "map" ? state.words.map_project : state.words.mod}: ${kind === "map" ? state.map : state.mod}`, "ok");
    if (kind === "map") { if (window.MapView && window.MapView.modChanged) window.MapView.modChanged(); }
    else await modChanged();
  } catch (err) { problem(err); }
}

// --- the mod (or map) as one file (Export…): version, author and description; it goes straight into the Launcher's
// library and the platform's exports folder (StudioApi.export_mod)
async function openExport(kind = "mod") {
  state.exportKind = kind;
  const info = await api().mod_info(kind);
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
    const { job } = await api().export_mod(version, $("export-author").value.trim(), $("export-description").value.trim(),
      state.exportKind || "mod");
    if (!job) return;  // the dialog was cancelled
    $("export-mod").classList.add("hidden");
    const log = $("test-log");
    log.textContent = "";
    $("test-panel").classList.remove("hidden");
    follow(job, log, (ok, message, j) => {
      if (message) say(message, ok ? "ok" : "error");
      if (ok && j && j.result) { state.exported = j.result; openShare(j.result); }  // its size and SHA-256 for the list
    });
  } catch (err) { problem(err); }
}

// --- Share your mod: how an exported mod gets onto the supported-mods list (MOD_FORMAT §15). After an export it shows
// the file's size, SHA-256 and its index.toml entry, and the credit line its manifest carries; Publish opens the list's
// "Add my mod" form filled in from the file (StudioApi.publish_mod); the other buttons open the list's guidelines, its
// page and the Discussions ---
async function openShare(file) {
  const w = state.words;
  let info = { repo: "sneadtristen6/Ruse-Mods", credit: "" };
  try { info = await api().share_info(); } catch { /* an older Studio: the list's usual name */ }
  $("share-title").textContent = w.share_title;
  $("share-lead").textContent = w.share_lead;
  $("share-step-export").textContent = w.share_step_export;
  $("share-step-pr").textContent = fillText(w.share_step_pr, { repo: info.repo });
  $("share-step-post").textContent = w.share_step_post;
  $("share-file").classList.toggle("hidden", !file);
  if (file) {
    $("share-file-name").textContent = fillText(w.share_file, { file: file.file, size: file.size });
    $("share-sha").textContent = fillText(w.share_sha, { sha: file.sha256 });
    $("share-entry-label").textContent = w.share_entry;
    $("share-entry").value = file.entry;
  }
  $("share-copy").textContent = w.share_copy;
  $("share-note").textContent = "";
  $("share-credit-label").textContent = w.share_credit;
  $("share-credit").value = (file && file.credit) || info.credit || "";
  $("share-credit-copy").textContent = w.share_credit_copy;
  $("share-published").classList.add("hidden");
  $("share-publish").textContent = w.share_publish;
  $("share-guidelines").textContent = w.share_guidelines;
  $("share-open").textContent = w.share_open;
  $("share-discussions").textContent = w.share_discussions;
  $("share-close").textContent = w.close;
  if (!$("share").open) $("share").showModal();
}

async function copyShareEntry() {
  const area = $("share-entry");
  try { await navigator.clipboard.writeText(area.value); } catch { area.focus(); area.select(); return; }  // selected: Ctrl+C
  $("share-note").textContent = state.words.share_copied;
}

async function copyShareCredit() {
  const box = $("share-credit");
  try { await navigator.clipboard.writeText(box.value); } catch { box.focus(); box.select(); return; }  // selected: Ctrl+C
  $("share-note").textContent = state.words.share_credit_copied;
}

async function publishMod() {
  try { await api().publish_mod(); } catch (err) { problem(err); return; }
  $("share-published").textContent = state.words.share_published;
  $("share-published").classList.remove("hidden");
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
// Its two ways in, above the kinds (the owner, 2026-10-04: "new unit, import, or adjust an existing one"): Change a
// unit (pick it: its values, Open in Blender) or New unit (pick the unit to start from: its New unit form opens, and
// the new unit's page opens at Import model). Ammunition has no model, so New unit leaves it out.
const STARTS = [["change", "start_change", "tip_start_change"], ["new", "start_new", "tip_start_new"]];

function renderStart() {
  const w = state.words;
  $("unit-start").replaceChildren(...STARTS.map(([key, word, tip]) => {
    const b = el("button", { type: "button", className: "start", textContent: w[word], title: w[tip] });
    b.setAttribute("aria-pressed", String(state.start === key));
    b.addEventListener("click", () => setStart(key));
    return b;
  }));
  $("start-help").textContent = w.start_new_help;
  $("start-help").classList.toggle("hidden", state.start !== "new");
  if ($("pick")) $("pick").textContent = state.start === "new" ? w.pick_unit_new : w.pick_unit;
}

function setStart(key) {
  if (state.start === key) return;
  state.start = key;
  if (key === "new" && state.kind === "ammo") { state.kind = "all"; state.group = "all"; }
  renderStart();
  renderChips();
  refreshList();
  if (state.page) showUnit(state.page.address, state.page.via);  // the unit shown: with its New unit form, or without
}

function renderChips() {
  const w = state.words;
  const kinds = state.start === "new" ? KINDS.filter((k) => k !== "ammo") : KINDS;
  $("kinds").replaceChildren(...kinds.map((k) => {
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

// The second sort, under the kind: for Ground, Infantry and Air the game's own types ("Light Tank", "Heavy Bomber",
// "Armored Recon": StudioApi.units' `types`, picked as TYPE_PICK + the name); for buildings, ammunition and All, what
// they're for (a building's job, or the factory that builds a unit).
const TYPE_PICK = "type:";

function renderGroups(groups, types) {
  const w = state.words, pick = $("unit-group");
  const options = types.length ? types.map((t) => [TYPE_PICK + t, t]) : groups.map((g) => [g, w["group_" + g] || g]);
  pick.classList.toggle("hidden", !options.length);
  pick.title = types.length ? w.tip_unit_type : w.tip_group;
  pick.setAttribute("aria-label", pick.title);
  pick.replaceChildren(el("option", { value: "all", textContent: w.group_all }),
    ...options.map(([value, label]) => el("option", { value, textContent: label })));
  pick.value = options.some(([value]) => value === state.group) ? state.group : "all";
}

// A unit's or building's second line: with the code names, the name a player knows first ("ARMOR BASE"); then its
// country, its type (a building: what it's for, so a decoy says so), and its code name when names are shown.
function unitSub(u) {
  const w = state.words;
  const what = u.type || (u.kind === "buildings" ? w["group_" + u.group] || w.buildings : w[u.kind]);
  const known = state.lang === "base" && u.game_name && u.game_name !== u.name ? `${u.game_name} · ` : "";
  return known + `${u.nation_name} · ${what}` + (u.name !== u.base_name ? ` · ${u.base_name}` : "");
}

async function refreshList() {
  let res;
  try {
    res = await api().units(state.lang, state.kind, state.nation, state.search, state.group || "all");
    if ((state.group || "").startsWith(TYPE_PICK) && !(res.types || []).includes(state.group.slice(TYPE_PICK.length))) {
      state.group = "all";  // a type picked in another language or kind: show them all again
      res = await api().units(state.lang, state.kind, state.nation, state.search, "all");
    }
    state.edited = new Set(await api().edited());
  } catch (err) { problem(err); return; }
  $("count").textContent = state.words.units.replace("{n}", res.units.length);
  renderGroups(res.groups || [], res.types || []);
  $("unit-list").replaceChildren(...res.units.map((u) => {
    const sub = u.kind === "ammo"
      ? (u.nations.length ? u.nations.join(", ") + " · " : "") +
        (u.users.length ? fill(state.words.fired_by, { names: u.users.slice(0, 3).join(", ") +
          (u.users.length > 3 ? ", …" : "") }) : state.words.fired_by_nobody) +
        (u.name !== u.base_name ? ` · ${u.base_name}` : "")
      : unitSub(u);
    // the game's own line for it ("May field armored units and armored recon.") as its tooltip
    const open = state.start === "new" && !u.new ? state.words.tip_start_from : state.words.tip_open_unit;
    const tip = u.desc ? `${u.desc}\n${open}` : open;
    const b = el("button", { type: "button", title: tip },
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

// How far a weapon shoots (an ammo's range): a slider beside its number box, and about how far that is in metres (the
// game counts about 260 of its units to a metre, rusemod.nav.METRE). Ranges go from a few metres to the V2's 10 km,
// so a slider reaches 4 times the game's own value (further when more is set); the box takes any exact number.
const RANGE_PROPS = new Set(["PorteeMaximale", "PorteeMinimale"]);
const METRE = 260, RANGE_STEP = 13000;  // most of the game's ranges are whole 13,000s (50 m)

function rangeTop(game, now) {
  const most = Math.max(4 * (game || 0), now || 0, 20 * RANGE_STEP);
  return Math.ceil(most / RANGE_STEP) * RANGE_STEP;
}

function metres(v) {
  return fill(state.words.range_metres, { m: Math.round(v / METRE).toLocaleString() });
}

// A slider for a range's number box: moving it fills the box and says the metres, letting go saves (the box's own
// change event); typing in the box moves it. Returns { node, sync }: sync after the box is set from code.
function rangeSlider(box, game) {
  const w = state.words;
  const slider = el("input", { type: "range", min: "0", step: String(METRE), disabled: box.disabled,
    title: w.tip_range_slider });
  slider.setAttribute("aria-label", w.range_slider);
  const far = el("span", { className: "muted small range-m", title: w.tip_range_box });
  const sync = () => {
    const v = Number(box.value);
    if (box.value.trim() === "" || !Number.isFinite(v)) return;
    slider.max = String(rangeTop(game, v));
    slider.value = String(v);
    far.textContent = metres(v);
  };
  slider.addEventListener("input", () => { box.value = slider.value; far.textContent = metres(Number(slider.value)); });
  slider.addEventListener("change", () => box.dispatchEvent(new Event("change")));
  box.addEventListener("input", sync);
  box.addEventListener("change", sync);
  sync();
  return { node: el("span", { className: "range" }, slider, far), sync };
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
  const ranged = RANGE_PROPS.has(r.prop) && !r.list && r.type !== "bool";
  if (ranged) boxes[0].title = w.tip_range_box;
  // A list whose values are all the same (a unit's five prices, one per battle date) gets one box that changes them
  // all, so a modder can't change one of five by accident; "set each" shows every box.
  let one = r.list && shown.length > 1 && r.type !== "bool" && shown.every((n) => n === shown[0])
    ? numberBox(r, shown[0], `${r.label} (${w.all_values.replace("{n}", shown.length)})`) : null;
  const holder = el("div", { className: "boxes" }, ...(one ? [one] : boxes));
  const slider = ranged ? rangeSlider(boxes[0], r.numbers[0]) : null;
  if (slider) holder.append(slider.node);
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
        if (slider) slider.sync();
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
      if (slider) slider.sync();
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
// an "Add" picker listing every flag, 0-104 (what it does, and who has it: the ones no unit carries say they do
// nothing in a unit's flags).
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
          (f.count ? ` (${fill(w.flag_count, { n: f.count })})` : "") }));  // no unit has it: it says it does nothing
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

// A weapon's range on its unit's page (api.set_range): a slider and a box. When other units fire the same ammo, the
// modder picks for whom: only this unit (the weapon gets its own copy of the ammo, as "Copy ammo" does) or all of them.
const rangeFor = new Map();  // weapon address -> "own" or "shared", kept while the Studio is open

function weaponRange(u, wp, redraw) {
  const w = state.words;
  const base = u.address.split(":")[0];
  const box = el("input", { type: "number", step: "any", inputMode: "decimal", value: String(wp.range),
    disabled: !state.mod, title: w.tip_range_box });
  box.setAttribute("aria-label", w.range);
  const slider = rangeSlider(box, wp.game_range);
  const line = el("div", { className: "weapon-range" },
    el("span", { className: "range-label", textContent: w.range, title: w.tip_range }), box, slider.node);
  const out = el("div", {}, line);
  const others = wp.firing.filter((f) => f.address !== base);
  if (wp.own_copy) out.append(el("div", { className: "muted small", textContent: w.range_own_copy }));
  else if (others.length) {
    const names = wp.firing.map((f) => f.name);
    const shown = names.length > 12 ? names.slice(0, 12).join(", ") + ", …" : names.join(", ");
    const choice = el("div", { className: "choice range-for", role: "radiogroup" }, el("span", { textContent: w.change_for }));
    const name = (wp.firing.find((f) => f.address === base) || { name: u.name }).name;
    for (const [mode, text, tip] of [["own", fill(w.only_unit, { name }), w.tip_range_only],
      ["shared", fill(w.range_all, { n: names.length }), fill(w.tip_range_all, { names: shown })]]) {
      const input = el("input", { type: "radio", name: `range-for-${wp.address}`, value: mode, title: tip,
        disabled: !state.mod, checked: (rangeFor.get(wp.address) || "own") === mode });
      input.addEventListener("change", () => rangeFor.set(wp.address, mode));
      choice.append(el("label", { title: tip }, input, " " + text));
    }
    out.append(choice);
  }
  const save = async (value, mode) => {
    try {
      const res = await api().set_range(u.address, wp.address, value, mode);
      await refreshMarks();
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
    redraw();
  };
  box.addEventListener("change", () => {
    const v = Number(box.value);
    const bad = box.value.trim() === "" || !Number.isFinite(v);
    box.setAttribute("aria-invalid", String(bad));
    if (!bad && v !== wp.range) save(v, wp.own_copy || !others.length ? "own" : rangeFor.get(wp.address) || "own");
  });
  if (wp.game_range !== null && wp.range !== wp.game_range) {
    line.classList.add("edited");
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_range_reset,
      disabled: !state.mod });
    undo.addEventListener("click", () => save(wp.game_range, "shared"));
    out.append(el("div", { className: "was" },
      el("span", { textContent: fill(w.was, { v: `${wp.game_range} (${metres(wp.game_range)})` }) }), undo));
  }
  return out;
}

// A unit's weapons and what each fires: one dropdown per weapon, listing every ammunition (the mod's copies first),
// and how far it shoots.
function weaponsGroup(u) {
  const w = state.words;
  const group = el("div", { className: "group hidden" }, el("h2", { textContent: w.weapons }));
  const draw = () => api().weapons(u.address, state.lang).then((res) => {
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
      const open = el("button", { type: "button", className: "link", textContent: w.open_ammo, title: w.tip_open_ammo });
      open.addEventListener("click", () => showUnit(pick.value));
      const was = el("div", { className: "was" });
      // the muzzle flash and sound this weapon plays (they follow the ammo: api.set_ammo)
      const shot = el("div", { className: "muted small", textContent: wp.shot ? fill(w.shot, { fx: wp.shot }) : "" });
      const cell = el("td", {}, el("div", { className: "boxes" }, pick, open), was, shot);
      if (wp.range !== null && wp.range !== undefined) cell.append(weaponRange(u, wp, draw));
      const tr = el("tr", { className: wp.edited ? "edited" : "" }, th, cell);
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
          await refreshMarks();
          say(w.saved.replace("{file}", saved.saved), "ok");
        } catch (err) { problem(err); }
        draw();  // its shot and its range follow the ammo
      });
      showWas(wp.edited);
      table.append(tr);
    });
    group.replaceChildren(el("h2", { textContent: w.weapons }), table,
      el("p", { className: "muted small", textContent: w.weapons_help }));
    group.classList.remove("hidden");
  }).catch(problem);
  draw();
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

// `opened`: the form shows at once (the Units tab's New unit way in). The box's openForm() opens it from elsewhere
// (the model box's "New unit from this one…").
function newUnitForm(u, opened) {
  const w = state.words;
  const open = el("button", { type: "button", className: "ghost" + (opened ? " hidden" : ""), textContent: w.new_unit,
    title: w.tip_new_unit });
  const form = el("form", { className: "new-unit" + (opened ? "" : " hidden") });
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
    el("p", { className: "small", textContent: fill(w.new_unit_next, { name: u.name }) }),
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
      state.focusModel = res.address;  // its page opens at Import model
      if (state.start === "new") { state.start = "change"; renderStart(); renderChips(); }  // made: now it's changed
      await refreshList();
      await showUnit(res.address);
      say(w.unit_made.replace("{name}", res.name), "ok");
    } catch (err) { problem(err); create.disabled = false; }
  });
  const box = el("div", { className: "copy" }, open, form);
  box.openForm = () => {
    if (form.classList.contains("hidden")) open.click();
    else name.focus();
    box.scrollIntoView({ block: "nearest", behavior: "smooth" });
  };
  if (opened) requestAnimationFrame(() => name.focus({ preventScroll: true }));
  return box;
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

// --- a unit's 3D model on its page, turning slowly until it's dragged (api.unit_preview: the game's model as a .glb
// from rusemod.gltf, made once per game build and kept in the cache). three.js comes from the internet, as for the
// Maps view (index.html). One renderer for every page, moved into the page shown. The mod's paint (what Bring back
// put in it) goes on in place of the game's picture; propeller discs (`<model>_propeller`) stay hidden, as in
// Blender: the game spins them with a shader of its own. ---
const uview = { gl: null, ask: 0 };

async function unitViewGl() {
  if (uview.gl) return uview.gl;
  const THREE = await import("three");
  const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
  const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(window.devicePixelRatio || 1);
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
  scene.add(new THREE.HemisphereLight(0xeef3f8, 0x4a4234, 2.2));
  const sun = new THREE.DirectionalLight(0xfff4e0, 2.4);
  sun.position.set(3, 5, 4);
  scene.add(sun, camera);
  camera.add(new THREE.DirectionalLight(0xffffff, 0.8));  // a little light from where we look
  const controls = new OrbitControls(camera, renderer.domElement);
  Object.assign(controls, { enableDamping: true, autoRotate: true, autoRotateSpeed: 1.5, enablePan: true });
  controls.addEventListener("start", () => {  // dragged or zoomed: it stays where it's put
    controls.autoRotate = false;
    if (uview.gl.fit) uview.gl.fit.moved = true;
  });
  const model = new THREE.Group();
  const soft = el("canvas", { width: 128, height: 128 }), sctx = soft.getContext("2d");  // a shadow fading out
  const fade = sctx.createRadialGradient(64, 64, 0, 64, 64, 64);
  fade.addColorStop(0, "rgba(0, 0, 0, 0.55)");
  fade.addColorStop(0.55, "rgba(0, 0, 0, 0.3)");
  fade.addColorStop(1, "rgba(0, 0, 0, 0)");
  sctx.fillStyle = fade;
  sctx.fillRect(0, 0, 128, 128);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(2, 2),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(soft), transparent: true, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2;
  scene.add(model, shadow);
  uview.gl = { THREE, renderer, scene, camera, controls, model, shadow, loader: new GLTFLoader(),
    pictures: new THREE.TextureLoader() };
  const loop = () => {
    requestAnimationFrame(loop);
    const host = renderer.domElement.parentElement;
    if (!host || !host.isConnected || host.offsetParent === null) return;  // another page or the Maps tab
    const wd = host.clientWidth, ht = host.clientHeight, size = renderer.getSize(new THREE.Vector2());
    if (wd && ht && (size.x !== wd || size.y !== ht)) {
      renderer.setSize(wd, ht);
      camera.aspect = wd / ht;
      camera.updateProjectionMatrix();
      if (uview.gl.fit && !uview.gl.fit.moved) unitViewFit(uview.gl);  // not zoomed yet: keep it all in view
      placeCardFrame();
    }
    controls.update();
    renderer.render(scene, camera);
  };
  loop();
  return uview.gl;
}

// The camera about as far from the model as it takes to see all of it (its bounding sphere, which is roomy round a
// box: 0.85 of that distance still keeps a turning plane's wings in) in the view's narrower angle, looking from
// where it looks now.
function unitViewFit(gl) {
  const { centre, radius } = gl.fit;
  const tan = Math.tan(gl.camera.fov * Math.PI / 360);
  let half = Math.atan(tan * Math.min(1, gl.camera.aspect));
  const host = gl.renderer.domElement.parentElement, f = uview.frame;
  let room = 0.85;
  if (f && f.el.isConnected && host && host.clientWidth && host.clientHeight) {  // a card: fit inside its frame,
    const r = cardRect(host.clientWidth, host.clientHeight, f.aspect);         // filling it as the game's cards do
    half = Math.min(Math.atan(tan * r.h / host.clientHeight),
      Math.atan(tan * (host.clientWidth / host.clientHeight) * r.w / host.clientWidth));
    room = 0.62;
  }
  const away = gl.camera.position.clone().sub(gl.controls.target);
  if (away.lengthSq() < 1e-12) away.set(0.85, 0.42, 0.85);
  gl.controls.target.copy(centre);
  gl.camera.position.copy(centre).add(away.normalize().multiplyScalar(radius / Math.sin(half) * room));
  gl.controls.update();
}

// --- the unit's card (its picture in the build menu): what's inside the dashed frame on the 3D view, taken at the
// card's own size over a backdrop like the game's cards (a hazy sky, far hills, sandy ground), and saved in the mod
// (api.look_card; the build writes it as the game stores its cards, rusemod.unitlook.make_picture). ---
function cardRect(wd, ht, aspect) {  // the frame: as big as fits with a small margin, centred
  const room = 0.88;
  let fw = wd * room, fh = fw / aspect;
  if (fh > ht * room) { fh = ht * room; fw = fh * aspect; }
  return { x: (wd - fw) / 2, y: (ht - fh) / 2, w: fw, h: fh };
}

function placeCardFrame() {
  const f = uview.frame;
  if (!f || !f.el.isConnected) return;
  const host = f.el.parentElement, r = cardRect(host.clientWidth, host.clientHeight, f.aspect);
  Object.assign(f.el.style, { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px` });
}

function cardBackdrop(ctx, wd, ht) {
  ctx.save();
  const sky = ctx.createLinearGradient(0, 0, 0, ht * 0.62);
  sky.addColorStop(0, "#aebdca");
  sky.addColorStop(1, "#dde2e5");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, wd, ht);
  ctx.filter = "blur(2px)";
  ctx.fillStyle = "rgba(120, 132, 146, 0.75)";  // far hills, hazy
  ctx.beginPath();
  ctx.moveTo(0, ht * 0.56);
  for (let x = 0; x <= wd; x += 4) {
    const t = x / wd;
    ctx.lineTo(x, ht * (0.47 - 0.08 * Math.sin(t * 5.1 + 0.6) * Math.sin(t * 2.3 + 1.1) - 0.03 * Math.sin(t * 17)));
  }
  ctx.lineTo(wd, ht * 0.6);
  ctx.lineTo(0, ht * 0.6);
  ctx.fill();
  const ground = ctx.createLinearGradient(0, ht * 0.52, 0, ht);
  ground.addColorStop(0, "#d2c4a8");
  ground.addColorStop(1, "#a88f6c");
  ctx.fillStyle = ground;
  ctx.fillRect(0, ht * 0.55, wd, ht * 0.45);
  ctx.restore();
}

// What's inside the frame now, as a PNG data address at the card's size (drawn twice as big, then halved: smoother).
function cardShot(card) {
  const gl = uview.gl, { THREE } = gl, host = gl.renderer.domElement.parentElement;
  const wd = host.clientWidth, ht = host.clientHeight, r = cardRect(wd, ht, card.width / card.height);
  const shot = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
  try {
    shot.setPixelRatio(1);
    shot.setSize(card.width * 2, card.height * 2, false);
    const cam = gl.camera.clone();
    cam.aspect = wd / ht;
    cam.setViewOffset(wd, ht, r.x, r.y, r.w, r.h);
    shot.render(gl.scene, cam);
    const c = el("canvas", { width: card.width, height: card.height }), ctx = c.getContext("2d");
    cardBackdrop(ctx, card.width, card.height);
    ctx.drawImage(shot.domElement, 0, 0, card.width, card.height);
    return c.toDataURL("image/png");
  } finally {
    shot.dispose();
    shot.forceContextLoss();
  }
}

function cardRow(u, card) {
  const w = state.words;
  const thumb = el("img", { className: "card-thumb", src: card.url, alt: w.card_now, title: w.card_now });
  const use = el("button", { type: "button", textContent: w.card_use, title: w.tip_card_use });
  const reset = el("button", { type: "button", className: "ghost", textContent: w.card_reset, title: w.tip_card_reset });
  const show = (c) => {
    thumb.src = c.url;
    reset.classList.toggle("hidden", !c.own);
  };
  show(card);
  use.addEventListener("click", async () => {
    if (!state.mod) { say(w.no_mod, "error"); return; }
    use.disabled = true;
    try {
      const r = await api().look_card(u.address, cardShot(card));
      show(r.card);
      say(r.message, "ok");
    } catch (err) { problem(err); } finally { use.disabled = false; }
  });
  reset.addEventListener("click", async () => {
    try { const r = await api().look_card_reset(u.address); show(r.card); say(r.message, "ok"); }
    catch (err) { problem(err); }
  });
  return el("div", { className: "card-row" }, thumb,
    el("div", {}, el("p", { className: "muted small", textContent: w.card_note }), el("div", { className: "actions" }, use, reset)));
}

function unitView(u) {
  const w = state.words;
  const status = el("div", { className: "view-note", textContent: w.unit_view_loading });
  const host = el("div", { className: "unit-view" }, status);
  const box = el("div", { className: "group unit-view-box" }, el("h2", { textContent: w.unit_view }), host);
  const load = async () => {
    const ask = ++uview.ask;
    const info = await api().unit_preview(u.address);
    if (ask !== uview.ask) return;
    if (!info.models || !info.models.length) {  // no model the Studio can show: the values take the whole page
      const page = box.closest(".unit-page");
      if (page) page.classList.add("no-model");
      box.remove();
      return;
    }
    const gl = await unitViewGl();
    if (ask !== uview.ask) return;
    const { THREE } = gl;
    const loaded = await Promise.all(info.models.map((m) => gl.loader.loadAsync(m.url)));
    const paint = await Promise.all(Object.entries(info.paint || {}).map(async ([tex, url]) => {
      const t = await gl.pictures.loadAsync(url);
      Object.assign(t, { flipY: false, colorSpace: THREE.SRGBColorSpace, wrapS: THREE.RepeatWrapping,
        wrapT: THREE.RepeatWrapping });
      return [tex, t];
    }));
    if (ask !== uview.ask) return;
    for (const old of [...gl.model.children]) {  // the last page's model
      gl.model.remove(old);
      old.traverse((o) => {
        if (!o.isMesh) return;
        o.geometry.dispose();
        for (const m of [].concat(o.material)) { if (m.map) m.map.dispose(); m.dispose(); }
      });
    }
    const pictureOf = Object.fromEntries(paint), shown = [];
    let painted = 0;
    for (const g of loaded) {
      g.scene.traverse((o) => {
        if (/_propeller$/.test(o.name)) o.visible = false;
      });
      g.scene.traverse((o) => {
        if (!o.isMesh) return;
        let seen = true;
        for (let p = o; p; p = p.parent) if (!p.visible) seen = false;
        if (seen) shown.push(o);
        for (const m of [].concat(o.material)) {
          const t = pictureOf[m.userData && m.userData.rusemod_texture];
          if (t) { m.map = t; m.needsUpdate = true; painted++; }
        }
      });
      gl.model.add(g.scene);
    }
    gl.model.updateMatrixWorld(true);
    const bounds = new THREE.Box3();
    for (const o of shown) {
      o.geometry.computeBoundingBox();
      bounds.union(o.geometry.boundingBox.clone().applyMatrix4(o.matrixWorld));
    }
    const centre = bounds.getCenter(new THREE.Vector3()), size = bounds.getSize(new THREE.Vector3());
    const reach = Math.max(size.length(), 0.01);
    gl.shadow.position.set(centre.x, bounds.min.y + reach * 0.002, centre.z);
    gl.shadow.scale.setScalar(Math.max(size.x, size.z) * 0.62);
    gl.camera.near = reach / 100;
    gl.camera.far = reach * 20;
    gl.camera.updateProjectionMatrix();
    gl.camera.position.set(centre.x + 0.85, centre.y + 0.42, centre.z + 0.85);  // from the front corner, a bit above
    gl.controls.target.copy(centre);
    gl.controls.minDistance = reach * 0.15;
    gl.controls.maxDistance = reach * 5;
    gl.controls.autoRotate = true;
    host.prepend(gl.renderer.domElement);
    status.textContent = painted ? w.unit_view_paint : "";
    for (const old of host.querySelectorAll(".hint, .card-frame")) old.remove();  // a reload after Bring back
    host.append(el("div", { className: "hint", textContent: w.unit_view_hint }));
    const oldRow = box.querySelector(".card-row");
    if (oldRow) oldRow.remove();
    uview.frame = null;
    if (info.card) {
      const frame = el("div", { className: "card-frame" }, el("span", { textContent: w.card_frame }));
      host.append(frame);
      uview.frame = { el: frame, aspect: info.card.width / info.card.height };
      placeCardFrame();
      box.append(cardRow(u, info.card));
    }
    gl.fit = { centre, radius: reach / 2, moved: false };
    unitViewFit(gl);  // after the frame is in: a card's model starts out fitting inside it
  };
  box.reload = () => load().catch((err) => { status.textContent = (err && err.message) || String(err); });
  box.reload();
  return box;
}

// --- a unit's look: its model out to Blender, the paint back into the mod (api.look, look_open, look_bring_back,
// choose_blender, get_blender; rusemod.unitlook). Blender is a program of its own: the Studio opens it, with the
// unit loaded and each texture linked to its picture, and takes back what was painted there (Bring back asks
// Blender to save it first, rusemod.blender.ask_to_save). `brought` is called after paint came back. A game unit's
// model can't be swapped: a model of one's own goes on a new unit, so a game unit's box says so, and `startNew` (its
// page's New unit form, when it can be copied) makes one.
function lookBox(u, brought, startNew) {
  const w = state.words;
  const address = u.address;
  const body = el("div", { className: "muted small", textContent: w.look_working });
  const box = el("div", { className: "group look" }, el("h2", { textContent: w.unit_look, title: w.tip_unit_look }), body);
  const draw = (info) => {
    if (!info.models || !info.models.length) { box.remove(); return; }
    const parts = [];
    if (!info.blender) {
      const get = el("button", { type: "button", textContent: w.look_get_blender, title: w.tip_look_get_blender });
      get.addEventListener("click", () => api().get_blender().catch(problem));
      const choose = el("button", { type: "button", className: "ghost", textContent: w.look_choose_blender,
        title: w.tip_look_choose_blender });
      choose.addEventListener("click", async () => {
        try {
          const r = await api().choose_blender();
          if (r.message) say(r.message, "error");
          draw(await api().look(address));
        } catch (err) { problem(err); }
      });
      parts.push(el("p", { textContent: w.look_no_blender }), el("div", { className: "actions" }, get, choose));
    } else {
      const open = el("button", { type: "button", textContent: w.look_open, title: w.tip_look_open });
      const back = el("button", { type: "button", textContent: w.look_back, title: w.tip_look_back,
        disabled: !info.opened || !state.mod });
      open.addEventListener("click", async () => {
        open.disabled = true;
        say(w.look_opening);
        try { const r = await api().look_open(address); say(r.message, "ok"); draw(r); }
        catch (err) { problem(err); } finally { open.disabled = false; }
      });
      back.addEventListener("click", async () => {
        back.disabled = true;
        say(w.look_bringing);
        try {
          const r = await api().look_bring_back(address);
          say(r.message, r.brought.length ? "ok" : "");
          draw(r);
          if (r.brought.length && brought) brought();
        } catch (err) { problem(err); } finally { back.disabled = !state.mod; }
      });
      parts.push(el("p", { className: "muted small", textContent: w.look_how }),
        el("div", { className: "actions" }, open, back));
      if (!state.mod) parts.push(el("p", { className: "notice", textContent: w.no_mod }));
    }
    if (info.painted && info.painted.length) {
      parts.push(el("p", { className: "small", textContent: fill(w.look_painted, { n: info.painted.length }) }));
    }
    let model = null;
    if (info.new_unit && state.mod) parts.push(model = modelBox(address, info, draw, brought));
    else if (!info.new_unit && u.can_copy && u.editable) parts.push(modelWant(startNew));  // (no mod: no startNew)
    body.className = "new-unit";
    body.replaceChildren(...parts);
    if (model && state.focusModel === address) {  // just made: show where its model goes
      state.focusModel = null;
      model.classList.add("lit");
      model.pick.focus({ preventScroll: true });
      keepInSight(model);
    }
  };
  api().look(address).then(draw).catch((err) => { body.textContent = (err && err.message) || String(err); });
  return box;
}

// --- a new unit's own model (api.model_import, model_import_remove; rusemod.modelin, rusemod.unitmodel): a .3ds or
// .glb from any 3D tool, fitted to the copied unit (its length times Size, its turret on the copy's turret point) and
// kept in the mod as files/models/<the unit's name>.glb; the build puts it in the game beside the copied model ---
function modelBox(address, info, draw, changed) {
  const w = state.words;
  const own = info.own_model;
  const size = el("input", { type: "number", min: "0.2", max: "5", step: "0.05", value: "1", className: "model-size",
    title: w.tip_model_size });
  const pick = el("button", { type: "button", textContent: own ? w.model_import_again : w.model_import,
    title: w.tip_model_import });
  pick.addEventListener("click", async () => {
    pick.disabled = true;
    say(w.model_importing);
    try {
      const r = await api().model_import(address, null, Number(size.value) || 1);
      if (r.model) {  // (none: the file picker was closed)
        say(fill(w.model_done, { file: r.model.file || "" }), "ok");
        if (changed) changed();
      }
      draw(r);
    } catch (err) { problem(err); } finally { pick.disabled = false; }
  });
  const box = el("div", { className: "model-own" }, el("h3", { textContent: w.model_title }));
  if (own) {
    box.append(el("p", { className: "small", textContent: fill(w.model_own, { file: own.file || "",
      points: (own.vertices || 0).toLocaleString(), triangles: (own.triangles || 0).toLocaleString() }) }));
    const turret = Object.entries(own.parts || {}).filter(([, role]) => role !== "hull").map(([name]) => name);
    if (turret.length) box.append(el("p", { className: "muted small", textContent: fill(w.model_turret, { parts: turret.join(", ") }) }));
    if (own.missing && own.missing.length) {
      box.append(el("p", { className: "notice warn", textContent: fill(w.model_missing, { names: own.missing.join(", ") }) }));
    }
    const drop = el("button", { type: "button", className: "ghost", textContent: w.model_remove, title: w.tip_model_remove });
    drop.addEventListener("click", async () => {
      try { draw(await api().model_import_remove(address)); if (changed) changed(); } catch (err) { problem(err); }
    });
    box.append(el("div", { className: "actions" }, pick, el("label", { className: "small" }, w.model_size, " ", size), drop));
  } else {
    box.append(el("p", { className: "muted small", textContent: w.model_how }),
      el("div", { className: "actions" }, pick, el("label", { className: "small" }, w.model_size, " ", size)));
  }
  box.pick = pick;
  return box;
}

// A box in the unit's side column brought into sight (the side column and the page each scrolled as little as it
// takes), and kept there for a few seconds while the 3D view above it loads: it grows as it does.
function keepInSight(box) {
  const side = box.closest(".unit-side");
  const keep = () => { if (box.isConnected) box.scrollIntoView({ block: "nearest" }); };
  requestAnimationFrame(keep);
  if (!side || typeof ResizeObserver === "undefined") return;
  const watch = new ResizeObserver(keep);
  for (const part of side.children) watch.observe(part);
  setTimeout(() => watch.disconnect(), 4000);
}

// a game unit's page: where its own model would go, and the way there (a new unit from it)
function modelWant(startNew) {
  const w = state.words;
  const go = el("button", { type: "button", textContent: w.model_want_button, title: w.tip_model_want,
    disabled: !startNew });
  if (startNew) go.addEventListener("click", startNew);
  return el("div", { className: "model-own" }, el("h3", { textContent: w.model_title }),
    el("p", { className: "muted small", textContent: w.model_want }), el("div", { className: "actions" }, go));
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
    // with the code names, the name a player knows; and the game's own line for it, as on its card in the game
    ...(state.lang === "base" && u.game_name && u.game_name !== u.name
      ? [el("div", { className: "game-name", textContent: u.game_name })] : []),
    ...(u.desc ? [el("p", { className: "unit-desc", textContent: u.desc })] : []),
    el("div", { className: "address" }, el("code", { textContent: u.address }), copy),
    el("div", { className: "meta", textContent: u.class })];
  const head = parts.length;  // the name, address and class: above the page's columns
  if (u.new) parts.push(copyNotice(u));
  let copyForm = null;  // New unit…: open at once when the Units tab's way in is New unit
  if (!u.editable) parts.push(el("p", { className: "notice", textContent: w[u.why_not] || u.why_not }));
  else if (!state.mod) parts.push(el("p", { className: "notice", textContent: w.no_mod }));
  else if (u.can_copy) parts.push(copyForm = newUnitForm(u, state.start === "new"));
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
  if (u.named || u.new) {  // a unit: its model beside its values, with the Blender buttons under it
    const view = unitView(u);
    const side = el("aside", { className: "unit-side" }, view,
      lookBox(u, () => view.reload(), copyForm && copyForm.openForm));
    $("detail").replaceChildren(...parts.slice(0, head),
      el("div", { className: "unit-page" }, el("div", { className: "unit-main" }, ...parts.slice(head)), side));
    return;
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
    done(j.state === "done", j.message, j);
  };
  tick();
}

async function testInGame() {
  const button = $("test");
  if (button.dataset.running === "1") return;  // one build at a time: a double click started two (2026-09-30)
  button.disabled = true;
  button.dataset.running = "1";
  if (!await checkMod()) {
    button.dataset.running = "0";
    button.disabled = !state.mod;
    say(state.words.check_stop, "error");
    return;
  }
  const log = $("test-log");
  log.textContent = "";
  $("test-problems").replaceChildren();
  $("test-problems").classList.add("hidden");
  $("test-panel").classList.remove("hidden");
  if (state.view === "settings") renderBackup();  // a restore waits for the test's copy
  const finish = (ok, message, j) => {
    button.dataset.running = "0";
    button.disabled = !state.mod;
    if (state.view === "settings") renderBackup();
    if (message) say(message, ok ? "ok" : "error");
    // mistakes in the mods: each one listed with its fix, not the troubleshooter (it can't fix a mod)
    if (!ok && j && j.errors && j.errors.length) showTestProblems();
    else if (!ok) offerTroubleshoot();
  };
  try {
    const { job } = await api().test_in_game();
    follow(job, log, finish);
  } catch (err) { problem(err); finish(false); }
}

// A test the build stopped: its mistakes at the top of the log, each with what fixes it (StudioApi.test_problems and
// test_fix: a team spawn on a BATTLES map made neutral or taken out, a road that joins nothing taken out)
async function showTestProblems() {
  const w = state.words, box = $("test-problems");
  let res;
  try { res = await api().test_problems(); } catch (err) { problem(err); return; }
  const list = res.problems || [];
  if (!list.length) { offerTroubleshoot(); return; }
  const labels = { spawn_neutral: [w.test_fix_neutral, w.tip_test_fix_neutral],
    spawn_remove: [w.test_fix_remove_spawn, w.tip_test_fix_remove_spawn],
    spawns_neutral_all: [w.test_fix_neutral_all, w.tip_test_fix_neutral_all],
    spawns_remove_all: [w.test_fix_remove_all, w.tip_test_fix_remove_all],
    road_remove: [w.test_fix_remove_road, w.tip_test_fix_remove_road] };
  box.replaceChildren(el("p", { className: "test-problems-title", textContent: fillText(w.test_problems_title, { n: list.length }) }),
    ...list.map((p) => {
      const row = el("div", { className: "check-row" }, el("span", { textContent: p.text }));
      if (p.mod) row.append(el("span", { className: "muted small", textContent: fillText(w.test_in_mod, { mod: p.mod }) }));
      if (!p.fixes.length) row.append(el("span", { className: "muted small", textContent: w.test_no_fix }));
      for (const fix of p.fixes) {
        const [label, tip] = labels[fix.kind] || [fix.kind, ""];
        const b = el("button", { type: "button", className: "small", textContent: fillText(label, { n: fix.road ?? fix.count }), title: tip || "" });
        b.addEventListener("click", async () => {
          for (const other of row.querySelectorAll("button")) other.disabled = true;  // one fix per mistake
          try {
            const done = await api().test_fix(fix);
            row.classList.add("fixed");
            say(fillText(w.test_fixed, { done: done.done }), "ok");
            if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();  // the map shows the change
          } catch (err) { problem(err); for (const other of row.querySelectorAll("button")) other.disabled = false; }
        });
        row.append(b);
      }
      return row;
    }));
  box.classList.remove("hidden");
}

// The test's log and its message, for a bug report or Discord
async function copyTestLog() {
  const text = $("test-log").textContent + ($("status").firstChild ? "\n" + $("status").firstChild.textContent : "");
  try { await navigator.clipboard.writeText(text); } catch {
    const box = el("textarea", { value: text, readOnly: true, className: "sr-only" });
    document.body.append(box);
    box.select();
    const copied = document.execCommand("copy");
    box.remove();
    if (!copied) { say(state.words.test_copy_failed, "error"); return; }
  }
  say(state.words.doc_copied, "ok");
}

// --- the troubleshooter (StudioApi.troubleshoot, rusemod.doctor): what can stop a test, checked in one go, each
// finding with a fix button when the app can run one; the report goes into a bug report or on Discord ---
const DOC_MARKS = { ok: "✔︎", info: "ℹ︎", warn: "⚠︎", fail: "✖︎" };  // ︎: drawn as text, not emoji
let doctorReport = "";

// A failed test: a link to the troubleshooter beside its message (a game left running from the copy, or a leftover
// copy Windows won't delete, stopped every second test for a player, 2026-09-30)
function offerTroubleshoot() {
  const w = state.words;
  const link = el("button", { type: "button", className: "link", textContent: w.doc_troubleshoot_link, title: w.doc_intro });
  link.addEventListener("click", openDoctor);
  const close = $("status").querySelector(".status-close");  // the × stays last
  if (close) close.before(" ", link); else $("status").append(" ", link);
}

function openDoctor() {
  const w = state.words, box = $("doctor");
  $("doctor-title").textContent = w.doc_title;
  $("doctor-intro").textContent = w.doc_intro;
  $("doctor-again").textContent = w.doc_again;
  $("doctor-copy").textContent = w.doc_copy;
  $("doctor-close").textContent = w.doc_close;
  doctorNote("");
  if (!box.open) box.showModal();
  runDoctor();
}

function doctorNote(text, ok) {
  const note = $("doctor-note");
  note.textContent = text || "";
  note.className = "small " + (ok ? "ok-text" : "error-text");
}

async function runDoctor() {
  const w = state.words, list = $("doctor-list");
  $("doctor-again").disabled = $("doctor-copy").disabled = true;
  list.replaceChildren(el("li", { className: "muted", textContent: w.doc_checking }));
  try {
    const res = await api().troubleshoot();
    doctorReport = res.report;
    list.replaceChildren(...res.findings.map(findingRow));
    $("doctor-copy").disabled = false;
  } catch (err) {
    list.replaceChildren();
    doctorNote((err && err.message) || String(err), false);
  }
  $("doctor-again").disabled = false;
}

function findingRow(f) {
  const w = state.words;
  const row = el("li", { className: "doc-row " + f.level },
    el("span", { className: "doc-mark", textContent: DOC_MARKS[f.level] || "•" }),
    el("span", { className: "doc-say", textContent: fill(w[f.say] || f.say, f.data) }));
  if (f.fix) {
    const button = el("button", { type: "button", className: "small", textContent: w["doc_fix_" + f.fix] || f.fix });
    button.addEventListener("click", () => fixFinding(f.fix));
    row.append(button);
  }
  return row;
}

async function fixFinding(action) {
  const w = state.words;
  for (const b of $("doctor-list").querySelectorAll("button")) b.disabled = true;
  try {
    if (action === "choose_game") {  // Settings' own "Choose folder…"
      const g = await chooseGame();
      doctorNote(g.message, false);
    } else {
      const res = await api().troubleshoot_fix(action);
      const left = res.left || [];
      doctorNote(left.length ? fill(w.doc_fix_left, { left: left.join("; ") }) : fill(w.doc_fixed, { done: res.done }),
        !left.length);
    }
  } catch (err) { doctorNote((err && err.message) || String(err), false); }
  await runDoctor();
}

async function copyReport() {
  try {
    await navigator.clipboard.writeText(doctorReport);
  } catch (err) {  // a window that refuses the clipboard call: the old way, from a box inside the dialog
    const box = el("textarea", { value: doctorReport, readOnly: true, className: "sr-only" });
    $("doctor").append(box);
    box.focus();
    box.select();
    const copied = document.execCommand("copy");
    box.remove();
    $("doctor-copy").focus();
    if (!copied) { doctorNote((err && err.message) || String(err), false); return; }
  }
  doctorNote(state.words.doc_copied, true);
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
    // the panel shows on the Units tab only: the status line says it's building, and how it ended, on every tab
    say(state.words.index_building);
    follow(job, log, async (ok, message) => {
      if (ok) {
        $("no-index").classList.add("hidden");
        await setLanguage(state.lang);
        say(state.words.index_ready);
      } else {
        button.disabled = false;
        say(message, "error");
      }
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
  $("pick-mod").classList.toggle("hidden", view === "maps");  // the Units tab edits a mod, the Maps tab a map
  $("pick-map").classList.toggle("hidden", view !== "maps");
  // "No game index yet" (and the index's build, a minute or more) covers the Units tab only: the Maps tab and
  // Settings (where the installer's clean backup shows how far it is) can be used meanwhile
  $("no-index").classList.toggle("off-tab", view !== "units");
  if (view === "settings") { renderSettings(); loadBackup(); return; }
  if (view !== "maps") return;
  const open = () => window.MapView.open(api(), state.words, state.lang).catch(problem);
  if (window.MapView) open();
  else window.addEventListener("mapview-ready", open, { once: true });
}

// Duplicate map (maps.js) made a new map: it may have made a map project for it too, which the header's menu shows
window.addEventListener("map-duplicated", async (e) => {
  try { useMods(await api().mods("map")); } catch (err) { problem(err); }
  say(e.detail.text, "ok");
});
// Delete map (maps.js) sent a new map to the Recycle Bin: the status line says so
window.addEventListener("map-deleted", (e) => say(e.detail.text, "ok"));

// --- "Choose your language" (rusemod.uilang.LanguageCalls): opens by itself until the player has picked a language
// there (the Studio used to start on the code names, and a French player stayed on them, not knowing it speaks
// French), then from the language button at the top. Each language is shown in its own words, the screen's title in
// all of them, and the one the game is set to in Steam (else the PC's) is marked; the code names are one link below ---
let langPick = null;  // while open: { first, suggested, from, own: {code: that language's words}, done }

async function openLangPick(first) {
  let choice = { suggested: state.lang, from: "default", chosen: true };
  try { choice = await api().language_choice(); } catch { if (first) return; }  // an older back end: the button only
  if (first && choice.chosen) return;
  const own = {};
  await Promise.all(state.languages.filter((l) => l.code !== "base").map(async (l) => {
    try { own[l.code] = await api().strings(l.code); } catch { own[l.code] = {}; }
  }));
  await new Promise((done) => {
    langPick = { first, suggested: choice.suggested, from: choice.from, own, done };
    renderLangPick();
    const pick = $("lang-pick-list").querySelector(".suggested") || $("lang-pick-list").querySelector("button");
    if (pick) pick.focus();
  });
}

function closeLangPick() {
  const p = langPick;
  langPick = null;
  renderLangPick();
  if (p) p.done();
}

async function pickLanguage(code) {
  await setLanguage(code);
  Promise.resolve().then(() => api().set_pref("lang_chosen", true)).catch(() => {});
  closeLangPick();
}

function renderLangPick() {
  const p = langPick, w = state.words;
  $("lang-pick").classList.toggle("hidden", !p);
  if (!p) return;
  $("lang-pick-title").textContent = w.lang_pick_title;
  $("lang-pick-help").textContent = w.lang_pick_help;
  const titles = new Set(Object.values(p.own).map((o) => o.lang_pick_title).filter(Boolean));
  titles.delete(w.lang_pick_title);
  $("lang-pick-all").textContent = [...titles].join(" · ");
  const close = $("lang-pick-close");
  close.classList.toggle("hidden", p.first);  // the first time a language is picked: one click, and it's done
  close.title = w.lang_pick_close;
  close.setAttribute("aria-label", w.lang_pick_close);
  $("lang-pick-list").replaceChildren(...state.languages.filter((l) => l.code !== "base").map((l) => {
    const marked = l.code === p.suggested && p.from !== "default", theirs = p.own[l.code] || {};
    const b = el("button", { type: "button", className: "lang-choice" + (marked ? " suggested" : "")
      + (l.code === state.lang ? " current" : ""), lang: l.code === "us" ? "en" : l.code });
    b.setAttribute("aria-pressed", String(l.code === state.lang));
    b.append(el("span", { className: "lang-native", textContent: l.name }));
    // why it's marked, in that language's own words: the player reads it even before the screen speaks it
    if (marked) b.append(el("small", { textContent: p.from === "steam" ? theirs.lang_from_steam : theirs.lang_from_pc }));
    b.addEventListener("click", () => pickLanguage(l.code).catch(problem));
    return b;
  }));
  const base = $("lang-pick-base");
  base.textContent = w.lang_code_names;
  base.classList.toggle("current", state.lang === "base");
}

// --- Settings: one entry per section (its words are set_<id>_title / _help); a new setting is one more entry and
// its section in index.html. What they change is kept by the app (settings.json), not by the window.
const SETTINGS = [  // the language isn't here: it has its own button at the top ("Choose your language")
  { id: "keys", render() { if (window.MapView && window.MapView.renderKeysPanel) window.MapView.renderKeysPanel(api(), state.words); } },
  { id: "game", async render() {
    const w = state.words, g = await api().game_folder();
    $("set-game-path").textContent = g.message || (g.path ? fill(w.set_game_path, { path: g.path }) : w.set_game_none);
    $("set-game-change").textContent = w.set_game_change;
  } },
  { id: "backup", render() { renderBackup(); } },  // loaded each time Settings opens (loadBackup)
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
    $("help-troubleshoot").textContent = w.doc_button;
    $("help-troubleshoot").title = w.doc_intro;
  } },
];

// The game folder chosen by hand: Settings' "Choose folder…", and the troubleshooter's fix when R.U.S.E. wasn't found
async function chooseGame() {
  const g = await api().choose_game_folder();
  renderSettings();
  loadBackup();  // another game folder: its own backups
  if (g.message) $("set-game-path").textContent = g.message;
  return g;
}

// --- the clean game backup (rusemod.backup through api.backup_*): made while the game is clean, then a check of the
// game's files against it, and a restore of what other mod managers or hand edits changed. The only way the Studio
// writes into the game's own folder, and only after the modder says yes. Its jobs' lines are their progress ("37%";
// a restore checks first: "check 37%"), and a finished job brings what it found or did as its "result" ---
const BACKUP_LIST = 40;  // file names shown per kind (changed, missing, added); the rest are counted

function backupState() {
  return state.backup || (state.backup = { status: null, busy: "", phase: "", pct: "", found: null, note: "", ok: false,
    asking: false });
}

function errorText(err) {
  return (err && err.message) || String(err);
}

async function loadBackup() {
  const b = backupState();
  try { b.status = await api().backup_status(); } catch (err) { Object.assign(b, { note: errorText(err), ok: false }); }
  if (state.view === "settings") renderBackup();
}

function renderBackup() {
  const w = state.words, b = backupState(), s = b.status;
  let line = "";
  if (s && !s.found) line = w.set_game_none;
  else if (s && s.current) line = fill(w.backup_have, { build: s.current.build || "?", date: s.current.date, size: s.current.size_gb, path: s.current.path });
  else if (s && s.backups.length) line = fill(w.backup_other, { build: s.backups[0].build || "?", date: s.backups[0].date, now: s.build || "?" });
  else if (s) line = fill(w.backup_none, { need: s.need_gb, free: s.free_gb === null ? "?" : s.free_gb, drive: s.drive });
  $("backup-status").textContent = line;
  $("backup-status").className = "small " + (s && s.current ? "ok-text" : s && s.found && !s.enough ? "error-text" : "muted");
  const found = Boolean(s && s.found), ready = found && !b.busy && !b.asking, current = Boolean(s && s.current);
  const testing = $("test").dataset.running === "1";  // a Test in game builds its copy from the game's files
  $("backup-make").textContent = current ? w.backup_make_again : w.backup_make;
  $("backup-check").textContent = w.backup_check;
  $("backup-restore").textContent = w.backup_restore;
  $("backup-verify").textContent = w.backup_verify;
  $("backup-verify").title = w.backup_verify_tip;
  $("backup-deep-label").textContent = w.backup_deep;
  $("backup-make").disabled = !ready;
  $("backup-check").disabled = !ready || !current;
  $("backup-restore").disabled = !ready || !current || testing;
  $("backup-verify").disabled = !found || b.busy === "restore";
  $("backup-deep").disabled = Boolean(b.busy);
  const progress = { make: w.backup_making, check: w.backup_checking, restore: w.backup_restoring }[b.phase || b.busy];
  const note = $("backup-note");
  note.textContent = b.busy ? fill(progress, { pct: b.pct }) : b.note;
  note.className = "small " + (b.busy ? "muted" : b.ok ? "ok-text" : "error-text");
  renderBackupFiles(b.found);
}

function renderBackupFiles(found) {
  const w = state.words, holder = $("backup-files");
  holder.replaceChildren();
  if (!found) return;
  for (const [word, list] of [[w.backup_changed, found.changed], [w.backup_missing, found.missing], [w.backup_added, found.added]]) {
    if (!list.length) continue;
    const items = list.slice(0, BACKUP_LIST).map((f) => el("li", { textContent: f }));
    if (list.length > BACKUP_LIST) items.push(el("li", { className: "muted", textContent: fill(w.backup_more, { n: list.length - BACKUP_LIST }) }));
    const box = el("details", {}, el("summary", { textContent: fill(word, { n: list.length }) }), el("ul", {}, ...items));
    box.open = list.length <= 10;
    holder.append(box);
  }
}

// a question before something that changes files (making the backup again, a restore): Yes runs `onYes`
function askBackup(question, yesText, onYes) {
  const w = state.words, b = backupState();
  const yes = el("button", { type: "button", className: "ghost danger", textContent: yesText });
  const no = el("button", { type: "button", className: "ghost", textContent: w.cancel });
  const close = () => { b.asking = false; $("backup-ask").replaceChildren(); renderBackup(); };
  yes.addEventListener("click", () => { close(); onYes(); });
  no.addEventListener("click", close);
  b.asking = true;
  $("backup-ask").replaceChildren(el("div", { className: "sure" }, el("span", { className: "small", textContent: question }), yes, no));
  renderBackup();
  yes.focus();
}

// Runs one backup job and follows it; resolves with its result, or null when it failed (its message is the note)
async function runBackup(kind, call) {
  const b = backupState();
  Object.assign(b, { busy: kind, phase: "", pct: "", note: "", ok: false });
  renderBackup();
  let job;
  try { ({ job } = await call()); } catch (err) {
    Object.assign(b, { busy: "", note: errorText(err), ok: false });
    renderBackup();
    return null;
  }
  return new Promise((done) => {
    let seen = 0;
    const tick = async () => {
      let j;
      try { j = await api().job(job, seen); } catch (err) {
        Object.assign(b, { busy: "", note: errorText(err), ok: false });
        renderBackup();
        done(null);
        return;
      }
      seen = j.count;
      const last = j.lines[j.lines.length - 1];
      if (last) Object.assign(b, { phase: last.startsWith("check ") ? "check" : kind, pct: last.replace(/^check /, "") });
      if (j.state === "running") { renderBackup(); setTimeout(tick, 400); return; }
      Object.assign(b, { busy: "", phase: "" });
      if (j.state !== "done") Object.assign(b, { note: j.message, ok: false });
      renderBackup();
      done(j.state === "done" ? j.result || {} : null);
    };
    tick();
  });
}

async function makeBackup() {
  const w = state.words, s = backupState().status;
  const go = async (replace) => {
    const res = await runBackup("make", () => api().backup_make(replace));
    if (res) Object.assign(backupState(), { found: null, note: fill(w.backup_made, { files: res.files, size: res.size_gb }), ok: true });
    await loadBackup();
  };
  if (s && s.current) askBackup(fill(w.backup_replace_ask, { date: s.current.date }), w.backup_replace_yes, () => go(true));
  else go(false);
}

async function checkBackup() {
  const w = state.words, b = backupState();
  b.found = null;
  const res = await runBackup("check", () => api().backup_check($("backup-deep").checked));
  if (res) {
    const n = res.changed.length + res.missing.length + res.added.length;
    Object.assign(b, { found: res, note: n ? fill(w.backup_differs, { n }) : w.backup_clean, ok: !n });
  }
  renderBackup();
  return res;
}

// Restore: the game is checked first, and the modder sees what will change before saying yes
async function restoreBackup() {
  const w = state.words, b = backupState();
  const found = await checkBackup();
  if (!found) return;
  const n = found.changed.length + found.missing.length, m = found.added.length;
  if (!n && !m) {
    Object.assign(b, { note: w.backup_nothing, ok: true });
    renderBackup();
    return;
  }
  askBackup(fill(w.backup_restore_ask, { n, m, path: b.status.folder }), w.backup_restore_yes, async () => {
    const res = await runBackup("restore", () => api().backup_restore($("backup-deep").checked));
    if (res) {
      const said = [fill(w.backup_restored, { n: res.restored })];
      if (res.set_aside) said.push(fill(w.backup_set_aside, { m: res.set_aside, path: res.set_aside_to }));
      if (res.kept) said.push(fill(w.backup_kept, { k: res.kept, path: res.set_aside_to }));  // nothing is deleted
      if (res.left.length) said.push(fill(w.doc_fix_left, { left: res.left.join("; ") }));
      Object.assign(b, { found: null, note: said.join(" "), ok: !res.left.length });
    }
    await loadBackup();
  });
}

async function verifyWithSteam() {
  const b = backupState();
  try {
    await api().steam_verify();
    Object.assign(b, { note: state.words.backup_verify_opened, ok: true });
  } catch (err) { Object.assign(b, { note: errorText(err), ok: false }); }
  renderBackup();
}

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
  try { $("app-version").textContent = `v${(await api().app_version()).version}`; } catch { /* an older back end */ }
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
  renderChanges();
}

// What changes: the running version beside the new one, a row per change (rusemod.update.changes_since), and the
// release page under it
function renderChanges() {
  const u = state.update, w = state.words, box = $("update-changes");
  if (!u || !u.available || !state.showChanges) { box.classList.add("hidden"); return; }
  const rows = u.changes || [];
  const page = el("button", { type: "button", className: "small ghost", textContent: w.release_page });
  page.addEventListener("click", () => api().update_page().catch(() => {}));
  box.replaceChildren(rows.length ? el("table", {},
    el("thead", {}, el("tr", {}, el("th", { textContent: "" }),
      el("th", { textContent: fill(w.changes_before, { version: u.current || "" }) }),
      el("th", { textContent: fill(w.changes_now, { version: u.version }) }))),
    el("tbody", {}, ...rows.map((r) => el("tr", {}, el("td", { className: "ver", textContent: r.version }),
      el("td", { className: "before", textContent: r.before || "\u2014" }), el("td", { textContent: r.now })))))
    : el("p", { textContent: w.changes_none }), page);
  box.classList.remove("hidden");
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
  $("set-game-change").addEventListener("click", () => chooseGame().catch(problem));
  $("backup-make").addEventListener("click", makeBackup);
  $("backup-check").addEventListener("click", checkBackup);
  $("backup-restore").addEventListener("click", restoreBackup);
  $("backup-verify").addEventListener("click", verifyWithSteam);
  $("help-wiki").addEventListener("click", () => api().open_help("wiki").catch(problem));
  $("help-discussions").addEventListener("click", () => api().open_help("discussions").catch(problem));
  $("help-report").addEventListener("click", () => api().report_problem("").catch(problem));
  $("help-troubleshoot").addEventListener("click", openDoctor);
  $("troubleshoot").addEventListener("click", openDoctor);
  $("doctor-again").addEventListener("click", () => { doctorNote(""); runDoctor(); });
  $("doctor-copy").addEventListener("click", copyReport);
  $("doctor-close").addEventListener("click", () => $("doctor").close());
  // keys pressed in the troubleshooter stay in it: the unit list's and the map's own keys wait behind it
  window.addEventListener("keydown", (e) => { if ($("doctor").open) e.stopPropagation(); }, true);
  $("set-updates-check").addEventListener("click", async () => {
    $("set-updates-text").textContent = state.words.set_updates_checking;
    try { state.update = await api().update_check(); } catch (err) { state.update = { error: (err && err.message) || String(err) }; }
    renderUpdate();
    renderSettings();
  });
  state.languages = await api().languages();
  state.lang = await loadLang();
  if (!state.lang) {  // nothing kept yet: the language the game is set to in Steam, else the PC's (rusemod.uilang)
    try { state.lang = (await api().language_choice()).suggested; } catch { state.lang = "base"; }  // an older back end
  }
  if (!state.languages.some((l) => l.code === state.lang)) state.lang = "base";
  $("lang-open").addEventListener("click", () => openLangPick(false).catch(problem));
  $("lang-pick-close").addEventListener("click", closeLangPick);
  $("lang-pick-base").addEventListener("click", () => pickLanguage("base").catch(problem));
  // Escape closes it when it was opened from the button, and never reaches the unit list's or the map's own keys
  window.addEventListener("keydown", (e) => {
    if (!langPick) return;
    e.stopPropagation();
    if (e.key === "Escape" && !langPick.first) closeLangPick();
  }, true);
  $("mod").addEventListener("change", (e) => pickMod(e, "mod"));
  $("map-project").addEventListener("change", (e) => pickMod(e, "map"));
  $("new-mod").addEventListener("submit", createMod);
  $("new-mod-cancel").addEventListener("click", () => $("new-mod").classList.add("hidden"));
  $("export-mod").addEventListener("submit", exportMod);
  $("export-cancel").addEventListener("click", () => $("export-mod").classList.add("hidden"));
  $("share-open").addEventListener("click", () => api().open_help("mods").catch(problem));
  $("share-discussions").addEventListener("click", () => api().open_help("discussions").catch(problem));
  $("share-copy").addEventListener("click", copyShareEntry);
  $("share-credit-copy").addEventListener("click", copyShareCredit);
  $("share-publish").addEventListener("click", publishMod);
  $("share-guidelines").addEventListener("click", () => api().open_help("guidelines").catch(problem));
  $("share-close").addEventListener("click", () => $("share").close());
  $("test").addEventListener("click", testInGame);
  $("test-log-close").addEventListener("click", () => $("test-panel").classList.add("hidden"));
  $("test-log-copy").addEventListener("click", copyTestLog);
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
  try {
    const maps = await api().mods("map");
    state.maps = maps.mods;
    state.map = maps.current;
  } catch { state.maps = []; state.map = null; }  // an older back end: one mod for both
  const status = await api().status();
  if (!status.ready) {
    state.words = await api().strings(state.lang);
    await showNoIndex(status);
  }
  $("update-now").addEventListener("click", installUpdate);
  $("update-info").addEventListener("click", () => { state.showChanges = !state.showChanges; renderChanges(); });
  await setLanguage(state.lang);
  // the first screen is drawn: the start-up log (rusemod.startlog) notes it, for the troubleshooter's report
  Promise.resolve().then(() => api().start_mark("ready")).catch(() => {});  // an older back end: no log
  checkUpdate();
  await openLangPick(true);  // until a language is picked there: "Choose your language", first
  firstBackup(status.ready).catch(problem);
}

// The installer's "Keep a clean copy of my game's files" (rusemod.backup.BackupCalls.backup_requested): made on this
// start, in Settings, where its help says why (behind the first run's game index, while that is built)
async function firstBackup(show) {
  let ask;
  try { ask = await api().backup_requested(); } catch { return; }  // an older back end
  if (!ask || !ask.make) return;
  if (show) showView("settings");
  await loadBackup();
  makeBackup();
}

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start().catch(problem);
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
