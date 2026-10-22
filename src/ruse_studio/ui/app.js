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
  era: "vanilla",      // the Units list's era filter: the game's own units, or an era's (eraunits.js)
  eraPage: null,       // the era unit shown (its library key), when one is
  focusModel: null,    // a new unit just made: its page opens at Import model (lookBox)
  aiProfile: null,     // the AI tab's set of values shown (its address: Default, a difficulty or a profile)
  aiScripts: null,     // the AI tab's list of the game's scripts, for one language: { lang, scripts, missing }
  aiScriptPath: null,  // the script shown there (its path in the game's file)
  prefs: {},           // what the Studio keeps for the window (api.prefs): the research choices are read from it
  lastEdit: null };  // the last value changed this session, for Ctrl+Z: { address, prop, mode, via, label }
const KINDS = ["all", "ground", "infantry", "air", "buildings", "ammo"];
const ERA_CHINA = 7;  // the era units' nation chip for China, which has no game nation of its own (eraunits.js)  // ammo: what weapons fire (its own list)
const WHOLE = new Set(["int8", "int16", "uint16", "int32", "uint32", "int64"]);
const NEW = "\u0001new", OPEN = "\u0001open", EXPORT = "\u0001export", SHARE = "\u0001share", EDIT = "\u0001edit";  // the mod menu's actions (never a folder path)

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
    state.prefs = (await api().prefs()) || {};
    const kept = state.prefs.lang;
    if (kept) return kept;
  } catch { /* an older Studio: the window's storage */ }
  try { return localStorage.getItem("studio.lang"); } catch { return null; }
}

function saveLang(lang) {
  try { localStorage.setItem("studio.lang", lang); } catch { /* private window: fine */ }
  Promise.resolve().then(() => api().set_pref("lang", lang)).catch(() => {});
}

// --- pop-ups: what just happened, as cards stacked at the bottom right (the owner's Studio 1.0 list, item 11, "job/
// error pop-ups"; the design: studio-tools-design §11.5). A card that says something went fine (✓) fades after a few
// seconds and a plain message after a few more; a problem (✗) stays until it's closed, with Report beside it (the
// player posts it); a job's card (jobCard: Test in game) shows its latest line while it runs and becomes its result.
// The same text again takes its card's place, and at most TOAST_MOST are up at once (the oldest that fades goes
// first). Every card can be closed (owner, 2026-10-02: a failed test's message stayed with no way out). ---
const TOAST_MOST = 4, TOAST_OK_MS = 4000, TOAST_INFO_MS = 8000, TOAST_GONE_MS = 250;
const TOAST_MARKS = { ok: "✔︎", error: "✖︎", warn: "⚠︎", "": "ℹ︎" };  // drawn as text
let lastSaid = "";   // the last message, for a copied test log

function dropToast(card) {
  if (!card || !card.isConnected || card.classList.contains("going")) return;
  clearTimeout(card._fade);
  card.classList.add("going");
  setTimeout(() => card.remove(), TOAST_GONE_MS);
}

function fadeToast(card, ms) {   // gone after `ms`, the clock held while the mouse is on it
  clearTimeout(card._fade);
  card._fade = setTimeout(() => dropToast(card), ms);
  card.onmouseenter = () => clearTimeout(card._fade);
  card.onmouseleave = () => { card._fade = setTimeout(() => dropToast(card), ms / 2); };
}

// A card for `text` (kind "ok", "error", "warn", "job" or ""), its buttons `actions` [{label, tip, act}]. Returns it.
function toast(text, kind, actions) {
  const w = state.words || {}, box = $("status");
  for (const c of box.querySelectorAll(".toast")) if (c._text === text && !c.classList.contains("job")) c.remove();
  const mark = el("span", { className: "toast-mark", textContent: kind === "job" ? "" : TOAST_MARKS[kind] || TOAST_MARKS[""] });
  const said = el("span", { className: "toast-text", textContent: text });
  const buttons = el("div", { className: "toast-actions" });
  const close = el("button", { type: "button", className: "toast-close", textContent: "×",
    title: w.tip_status_close || "", ariaLabel: w.close || "Close" });
  const card = el("div", { className: "toast " + (kind || "info") }, mark, el("div", { className: "toast-body" }, said, buttons), close);
  card._text = text;
  card._said = said;
  card._buttons = buttons;
  close.addEventListener("click", () => dropToast(card));
  for (const a of actions || []) addToastAction(card, a);
  box.append(card);
  const cards = [...box.querySelectorAll(".toast:not(.going)")];
  for (const old of cards.slice(0, Math.max(0, cards.length - TOAST_MOST))) {
    if (!old.classList.contains("job")) dropToast(old);
  }
  if (kind === "ok") fadeToast(card, TOAST_OK_MS);
  else if (kind !== "error" && kind !== "job") fadeToast(card, TOAST_INFO_MS);
  return card;
}

function addToastAction(card, { label, tip, act }) {
  const b = el("button", { type: "button", className: "link", textContent: label, title: tip || "" });
  b.addEventListener("click", act);
  card._buttons.append(b);
  return b;
}

// A job's card: its latest line while it runs (line), then its result (done).
function jobCard(text) {
  const card = toast(text, "job");
  card._said.append(el("span", { className: "toast-line muted" }));
  return {
    card,
    line(t) { card.querySelector(".toast-line").textContent = t || ""; },
    done(ok, message, actions) {
      dropToast(card);
      return message ? toast(message, ok ? "ok" : "error", actions) : null;
    } };
}

// the cards stand above the test's log while it's open, so its Copy report and Close stay in reach
function liftToasts() {
  const panel = $("test-panel");
  const up = panel && !panel.classList.contains("hidden") ? panel.offsetHeight : 0;
  document.documentElement.style.setProperty("--toasts-lift", `${up}px`);
}
if ($("test-panel")) {
  new ResizeObserver(liftToasts).observe($("test-panel"));
  new MutationObserver(liftToasts).observe($("test-panel"), { attributes: true, attributeFilter: ["class"] });
}

function say(text, kind) {
  if (!text) {   // a message taken back: the cards that fade go at once
    for (const c of $("status").querySelectorAll(".toast")) {
      if (!c.classList.contains("error") && !c.classList.contains("job")) dropToast(c);
    }
    return null;
  }
  const w = state.words || {};
  lastSaid = text;
  const actions = kind === "error" && w.report  // an error can go straight into a bug report (the player posts it)
    ? [{ label: w.report, tip: w.tip_report, act: () => api().report_problem(text).catch(() => {}) }] : [];
  return toast(text, kind || "", actions);
}

function problem(err) {
  say((err && err.message) || String(err), "error");
}

// --- words ---
async function setLanguage(lang) {
  state.lang = lang;
  knownFlags = null;  // the flags' meanings are in the language
  knownNumbers = null;  // and the numbers' (rusemod/numberinfo.toml)
  saveLang(lang);
  state.words = await api().strings(lang);
  renderUpdate();
  recheckUpdate();
  state.nationNames = await api().nations(lang);
  const w = state.words;
  $("tab-units").textContent = w.units_tab;
  $("tab-nations").textContent = w.nations_tab;
  $("tab-ai").textContent = w.ai_tab;  // AI and player settings: the Economy tab's values are in it too
  $("tab-values").textContent = w.values_files_tab;  // All values and files: its two parts by partSwitches
  partSwitches();
  $("tab-decoy").textContent = w.decoy_tab;
  $("tab-maps").textContent = w.maps_tab;
  $("tab-settings").textContent = w.settings_tab;
  if (state.view === "maps" && window.MapView) window.MapView.setWords(w, lang);
  if (state.view === "ai") renderPlay();  // AI and player settings: both halves
  if (state.view === "values") renderValues();
  if (state.view === "decoy") window.DecoyView.setWords(w, lang);
  if (state.view === "nations") window.NationsView.setWords(w, lang);
  if (state.view === "files") window.FilesView.setWords(w);
  if (window.StartFlow) window.StartFlow.setWords();  // the start screen and a new mod's steps, when they're up
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
  const tips = { "tab-units": "tip_tab_units", "tab-nations": "tip_tab_nations", "tab-ai": "tip_tab_ai", "tab-values": "tip_tab_values_files", "tab-decoy": "tip_tab_decoy", "tab-maps": "tip_tab_maps", "tab-settings": "tip_tab_settings", mod: "tip_mod", test: "tip_test", "lang-open": "tip_lang_open",
    "update-now": "tip_update_now", "update-info": "tip_update_info", "new-mod-create": "tip_create_mod",
    "new-mod-cancel": "tip_cancel", "export-go": "tip_export", "export-cancel": "tip_cancel", "test-log-close": "tip_close", "test-log-copy": "tip_copy_log",
    "build-index": "tip_build_index", search: "tip_search", "set-game-change": "tip_game_change",
    "backup-make": "tip_backup_make", "backup-check": "tip_backup_check", "backup-restore": "tip_backup_restore",
    "backup-deep": "tip_backup_deep", "set-updates-check": "tip_updates_check" };
  for (const [id, key] of Object.entries(tips)) $(id).title = w[key] || "";
  $("search").placeholder = w.search;
  $("search").title = [w.tip_search, w.tip_search_tags].filter(Boolean).join(" ");   // (and how #tags work)
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
      el("option", { value: EDIT, textContent: w.edit_installed }),
      el("option", { value: EXPORT, textContent: kind === "mod" ? w.export_mod : w.export_map, disabled: !current }),
      el("option", { value: SHARE, textContent: w.share_mod }));
    $(PICKER[kind]).replaceChildren(...options);
  }
  $("mod").title = w.tip_pick_mod || "";
  $("map-project").title = w.tip_pick_map || "";
  $("map-project-label").textContent = w.map_project || "Map changes";
  $("test").disabled = !(state.mod || state.map) || $("test").dataset.running === "1";
  renderFormat();  // the format bar follows the mod and the map being edited (and the words)
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
  renderChips();  // "In this mod" shows only while a mod is being edited
  checkMod();
}

// --- the mod format (StudioApi.mod_format, update_mod; rusemod.modformat; the owner, 2026-10-16: a mod mustn't be
// destroyed between updates, and an old one gets a way to be updated): a bar under the header for the mod or map being
// edited when it's of an older format with something to rewrite (Update this mod, a backup first), or a newer Studio
// saved it (opened anyway); a newer one is asked about before it's opened (pickMod). ---
async function renderFormat() {
  const w = state.words, bar = $("format-bar"), rows = [];
  for (const kind of ["mod", "map"]) {
    let f;
    try { f = await api().mod_format(kind); } catch { continue; }
    if (!f || (f.state !== "older" && f.state !== "newer")) continue;
    if (kind === "map" && f.path === state.mod) continue;  // (one folder for both: said once)
    const text = el("span", { textContent: fillText(f.state === "older" ? w.format_older : w.format_newer,
      { name: f.name, have: f.format, now: f.current }) });
    const row = el("div", { className: "check-row" }, text);
    if (f.state === "older") {
      const button = el("button", { type: "button", className: "small", textContent: w.format_update, title: w.tip_format_update });
      button.addEventListener("click", async () => {
        button.disabled = true;
        try {
          const res = await api().update_mod(kind);
          say(fillText(w.format_updated, { name: f.name, backup: res.backup || "" }), "ok");
          if (kind === "map") { if (window.MapView && window.MapView.modChanged) window.MapView.modChanged(); }
          else await modChanged();
        } catch (err) { problem(err); }
        renderFormat();
      });
      row.append(button);
    }
    rows.push(row);
  }
  bar.classList.toggle("hidden", !rows.length);
  bar.replaceChildren(...rows);
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
      // in plain words (rusemod.plainproblems: what it is, where, what to do), the build's own words under Details
      const say1 = el("span", { className: "check-say", textContent: plainProblem(p) });
      const how = el("span", { className: "check-how muted", textContent: plainHow(p) });
      const raw = el("code", { className: "check-raw hidden", textContent: p.problem });
      const row = el("div", { className: "check-row" }, el("div", { className: "check-words" }, say1, how, raw));
      const buttons = el("div", { className: "check-fixes" });
      row.append(buttons);
      for (const f of p.fixes || []) buttons.append(fixButton(p, f));
      if (p.set_aside && !(p.fixes || []).some((f) => f.fix === "set_aside")) buttons.append(fixButton(p, { fix: "set_aside", file: p.file }));
      if (needsFolder(p)) {
        const open = el("button", { type: "button", className: "small", textContent: w.pp_fix_open_folder, title: w.tip_pp_open_folder });
        open.addEventListener("click", async () => { try { await api().open_mod_in_folder(); } catch (err) { problem(err); } });
        buttons.append(open);
      }
      const details = el("button", { type: "button", className: "small ghost", textContent: w.pp_details, title: w.tip_pp_details });
      details.addEventListener("click", () => raw.classList.toggle("hidden"));
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
        buttons.append(button);
      }
      if (p.unit) {  // a unit researched from one taken out of the mod: its page, where its Upgrade box re-links it
        const button = el("button", { type: "button", className: "small", textContent: w.check_open_unit,
          title: w.tip_check_open_unit });
        button.addEventListener("click", async () => {
          if (state.era !== "vanilla" && window.EraUnits) {  // its page is in the game's list
            state.era = "vanilla";
            state.group = "all";
            renderChips();
            await refreshList();
          }
          if (state.view !== "units") showView("units");
          showUnit(p.unit);
        });
        buttons.append(button);
      }
      buttons.append(details);
      return row;
    }));
}

// --- one problem in plain words (StudioApi.check_mod's "plain": rusemod.plainproblems.explain) ---
function problemMap(pl) {  // the map as the menus name it, in the Studio's language
  const t = pl.map_titles || {};
  return t[state.lang] || t.us || pl.map || "";
}

function problemItem(pl) {
  const w = state.words;
  const item = w["pp_item_" + pl.item] || pl.item || "";
  return pl.n ? fillText(w.pp_item_n, { item, n: pl.n }) : item;
}

function problemKey(key) {
  return (key && state.words["pp_key_" + key]) || key || "";
}

function plainProblem(p) {
  const w = state.words, pl = p.plain || {};
  const values = { map: problemMap(pl), item: problemItem(pl), key: problemKey(pl.key), file: pl.file || p.file || "",
    line: pl.line || "", what: w["pp_file_" + String(pl.file || "").split("/").pop().replace(/\.toml$/, "")] || pl.file || "" };
  const kind = pl.kind === "bad_value" && !pl.key ? "bad_item" : pl.kind;
  const text = w["pp_" + kind];
  if (!text || kind === "other") return p.problem;  // the Studio's own words already (research, folder names), or unknown
  return `${fillText(text, values)} ${w.pp_stops}`;
}

function plainHow(p) {
  const w = state.words, pl = p.plain || {};
  if (pl.item) return fillText(w.pp_how_item, { item: w["pp_item_" + pl.item] || pl.item });
  if (pl.kind === "unreadable" || pl.kind === "map_file") return w.pp_how_file;
  if (pl.kind === "unit_file") return /(^|\/)studio\.rndf$/.test(pl.file || "") ? w.pp_how_studio_file : w.pp_how_unit_file;
  if (pl.kind === "text_file") return w.pp_how_unit_file;
  if (pl.kind === "manifest") return w.pp_how_manifest;
  return p.unit || p.rename_to ? "" : w.pp_how_other;
}

function needsFolder(p) {  // nothing a button can fix: the mod's folder, to fix it by hand
  const kind = (p.plain || {}).kind;
  return (kind === "manifest" || kind === "other") && !p.unit && !p.rename_to;
}

function fixButton(p, f) {
  const w = state.words, pl = p.plain || {};
  const item = w["pp_item_" + pl.item] || pl.item || "";
  const label = f.fix === "fill" ? (w["pp_fix_fill_" + f.key] || fillText(w.pp_fix_fill, { key: problemKey(f.key) }))
    : f.fix === "remove_key" ? fillText(w.pp_fix_remove_key, { key: f.key })
    : f.fix === "remove_item" ? fillText(w.pp_fix_remove_item, { item })
    : w.check_set_aside;
  const tip = { fill: w.tip_pp_fill, remove_key: w.tip_pp_remove_key, remove_item: w.tip_pp_remove_item }[f.fix] || w.tip_check_set_aside;
  const button = el("button", { type: "button", className: f.fix === "set_aside" ? "small ghost" : "small", textContent: label, title: tip || "" });
  button.addEventListener("click", async () => {
    button.disabled = true;
    try {
      const res = await api().fix_problem(f);
      state.problems = res.problems || [];
      renderCheck();
      say(res.kept ? fillText(w.check_aside_done, { file: res.kept }) : res.message || w.pp_fixed, "ok");
      if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();  // the map shows the fixed file
    } catch (err) { problem(err); button.disabled = false; }
  });
  return button;
}

async function modChanged() {
  state.lastEdit = null;  // the change was in the other mod
  await refreshMarks();
  if (state.page) await showUnit(state.page.address, state.page.via);
  else if (state.eraPage && state.view === "units") await window.EraUnits.showPage(state.eraPage);
  if (state.era !== "vanilla" && state.view === "units") await refreshList();
  if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();  // a map's strokes are the mod's
  state.aiScripts = null;  // which scripts the mod changes: the other mod's now (read again when the AI tab shows)
  $("ai-script").dataset.lang = "";
  closeScriptEditor();
  if (state.view === "ai") await renderPlay();  // the economy shown is the mod's, and so are the computer players and scripts
  if (state.view === "values") renderValuesNew();  // New object… needs a mod
  if (state.view === "values" && state.valuePage) await showValueObject(state.valuePage.address, { keep: true });  // and its changes
  if (state.view === "decoy") window.DecoyView.modChanged();  // and its sounds' volumes and replacements
  if (state.view === "nations") window.NationsView.modChanged();  // and the nations' new names and flags
  if (state.view === "files") window.FilesView.modChanged();  // and the game files it changes
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
    if (value === EDIT) { await openEditMods(); return; }
    if (value !== OPEN) {  // a mod a newer Studio saved: asked first (this one could drop what it doesn't know)
      const f = await api().mod_format(kind, value);
      if (f && f.state === "newer" && !window.confirm(fillText(state.words.format_newer_ask, { name: f.name }))) return;
      useMods(await api().choose_mod(value, kind, Boolean(f && f.state === "newer")));
    } else {
      useMods(await api().open_mod_folder(kind));
    }
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

// --- Edit an installed mod (StudioApi.installed_mods, edit_installed): the Launcher's mods, opened here with everything
// in them. Yours opens its project; anyone else's becomes a copy of your own under a name of its own (never the
// original's: the owner, 2026-10-10); one made the older way (an .rmod) says it can't be shown yet ---
async function openEditMods() {
  const w = state.words;
  $("edit-mods-title").textContent = w.edit_title;
  $("edit-mods-lead").textContent = w.edit_lead;
  $("edit-mods-close").textContent = w.close;
  $("edit-mods-search").placeholder = w.edit_search;
  $("edit-mods-search").title = w.tip_edit_search;
  $("edit-mods-search").value = "";
  $("edit-mods-list").replaceChildren();
  if (!$("edit-mods").open) $("edit-mods").showModal();
  let res;
  try { res = await api().installed_mods(); } catch (err) { problem(err); return; }
  state.installed = res.mods || [];
  renderEditMods();
  $("edit-mods-search").focus();
}

// the rows that match what's typed in the search box: name, author, id or description, case and accents ignored
function renderEditMods() {
  const w = state.words, list = state.installed || [];
  const fold = (s) => String(s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const words = fold($("edit-mods-search").value).split(/\s+/).filter(Boolean);
  const shown = list.filter((m) => {
    const text = fold([m.name, m.author, m.id, m.description].join(" "));
    return words.every((x) => text.includes(x));
  });
  if (!shown.length) {
    $("edit-mods-list").replaceChildren(el("li", { className: "muted small", textContent: list.length ? w.edit_no_match : w.edit_none }));
    return;
  }
  $("edit-mods-list").replaceChildren(...shown.map(editModRow));
}

function editModRow(m) {
  const w = state.words;
  const what = [m.units ? w.edit_has_units : "", m.maps ? w.edit_has_maps : ""].filter(Boolean).join(" · ");
  const head = el("div", { className: "edit-mod-head" },
    el("strong", { textContent: m.name }),
    el("span", { className: "muted small", textContent: [m.version, m.author ? fillText(w.edit_by, { author: m.author }) : "", what].filter(Boolean).join(" · ") }));
  const row = el("li", { className: "edit-mod-row" }, head);
  if (m.error) {
    row.append(el("span", { className: "muted small", textContent: m.error }));
    return row;
  }
  if (m.older) head.append(el("span", { className: "muted small", textContent: w.edit_older }));  // a RUSE Mod Manager mod: converted in its copy
  if (m.yours) {
    const open = el("button", { type: "button", className: "small primary", textContent: w.edit_open, title: w.tip_edit_open });
    open.addEventListener("click", () => editInstalled(m.id, "", open));
    row.append(el("span", { className: "badge edited", textContent: w.edit_yours }), open);
    return row;
  }
  // anyone else's: a copy of your own, named first
  const start = el("button", { type: "button", className: "small", textContent: w.edit_open, title: w.tip_edit_copy });
  const form = el("form", { className: "edit-mod-copy hidden" });
  const name = el("input", { autocomplete: "off", maxLength: 60, required: true, placeholder: w.edit_copy_name });
  const go = el("button", { type: "submit", className: "small primary", textContent: w.edit_copy_go });
  const note = el("span", { className: "small error-text", role: "alert" });  // why a name was refused, in the dialog
  form.append(el("span", { className: "small", textContent: fillText(w.edit_copy_lead, { name: m.name, author: m.author || w.edit_someone }) }), name, go, note);
  start.addEventListener("click", () => { form.classList.remove("hidden"); start.classList.add("hidden"); name.focus(); });
  form.addEventListener("submit", (e) => { e.preventDefault(); editInstalled(m.id, name.value.trim(), go, note); });
  row.append(start, form);
  return row;
}

async function editInstalled(id, name, button, note) {
  button.disabled = true;
  if (note) note.textContent = "";
  let res;
  try { res = await api().edit_installed(id, name); } catch (err) {
    if (note) note.textContent = (err && err.message) || String(err);
    else problem(err);
    button.disabled = false;
    return;
  }
  $("edit-mods").close();
  useMods(res.map);
  useMods(res.mod);
  say(res.message, "ok");
  if (window.MapView && window.MapView.modChanged) window.MapView.modChanged();
  await modChanged();
  if (res.units || !res.maps) {
    state.onlyMod = true;  // what's in the mod, first: its new units and the ones it changes
    if (state.view !== "units") showView("units");
    renderChips();
    await refreshList();
  } else if (state.view !== "maps") showView("maps");
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
  if (window.EraUnits) window.EraUnits.renderChips();  // (eraunits.js loads after this file: the first draw may come first)
  const era = state.era !== "vanilla";
  const kinds = era ? ["all", "ground", "air"] : state.start === "new" ? KINDS.filter((k) => k !== "ammo") : KINDS;
  $("kinds").replaceChildren(...kinds.map((k) => {
    const b = el("button", { type: "button", className: "chip", textContent: w[k], title: w.tip_kind });
    b.setAttribute("aria-pressed", String(state.kind === k));
    b.addEventListener("click", () => { state.kind = k; state.group = "all"; renderChips(); refreshList(); });
    return b;
  }));
  if (!era && state.mod) {  // only what the mod being edited has: its new units and the ones it changes
    const only = el("button", { type: "button", className: "chip", textContent: w.only_mod, title: w.tip_only_mod });
    only.setAttribute("aria-pressed", String(Boolean(state.onlyMod)));
    only.addEventListener("click", () => { state.onlyMod = !state.onlyMod; renderChips(); refreshList(); });
    $("kinds").append(only);
  }
  // ammunition has no nation; an era's units add China (no game nation of its own)
  const nations = state.kind === "ammo" ? [] : era ? [-1, 0, 1, 2, 3, 4, 5, 6, ERA_CHINA] : [-1, 0, 1, 2, 3, 4, 5, 6];
  $("nations").replaceChildren(...nations.map((n) => {
    const b = el("button", { type: "button", className: "chip", title: w.tip_nation,
      textContent: n < 0 ? w.all : n === ERA_CHINA ? w.eras_nation_china : state.nationNames[n] || String(n) });
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
  if (state.era !== "vanilla") return window.EraUnits.refreshList();  // an era's units (eraunits.js)
  let res;
  try {
    res = await api().units(state.lang, state.kind, state.nation, state.search, state.group || "all");
    if ((state.group || "").startsWith(TYPE_PICK) && !(res.types || []).includes(state.group.slice(TYPE_PICK.length))) {
      state.group = "all";  // a type picked in another language or kind: show them all again
      res = await api().units(state.lang, state.kind, state.nation, state.search, "all");
    }
    state.edited = new Set(await api().edited());
  } catch (err) { problem(err); return; }
  if (state.onlyMod && state.mod) res.units = res.units.filter((u) => u.new || state.edited.has(u.address));
  // New unit starts from a unit with a model: those the Studio can't read a model for are left out (the owner,
  // 2026-10-17: "if those units don't have models, just don't include them")
  if (state.start === "new") res.units = res.units.filter((u) => !u.no_model);
  searchTags = res.tags || [];   // (the #tags the search box offers: renderSearchHints)
  renderSearchHints();
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

// A colour of the game's constants (StudioApi.economy, r.colour): [red, green, blue, how solid], 0 to 255 each
function colourBoxes(r) {
  const w = state.words;
  const pick = el("input", { type: "color", disabled: !state.mod, title: w.tip_colour_pick });
  pick.setAttribute("aria-label", r.label);
  const solid = el("input", { type: "number", min: "0", max: "255", step: "1", inputMode: "numeric",
    disabled: !state.mod, title: w.tip_colour_solid });
  solid.setAttribute("aria-label", `${r.label}: ${w.colour_solid}`);
  return [pick, solid];
}

function colourHex(c) {
  return "#" + c.slice(0, 3).map((n) => Number(n).toString(16).padStart(2, "0")).join("");
}

function hexColour(hex) {
  return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
}

function colourText(c) {
  return colourHex(c) + (c[3] === 255 ? "" : ` · ${state.words.colour_solid} ${c[3]}`);
}

function colourSwatch(c) {
  const swatch = el("span", { className: "colour-swatch" });
  swatch.style.background = `rgba(${c[0]}, ${c[1]}, ${c[2]}, ${c[3] / 255})`;
  return swatch;
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
  Object.assign(slider.dataset, { stepper: "buttons", click: String(RANGE_STEP) });   // (the box is its number: 50 m a click)
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

// The lists that hold one value per game mode, and the modes' names (api.numbers modes: the game's lobby's own words;
// English until they're loaded)
const MODE_LISTS = new Set(["ProductionPrice", "ShowInMenu"]);
const MODES_EN = ["1945", "1942", "1939", "Total War", "Nuclear"];
function modeNames() {
  return (knownNumbers && knownNumbers.modes && knownNumbers.modes.length === 5) ? knownNumbers.modes : MODES_EN;
}

function row(u, r, mode) {
  const w = state.words;
  // a value with no name of its own in labels.toml is called by the number guide's ("Statistics id", not TrackingId)
  const entry = numberEntry(u.class, r.prop);
  const label = r.label === r.prop && entry && state.lang !== "base" ? entry.what : r.label;
  const th = el("th", { textContent: label });
  if (state.lang !== "base" && label !== r.prop) th.append(el("small", { textContent: r.prop }));
  if (!r.editable) {  // (one that can't be changed still says what it is)
    if (entry) { th.title = numberTip(entry); th.classList.add("has-meaning"); }
    return el("tr", {}, th, el("td", { textContent: r.values.join(" · ") }));
  }
  if (FLAG_LISTS.has(r.prop)) return flagRow(u, r, mode, th);
  const via = state.page.via;
  const st = rowState(r, mode);
  const shown = st.mine || st.base;
  // a price or shown-in-menu list holds one value per game mode (1945, 1942, 1939, Total War, Nuclear: the game's own
  // order): each box gets its mode's name, as the game's lobby says it
  const modes = MODE_LISTS.has(r.prop) && r.list && shown.length === 5 ? modeNames() : null;
  const boxes = shown.map((n, i) => numberBox(r, n, r.list ? `${r.label} [${modes ? modes[i] : i}]` : r.label));
  const cells = modes ? boxes.map((b, i) => el("label", { className: "mode-box" },
    el("small", { textContent: modes[i] }), b)) : boxes;
  const ranged = RANGE_PROPS.has(r.prop) && !r.list && r.type !== "bool";
  if (ranged) boxes[0].title = w.tip_range_box;
  // A list whose values are all the same (a unit's five prices, one per game mode) gets one box that changes them
  // all, so a modder can't change one of five by accident; "set each" shows every box.
  let one = r.list && shown.length > 1 && r.type !== "bool" && shown.every((n) => n === shown[0])
    ? numberBox(r, shown[0], `${r.label} (${w.all_values.replace("{n}", shown.length)})`) : null;
  const holder = el("div", { className: "boxes" }, ...(one ? [one] : cells));
  const slider = ranged ? rangeSlider(boxes[0], r.numbers[0]) : null;
  if (slider) holder.append(slider.node);
  if (one) {
    const each = el("button", { type: "button", className: "link", textContent: w.each_value, title: w.tip_each_value });
    each.addEventListener("click", () => {
      boxes.forEach((b) => { b.value = one.value; });
      one = null;
      holder.replaceChildren(...cells);
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
  numberHelp(u, r, th, cell, () => (one ? [one] : boxes), st, ranged);
  return tr;
}

// --- what a number means (api.numbers: rusemod/numberinfo.toml), shown on every number of a unit's page (the owner,
// 2026-10-15: "this is their base stat. And then you can make it smaller or larger", "give them perspective on the
// scale of what the numbers mean", "Include all numbers"): its meaning when its name is hovered, its value in plain
// units (metres, km/h, seconds, degrees, $, %), a slider making it smaller or larger than the game's value (its base
// stat), and a bar showing where it sits among the game's units of its kind (api.number_scale) ---
let knownNumbers = null;  // api.numbers(), once per language
const BASE_LEAST = -90, BASE_MOST = 300;  // the base-stat slider: % of the game's value

function numberEntry(cls, prop) {
  if (!knownNumbers) return null;
  const e = knownNumbers.numbers[`${cls}.${prop}`] || knownNumbers.numbers[prop] || null;
  return e && e.classes && !e.classes.includes(cls) ? null : e;  // (its words are about other kinds of object)
}

// A number in plain units ("about 35 km/h"), or "" when its unit has none.
function numberPlain(entry, value) {
  const w = state.words, p = entry && knownNumbers.plain[entry.unit];
  if (!p || !Number.isFinite(value)) return "";
  const v = value / p[0];
  const shown = Math.abs(v) >= 100 ? Math.round(v).toLocaleString() : Number(v.toPrecision(3)).toLocaleString();
  return fill(w.number_about_value, { v: shown, unit: w[p[1]] || "" });
}

function numberTip(entry) {
  const w = state.words;
  if (!entry) return "";
  const sure = w[`number_sure_${entry.sure}`] || entry.sure;
  return [entry.what, entry.does, `${w.flag_sure}: ${sure}`].filter(Boolean).join("\n");
}

function numberHelp(u, r, th, cell, getBoxes, st, ranged) {
  const w = state.words;
  const help = el("div", { className: "number-help" });
  cell.append(help);
  const draw = () => {
    const entry = numberEntry(u.class, r.prop);
    if (!entry) return;
    th.title = numberTip(entry);
    th.classList.add("has-meaning");
    const amount = knownNumbers.amounts.includes(entry.unit) && r.type !== "bool";
    const base = Number(st.base[0]);
    const plainNote = el("span", { className: "muted small number-plain" });
    // acceleration and braking: the game adds a fifth of the value to the speed every 0.2 s, so the unit's own speed
    // divided by it is the seconds to full speed (or to a stop)
    const speedOf = () => {
      const s = (u.groups || []).flatMap((g) => g.rows).find((x) => x.prop === "VitesseLineaire");
      if (!s) return null;
      const mine = s.edited === null || s.edited === undefined ? null : Array.isArray(s.edited) ? s.edited[0] : s.edited;
      return Number(mine === null ? s.numbers[0] : mine);
    };
    const plainOf = (v) => {
      if (r.prop !== "MaxAcceleration" && r.prop !== "MaxDeceleration") return numberPlain(entry, v);
      const speed = speedOf();
      if (!speed || !(v > 0)) return "";
      return fill(w[r.prop === "MaxAcceleration" ? "number_full_speed" : "number_full_stop"],
        { s: Number((speed / v).toPrecision(2)).toLocaleString() });
    };
    const sync = () => {
      const v = Number(getBoxes()[0].value);
      plainNote.textContent = plainOf(v);
      if (slider && Number.isFinite(v) && base) {
        const pct = Math.round((v / base - 1) * 100);
        slider.value = String(Math.max(BASE_LEAST, Math.min(BASE_MOST, pct)));
        pctNote.textContent = fill(w.number_from_base, { pct: (pct > 0 ? "+" : "") + pct });
      }
    };
    // the base-stat slider: not on ranges (they have their own, in metres), choices, switches and ids, nor a value of 0
    let slider = null;
    const pctNote = el("span", { className: "small number-pct" });
    const row = el("div", { className: "number-row" }, plainNote);
    if (amount && !ranged && base && state.mod) {
      slider = el("input", { type: "range", min: String(BASE_LEAST), max: String(BASE_MOST), step: "5",
        className: "base-slider", title: fill(w.tip_number_slider, { base: base.toLocaleString() }) });
      slider.dataset.stepper = "buttons";   // (its % is said beside it, the value in the boxes)
      slider.setAttribute("aria-label", fill(w.number_slider, { name: r.label }));
      const whole = WHOLE.has(r.type);
      slider.addEventListener("input", () => {
        const pct = Number(slider.value);
        for (const [i, b] of getBoxes().entries()) {
          const own = Number(st.base[i] ?? base);
          const v = own * (1 + pct / 100);
          b.value = String(whole ? Math.round(v) : Number(v.toPrecision(6)));
        }
        plainNote.textContent = plainOf(Number(getBoxes()[0].value));
        pctNote.textContent = fill(w.number_from_base, { pct: (pct > 0 ? "+" : "") + pct });
      });
      slider.addEventListener("change", () => getBoxes()[0].dispatchEvent(new Event("change")));
      row.append(el("span", { className: "small muted", textContent: fill(w.number_base, { v: base.toLocaleString() }) }),
        slider, pctNote);
    }
    for (const b of getBoxes()) { b.addEventListener("input", sync); b.addEventListener("change", sync); }
    sync();
    // where it sits among the game's units of its kind, asked for once the row is shown
    const scale = el("div", { className: "number-scale" });
    if (amount) {
      api().number_scale(u.address, r.prop, state.lang).then((s) => {
        if (!s || !s.count || s.min === s.max) return;
        const span = s.max - s.min;
        const at = (v) => `${Math.max(0, Math.min(100, ((v - s.min) / span) * 100))}%`;
        const bar = el("div", { className: "scale-bar" }, el("span", { className: "scale-band",
          style: `left:${at(s.low)};width:calc(${at(s.high)} - ${at(s.low)})` }));
        for (const m of s.marks) bar.append(el("span", { className: "scale-mark", style: `left:${at(m.value)}`,
          title: `${m.name}: ${m.value.toLocaleString()} ${numberPlain(entry, m.value)}` }));
        const here = Number(getBoxes()[0].value);
        if (Number.isFinite(here)) bar.append(el("span", { className: "scale-here", style: `left:${at(here)}`,
          title: fill(w.number_this_unit, { v: here.toLocaleString() }) }));
        const names = s.marks.map((m) => `${m.name} ${m.value.toLocaleString()}`).join(" · ");
        scale.replaceChildren(el("span", { className: "muted small", textContent: fill(w.number_among, { n: s.count }) }),
          bar, el("span", { className: "muted small scale-names", textContent: names }));
      }).catch(() => {});
    }
    help.replaceChildren(row, scale);
    // a scale from others, not measured by us (the metre is ours, measured on the game's maps)
    if (entry.sure === "community" && knownNumbers.plain[entry.unit] && entry.unit !== "m") {
      row.append(el("span", { className: "muted small number-sure", textContent: w.number_scale_unmeasured }));
    }
  };
  if (knownNumbers) draw();
  else api().numbers(state.lang).then((res) => { knownNumbers = res; draw(); }).catch(() => {});
}

// A unit's flags (InitialFlagSet): a set of numbers of any length. Shown as chips with a cross to take one out, and
// an "Add" picker listing every flag, 0-104 (what it does, and who has it: the ones no unit carries say they do
// nothing in a unit's flags).
const FLAG_LISTS = new Set(["InitialFlagSet"]);
let knownFlags = null;  // from api.flags(), once per language

// The flag guide's words for one flag: what it is, what it does, how to use it, how sure we are, its danger and who
// has it (api.flags: rusemod/flaginfo.toml), as one tooltip; `here` adds what the Studio found for this unit.
function flagTip(k, here) {
  const w = state.words;
  if (!k) return "";
  const lines = [`${k.flag} · ${k.what || k.meaning || ""}`];
  if (k.does) lines.push(k.does);
  if (k.use) lines.push(`${w.flag_how}: ${k.use}`);
  if (k.sure) lines.push(`${w.flag_sure}: ${w["flag_sure_" + k.sure] || k.sure}`);
  if (k.danger_why) lines.push(`⚠ ${k.danger_why}`);
  if (k.count) lines.push(fill(w.flag_used_by, { n: k.count, names: k.examples.join(", ") }));
  if (here) lines.push(`⚠ ${here}`);
  return lines.join("\n");
}

function flagRow(u, r, mode, th) {
  const w = state.words;
  const via = state.page.via;
  const st = rowState(r, mode);
  let current = (st.mine || st.base).slice();
  let checked = { problems: [], blocked: false, adding: {} };  // api.flag_check: what's wrong with this unit's flags
  const chips = el("div", { className: "flags" });
  const was = el("div", { className: "was" });
  const entry = numberEntry(u.class, r.prop);  // (what the flags are, on the name, as the other rows have it)
  if (entry) th.title = numberTip(entry);
  // what flags are and what the Studio does with them (the owner, 2026-10-15: "it has to tell the modder what the
  // thinking is going to be doing"), the guide to all of them, and what it found on this unit
  const guideButton = el("button", { type: "button", className: "link", textContent: w.flag_guide, title: w.tip_flag_guide });
  guideButton.addEventListener("click", () => openFlagGuide(current));
  const about = el("p", { className: "muted small flags-about" }, `${w.flags_about} `, guideButton);
  const found = el("div", { className: "flag-problems" });
  const typesLine = el("div", { className: "flag-types-line small" });
  const cell = el("td", {}, chips, found, typesLine, about, was);
  const tr = el("tr", {}, th, cell);
  const info = (n) => knownFlags && knownFlags.find((f) => f.flag === n);
  const setMine = (value) => {
    st.mine = value;
    if (mode === "own") r.edited_own = value; else r.edited = value;
  };
  const check = async () => {
    try { checked = await api().flag_check(u.address, current, state.lang); } catch (err) { checked = { problems: [], blocked: false, adding: {} }; }
    render();
  };
  const save = async (next) => {
    try {
      const res = await api().edit(u.address, r.prop, next, mode, via);
      current = res.value.slice();
      setMine(sameNumbers(current, st.base) ? null : current);
      render();
      await refreshMarks();
      say(w.saved.replace("{file}", res.saved), "ok");
      await check();
    } catch (err) { problem(err); }
  };
  const showProblems = () => {
    found.replaceChildren(...checked.problems.map((p) => {
      const box = el("div", { className: `notice ${p.level === "error" ? "error" : "warn"} flag-problem` },
        el("strong", { textContent: p.level === "error" ? w.flag_crash_head : w.flag_warn_head }), ` ${p.why}`);
      if (state.mod && current.includes(p.flag)) {  // the fix: take the flag off (or, for a recon plane, add 100)
        const off = el("button", { type: "button", className: "small", textContent: fill(w.flag_take_off, { n: p.flag }) });
        off.addEventListener("click", () => save(current.filter((m) => m !== p.flag)));
        box.append(" ", off);
        if (p.flag === 99 && !current.includes(100)) {
          const add = el("button", { type: "button", className: "small ghost", textContent: fill(w.flag_add_this, { n: 100 }) });
          add.addEventListener("click", () => save([...current, 100]));
          box.append(" ", add);
        }
      } else if (state.mod && !current.includes(p.flag)) {  // a flag it needs back
        const back = el("button", { type: "button", className: "small", textContent: fill(w.flag_put_back, { n: p.flag }) });
        back.addEventListener("click", () => save([...current, p.flag]));
        box.append(" ", back);
      }
      return box;
    }));
    if (checked.blocked) found.append(el("p", { className: "small flag-blocked", textContent: w.flag_blocked }));
  };
  const render = () => {
    tr.classList.toggle("edited", st.mine !== null);
    const level = new Map(checked.problems.filter((p) => current.includes(p.flag)).map((p) => [p.flag, p]));
    chips.replaceChildren(...current.map((n) => {
      const k = info(n), bad = level.get(n);
      const cls = ["flag", k ? `flag-${k.group}` : "", bad ? `flag-${bad.level}` : ""].filter(Boolean).join(" ");
      const chip = el("span", { className: cls, title: k ? flagTip(k, bad && bad.why) : String(n) },
        String(n), el("span", { className: "flag-name", textContent: k ? (k.what || k.meaning || "") : "" }));
      if (state.mod) {
        const x = el("button", { type: "button", className: "x", textContent: "×", title: w.flag_remove });
        x.addEventListener("click", () => save(current.filter((m) => m !== n)));
        chip.append(x);
      }
      return chip;
    }));
    showProblems();
    if (state.mod) {
      // the Add list by what the flags are for; one that crashes on this unit, or is expected to break it, says so
      const pick = el("select", { title: w.flag_add });
      pick.append(el("option", { value: "", textContent: w.flag_add }));
      const groups = new Map();
      for (const f of knownFlags || []) {
        if (current.includes(f.flag)) continue;
        const g = f.group || "unused";
        if (!groups.has(g)) groups.set(g, el("optgroup", { label: w["flag_group_" + g] || g }));
        const risk = checked.adding[f.flag];
        const mark = risk === "error" ? ` ⚠ ${w.flag_crashes_here}` : risk === "warning" ? ` ⚠ ${w.flag_breaks_here}` : "";
        groups.get(g).append(el("option", { value: String(f.flag), title: flagTip(f),
          textContent: `${f.flag} · ${f.what || f.meaning || ""}${mark}` + (f.count ? ` (${fill(w.flag_count, { n: f.count })})` : "") }));
      }
      for (const g of FLAG_GROUP_ORDER) if (groups.has(g)) pick.append(groups.get(g));
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
  // the mod's flag types (api.flag_types, flagtypes.py): the ones this unit has, each taken off with its cross, one
  // given from the list, and the window that makes and changes them (the owner, 2026-10-22: "make a new flag type.
  // Select from the existing flags ... You're just checking boxes")
  const giveType = async (name, on) => {
    try {
      const res = await api().flag_type_give(u.address, name, on, state.lang);
      current = res.flags.slice();
      setMine(sameNumbers(current, st.base) ? null : current);
      checked = res.check;
      render();
      renderTypes(res.types);
      await refreshMarks();
      say(fill(on ? w.flag_type_given : w.flag_type_taken, { name }), "ok");
    } catch (err) { problem(err); }
  };
  const renderTypes = (res) => {
    if (!state.mod) return;
    const types = res ? res.types : [];
    const has = types.filter((t) => t.here), others = types.filter((t) => !t.here);
    const typeTip = (t) => [t.about, fill(w.flag_type_turns, { on: t.on.join(" · ") || "—", off: t.off.join(" · ") || "—" })]
      .filter(Boolean).join("\n");
    const parts = [el("span", { className: "muted", textContent: w.flag_types_on_unit })];
    for (const t of has) {
      const x = el("button", { type: "button", className: "x", textContent: "×", title: w.flag_type_take });
      x.addEventListener("click", () => giveType(t.name, false));
      parts.push(el("span", { className: "flag flag-type", title: typeTip(t) }, el("span", { className: "flag-name", textContent: t.name }), x));
    }
    if (!has.length) parts.push(el("span", { className: "muted", textContent: w.flag_types_none_here }));
    if (others.length) {
      const pick = el("select", { title: w.flag_type_give });
      pick.append(el("option", { value: "", textContent: w.flag_type_give }),
        ...others.map((t) => el("option", { value: t.name, title: typeTip(t), textContent: t.name })));
      pick.addEventListener("change", () => { if (pick.value) giveType(pick.value, true); });
      parts.push(pick);
    }
    const edit = el("button", { type: "button", className: "link", textContent: w.flag_types_edit, title: w.tip_flag_types_edit });
    // (a type saved or deleted changes the flags of every unit that has it: this page drawn again)
    edit.addEventListener("click", () => openFlagTypes(() => showUnit(state.page.address, state.page.via)));
    parts.push(edit);
    typesLine.replaceChildren(...parts);
  };
  const loadTypes = () => {
    if (!state.mod) { typesLine.replaceChildren(); return; }
    api().flag_types(u.address).then(renderTypes).catch(() => typesLine.replaceChildren());
  };
  if (knownFlags) { render(); check(); }
  else api().flags(state.lang).then((res) => { knownFlags = res.flags; render(); check(); }).catch((err) => { problem(err); render(); });
  loadTypes();
  return tr;
}

// The mod's flag types (flagtypes.py): a list of them, and a form for one: its name, what it's for, and every game flag
// with an On and an Off box, by what the flags are for, with the flag guide's words on each. `changed()`: what to
// draw again once one is saved or deleted (the unit's flag row).
async function openFlagTypes(changed) {
  const w = state.words;
  if (!knownFlags) {
    try { knownFlags = (await api().flags(state.lang)).flags; } catch (err) { problem(err); return; }
  }
  let dlg = $("flag-types");
  if (!dlg) {
    dlg = el("dialog", { id: "flag-types", className: "doctor flag-guide" });
    dlg.addEventListener("keydown", (e) => e.stopPropagation());  // typing in it never reaches the page behind
    document.body.append(dlg);
  }
  let list = [], editing = null;  // editing: the type the form shows (null: a new one)
  const name = el("input", { type: "text", maxLength: 40, autocomplete: "off", className: "values-text", title: w.flag_type_name });
  name.setAttribute("aria-label", w.flag_type_name);
  const about = el("input", { type: "text", maxLength: 400, autocomplete: "off", className: "values-text flag-type-about", title: w.flag_type_about });
  about.setAttribute("aria-label", w.flag_type_about);
  const search = el("input", { type: "search", autocomplete: "off", className: "edit-mods-search", placeholder: w.flag_guide_search });
  const boxes = new Map();  // flag -> { on, off } checkboxes
  const flagList = el("div", { className: "flag-guide-list flag-types-list" });
  const typeList = el("div", { className: "flag-types-mine" });
  const save = el("button", { type: "button", className: "small primary", textContent: w.flag_type_save });
  const del = el("button", { type: "button", className: "small ghost danger", textContent: w.flag_type_delete });
  const close = el("button", { type: "button", className: "small ghost", textContent: w.close });
  close.addEventListener("click", () => dlg.close());
  const fold = (s) => String(s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const drawFlags = () => {
    const words = fold(search.value).split(/\s+/).filter(Boolean), out = [];
    for (const g of FLAG_GROUP_ORDER) {
      const flags = knownFlags.filter((f) => (f.group || "unused") === g && words.every((x) =>
        fold([f.flag, f.what, f.meaning, f.does, f.use].join(" ")).includes(x)));
      if (!flags.length) continue;
      out.push(el("h3", { className: "flag-guide-group", textContent: w["flag_group_" + g] || g }));
      for (const f of flags) {
        const b = boxes.get(f.flag);
        out.push(el("div", { className: "flag-type-row" + (f.danger ? ` flag-card-${f.danger}` : ""), title: flagTip(f) },
          el("label", { title: w.tip_flag_type_on }, b.on, ` ${w.flag_type_on}`),
          el("label", { title: w.tip_flag_type_off }, b.off, ` ${w.flag_type_off}`),
          el("span", { className: "flag-num", textContent: String(f.flag) }),
          el("strong", { textContent: f.what || f.meaning || "" }),
          f.does ? el("span", { className: "muted", textContent: ` ${f.does}` }) : ""));
      }
    }
    flagList.replaceChildren(...(out.length ? out : [el("p", { className: "muted small", textContent: w.flag_guide_none })]));
  };
  for (const f of knownFlags) {
    const on = el("input", { type: "checkbox" }), off = el("input", { type: "checkbox" });
    on.addEventListener("change", () => { if (on.checked) off.checked = false; });
    off.addEventListener("change", () => { if (off.checked) on.checked = false; });
    boxes.set(f.flag, { on, off });
  }
  const show = (t) => {
    editing = t;
    name.value = t ? t.name : "";
    about.value = t ? t.about : "";
    for (const [n, b] of boxes) { b.on.checked = Boolean(t && t.on.includes(n)); b.off.checked = Boolean(t && t.off.includes(n)); }
    del.classList.toggle("hidden", !t);
    drawTypes();
  };
  const drawTypes = () => {
    const fresh = el("button", { type: "button", className: "small" + (editing ? " ghost" : ""), textContent: w.flag_type_new });
    fresh.addEventListener("click", () => { show(null); name.focus(); });
    typeList.replaceChildren(...list.map((t) => {
      const b = el("button", { type: "button", className: "small" + (editing && editing.name === t.name ? "" : " ghost"),
        textContent: t.name, title: [t.about, fill(w.flag_type_units, { n: t.units })].filter(Boolean).join("\n") });
      b.addEventListener("click", () => show(t));
      return b;
    }), fresh);
  };
  const reload = async (pick) => {
    const res = await api().flag_types();
    list = res.types;
    show(list.find((t) => t.name === pick) || null);
  };
  save.addEventListener("click", async () => {
    const on = [], off = [];
    for (const [n, b] of boxes) { if (b.on.checked) on.push(n); if (b.off.checked) off.push(n); }
    save.disabled = true;
    try {
      await api().flag_type_save(name.value, about.value, on, off, editing ? editing.name : "");
      const saved = name.value.trim();
      await reload(saved);
      say(fill(w.flag_type_saved, { name: saved }), "ok");
      if (changed) changed();
    } catch (err) { problem(err); }
    save.disabled = false;
  });
  del.addEventListener("click", async () => {
    if (!editing || !window.confirm(fill(w.flag_type_really_delete, { name: editing.name }))) return;
    const gone = editing.name;
    try {
      await api().flag_type_delete(gone);
      await reload(null);
      say(fill(w.flag_type_deleted, { name: gone }), "ok");
      if (changed) changed();
    } catch (err) { problem(err); }
  });
  search.addEventListener("input", drawFlags);
  dlg.replaceChildren(el("h2", { textContent: w.flag_types_title }),
    el("p", { className: "muted small", textContent: w.flag_types_lead }), typeList,
    el("label", { className: "small flag-type-field" }, el("span", { textContent: w.flag_type_name }), name),
    el("label", { className: "small flag-type-field" }, el("span", { textContent: w.flag_type_about }), about),
    el("p", { className: "muted small", textContent: w.flag_type_pick }), search, flagList,
    el("div", { className: "actions" }, save, del, close));
  drawFlags();
  try { await reload(null); } catch (err) { problem(err); return; }
  if (!dlg.open) dlg.showModal();
  name.focus();
}

// The flag guide (api.flags: rusemod/flaginfo.toml): every flag, by what it's for, each with what it is, what it does,
// how to use it, how sure we are and its danger; `mine` (this unit's flags) marked; a search box over all of it.
const FLAG_GROUP_ORDER = ["kind", "combat", "movement", "sight", "player", "preview", "state", "unused"];

async function openFlagGuide(mine) {
  const w = state.words;
  $("flag-guide-title").textContent = w.flag_guide_title;
  $("flag-guide-lead").textContent = w.flag_guide_lead;
  $("flag-guide-close").textContent = w.close;
  $("flag-guide-search").placeholder = w.flag_guide_search;
  $("flag-guide-search").value = "";
  state.flagGuideMine = new Set(mine || []);
  if (!knownFlags) {
    try { knownFlags = (await api().flags(state.lang)).flags; } catch (err) { problem(err); return; }
  }
  renderFlagGuide();
  if (!$("flag-guide").open) $("flag-guide").showModal();
  $("flag-guide-search").focus();
}

function renderFlagGuide() {
  const w = state.words, mine = state.flagGuideMine || new Set();
  const fold = (s) => String(s || "").normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const words = fold($("flag-guide-search").value).split(/\s+/).filter(Boolean);
  const out = [];
  for (const g of FLAG_GROUP_ORDER) {
    const flags = (knownFlags || []).filter((f) => (f.group || "unused") === g && words.every((x) =>
      fold([f.flag, f.what, f.meaning, f.does, f.use].join(" ")).includes(x)));
    if (!flags.length) continue;
    out.push(el("h3", { className: "flag-guide-group", textContent: w["flag_group_" + g] || g }),
      el("p", { className: "muted small", textContent: w["flag_group_" + g + "_help"] || "" }));
    for (const f of flags) {
      const badges = [el("span", { className: `flag-sure flag-sure-${f.sure}`, textContent: w["flag_sure_" + f.sure] || f.sure })];
      if (f.danger) badges.push(el("span", { className: `flag-danger flag-danger-${f.danger}`, textContent: w["flag_danger_" + f.danger] || f.danger }));
      if (mine.has(f.flag)) badges.push(el("span", { className: "flag-mine", textContent: w.flag_this_unit }));
      out.push(el("div", { className: "flag-card" + (f.danger ? ` flag-card-${f.danger}` : "") },
        el("div", { className: "flag-card-head" }, el("span", { className: "flag-num", textContent: String(f.flag) }),
          el("strong", { textContent: f.what || f.meaning || "" }), ...badges),
        f.does ? el("p", { className: "small", textContent: f.does }) : "",
        f.use ? el("p", { className: "small" }, el("em", { textContent: `${w.flag_how}: ` }), f.use) : "",
        f.danger_why ? el("p", { className: "small flag-danger-why", textContent: `⚠ ${f.danger_why}` }) : "",
        f.count ? el("p", { className: "muted small", textContent: fill(w.flag_used_by, { n: f.count, names: f.examples.join(", ") }) }) : ""));
    }
  }
  if (!out.length) out.push(el("p", { className: "muted small", textContent: w.flag_guide_none }));
  $("flag-guide-list").replaceChildren(...out);
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

// What a weapon can hit (StudioApi.set_weapon_hits): the ground, planes, or both (a second weapon beside it, the way the
// game's AA guns carry one for each). The owner, 2026-10-14: any weapon on any unit, a tank shooting planes too.
function weaponHits(u, wp, redraw) {
  const w = state.words;
  const pick = el("select", { disabled: !state.mod, title: w.tip_hits });
  pick.setAttribute("aria-label", w.hits);
  for (const [value, word] of [["ground", w.hits_ground], ["planes", w.hits_planes], ["both", w.hits_both]]) {
    pick.append(el("option", { value, textContent: word, selected: wp.hits === value }));
  }
  pick.addEventListener("change", async () => {
    try {
      const res = await api().set_weapon_hits(u.address, wp.address, pick.value);
      await refreshMarks();
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
    redraw();  // its ammo, its shot and its range follow
  });
  const line = el("div", { className: "weapon-range" + (wp.hits !== wp.game_hits ? " edited" : "") },
    el("span", { className: "range-label", textContent: w.hits, title: w.tip_hits }), pick);
  const out = el("div", {}, line);
  if (wp.hits !== wp.game_hits) {
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_hits,
      disabled: !state.mod });
    undo.addEventListener("click", () => { pick.value = wp.game_hits; pick.dispatchEvent(new Event("change")); });
    const game = { ground: w.hits_ground, planes: w.hits_planes, both: w.hits_both }[wp.game_hits];
    out.append(el("div", { className: "was" }, el("span", { textContent: fill(w.was, { v: game }) }), undo),
      el("div", { className: "muted small", textContent: w.hits_not_tried }));
  }
  return out;
}

// A plane's role (StudioApi.plane_role / set_plane_role): fighter, fighter-bomber, bomber or scout. A bomber's bombs go
// in a bomb bay, the only way a bomber's run drops them (a player's report, 2026-10-14: a fighter-bomber given carpet
// bombs flew to its target and dropped nothing).
function roleGroup(u) {
  const w = state.words;
  const can = Boolean(state.mod && u.editable);
  const pick = el("select", { disabled: !can, title: w.tip_role_pick });
  pick.setAttribute("aria-label", w.role_title);
  const was = el("div", { className: "was" });
  const why = el("p", { className: "notice hidden" });
  const moved = el("p", { className: "muted small hidden", textContent: w.role_bombs_moved });
  const head = el("tr", {}, el("th", { textContent: w.role_title, title: w.tip_role_pick }), el("td", {}, pick, was));
  const name = (id) => w["role_" + id] || id;
  const show = (info) => {
    // an armed plane made a scout keeps its attacks (the fighter's behaviour: a scout's crashes the game on attack)
    const label = (id) => id === "scout" && info.armed ? w.role_scout_armed : name(id);
    const options = info.roles.map((r) => el("option", { value: r.id, selected: r.id === info.role,
      textContent: r.seen || r.id === info.game ? label(r.id) : fill(w.role_not_tried, { role: label(r.id) }) }));
    if (!info.roles.some((r) => r.id === info.role)) {
      options.unshift(el("option", { value: "", disabled: true, selected: true, textContent: name(info.role) }));
    }
    pick.replaceChildren(...options);
    pick.disabled = !can || !info.editable;
    why.textContent = info.why ? (w[info.why + "_why"] || w[info.why] || "") : "";
    why.classList.toggle("hidden", !info.why || info.why === "no_mod");
    const edited = info.role !== info.game;
    head.classList.toggle("edited", edited);
    moved.classList.toggle("hidden", !(edited && (info.role === "bomber" || info.game === "bomber")));
    if (!edited) { was.replaceChildren(); return; }
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_role_undo });
    undo.addEventListener("click", () => choose(null));
    was.replaceChildren(el("span", { textContent: w.was.replace("{v}", name(info.game)) }), undo);
  };
  const choose = async (role) => {
    try {
      const res = await api().set_plane_role(u.address, role, state.lang);
      await refreshMarks();
      await showUnit(state.page.address, state.page.via);  // its weapons moved with the role: the whole page again
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
  };
  pick.addEventListener("change", () => choose(pick.value || null));
  api().plane_role(u.address, state.lang).then(show).catch(problem);
  return el("div", { className: "group" }, el("h2", { textContent: w.role_title }),
    el("p", { className: "muted small", textContent: w.role_help }), why, el("table", {}, head), moved);
}

// A ground vehicle's role (StudioApi.ground_role / set_ground_role): as the game has it, or recon, with everything the
// game's recon cars have (T56: a Panzer IV made that way worked as recon; the longer sight alone did not)
function groundRoleGroup(u) {
  const w = state.words;
  const can = Boolean(state.mod && u.editable);
  const pick = el("select", { disabled: !can, title: w.tip_ground_role });
  pick.setAttribute("aria-label", w.role_title);
  const was = el("div", { className: "was" });
  const why = el("p", { className: "notice hidden" });
  const head = el("tr", {}, el("th", { textContent: w.role_title, title: w.tip_ground_role }), el("td", {}, pick, was));
  const name = (id) => id === "recon" ? w.ground_role_recon : w.ground_role_game;
  const show = (info) => {
    pick.replaceChildren(...["game", "recon"].map((id) => el("option", { value: id, selected: id === info.role,
      textContent: id === "recon" && info.game !== "recon" ? fill(w.role_not_tried, { role: name(id) }) : name(id) })));
    pick.disabled = !can || !info.editable;
    why.textContent = info.why && info.why !== "no_mod" ? (w[info.why] || "") : "";
    why.classList.toggle("hidden", !why.textContent);
    const edited = info.role !== info.game;
    head.classList.toggle("edited", edited);
    if (!edited) { was.replaceChildren(); return; }
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_role_undo });
    undo.addEventListener("click", () => choose(null));
    was.replaceChildren(el("span", { textContent: w.was.replace("{v}", name(info.game)) }), undo);
  };
  const choose = async (role) => {
    try {
      const res = await api().set_ground_role(u.address, role, state.lang);
      await refreshMarks();
      await showUnit(state.page.address, state.page.via);  // its values and flags changed: the whole page again
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
  };
  pick.addEventListener("change", () => choose(pick.value === "recon" ? "recon" : null));
  api().ground_role(u.address, state.lang).then(show).catch(problem);
  return el("div", { className: "group" }, el("h2", { textContent: w.role_title }),
    el("p", { className: "muted small", textContent: w.ground_role_help }), why, el("table", {}, head));
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
      const th = el("th", { textContent: fill(w.weapon_n, { n: i + 1 }), title: w.tip_weapon_n }, el("small", { textContent: wp.name }));
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
      if (wp.hits) cell.append(weaponHits(u, wp, draw));
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
    // how weapons and ammo work, step by step (the owner, 2026-10-15: "how to change weapons, ammo type, all of
    // that very well"): a weapon fires one ammo, picked in its list; a copy of an ammo is changed for that weapon only
    const how = el("details", { className: "weapons-how" }, el("summary", { textContent: w.weapons_how_title }),
      el("ol", {}, ...["weapons_how_1", "weapons_how_2", "weapons_how_3", "weapons_how_4", "weapons_how_5"].map((k) =>
        el("li", { className: "small", textContent: w[k] }))));
    group.replaceChildren(el("h2", { textContent: w.weapons }), table,
      el("p", { className: "muted small", textContent: w.weapons_help }), how);
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

// An ammunition's name and kind in game (StudioApi.ammo_text_set): words of the mod's own in every language, then each
// language on its own in the words panel (the owner, 2026-10-22: "make it to where we can name ammo to whatever we want")
function ammoTextsGroup(u) {
  const w = state.words, can = u.editable && Boolean(state.mod);
  const table = el("table");
  for (const t of u.ammo_texts) {
    const label = w["ammo_text_" + t.prop] || t.prop;
    const input = el("input", { type: "text", value: t.words, maxLength: 200, className: "values-text",
      title: w.tip_ammo_text, disabled: !can });
    input.setAttribute("aria-label", label);
    const save = el("button", { type: "button", className: "small primary", textContent: w.ammo_text_save,
      title: w.tip_ammo_text_save, disabled: !can });
    const send = async (words) => {
      save.disabled = true;
      try {
        await api().ammo_text_set(u.address, t.prop, words, state.lang);
        if (state.kind === "ammo") await refreshList();
        await showUnit(u.address);
        say(words ? fill(w.ammo_text_saved, { words }) : w.ammo_text_backed, "ok");
      } catch (err) { problem(err); save.disabled = false; }
    };
    save.addEventListener("click", () => {
      const words = input.value.trim();
      if (words) send(words); else input.focus();
    });
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") save.click(); });
    const cell = el("td", {}, input, " ", save);
    if (t.changed && can) {
      const back = el("button", { type: "button", className: "small ghost", textContent: w.ammo_text_back,
        title: w.tip_ammo_text_back });
      back.addEventListener("click", () => send(""));
      cell.append(" ", back);
    }
    if (t.own && can) {  // the mod's own text: each language on its own
      const edit = el("button", { type: "button", className: "link", textContent: w.values_words_edit,
        title: w.tip_values_words_edit });
      let panel = null;
      edit.addEventListener("click", () => {
        if (panel) { panel.remove(); panel = null; return; }
        panel = wordsPanel(t.key, () => showUnit(u.address), "mod", w.ammo_words_help_new);
        cell.append(panel);
      });
      cell.append(" ", edit);
    }
    table.append(el("tr", {}, el("th", { textContent: label, title: w.tip_ammo_text }), cell));
  }
  return el("div", { className: "group" }, el("h2", { textContent: w.ammo_texts }), table,
    el("p", { className: "muted small", textContent: w.ammo_texts_help }),
    ...(u.in_game ? [el("p", { className: "muted small", textContent: w.ammo_texts_game })] : []));
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
  const remove = async (researched) => {
    yes.disabled = true;
    try {
      const res = await api().delete_unit(u.address, researched);
      if (res.ask) {  // units are researched from it, and the modder chose to be warned first (Settings > Research)
        researchAsk(sure, u.name, res.ask, () => remove("anyway"), () => showUnit(u.address));
        return;
      }
      await refreshList();
      await showUnit(res.source);
      knownFlags = null;
      researchTold(res, w.unit_deleted.replace("{name}", u.name));
    } catch (err) { problem(err); yes.disabled = false; }
  };
  yes.addEventListener("click", () => remove(null));
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

// A picture file of the modder's own as the card: fitted to fill the card's size (cut at the edges, not squashed).
async function cardFromFile(file, card) {
  const pic = await createImageBitmap(file);
  try {
    const c = el("canvas", { width: card.width, height: card.height }), ctx = c.getContext("2d");
    const k = Math.max(card.width / pic.width, card.height / pic.height);
    const wd = pic.width * k, ht = pic.height * k;
    ctx.drawImage(pic, (card.width - wd) / 2, (card.height - ht) / 2, wd, ht);
    return c.toDataURL("image/png");
  } finally { pic.close(); }
}

// The view as it first comes up (from the front corner, a bit above, the model filling the frame): the picture Take a
// new picture takes.
function unitViewHome(gl) {
  if (!gl.fit) return;
  const { centre } = gl.fit;
  gl.controls.autoRotate = false;
  gl.camera.position.set(centre.x + 0.85, centre.y + 0.42, centre.z + 0.85);
  gl.fit.moved = false;
  unitViewFit(gl);
}

// `stale`: the unit wears the mod's paint but its card is still the game's (the owner, 2026-10-11: "that's where I
// think it's okay to be like, hey, the picture is still the base game's picture. We can automatically take one or you
// can choose"): a notice, with Take a new picture and Choose a picture….
function cardRow(u, card, stale) {
  const w = state.words;
  const thumb = el("img", { className: "card-thumb", src: card.url, alt: w.card_now, title: w.card_now });
  const use = el("button", { type: "button", textContent: w.card_use, title: w.tip_card_use });
  const reset = el("button", { type: "button", className: "ghost", textContent: w.card_reset, title: w.tip_card_reset });
  const notice = el("div", { className: "notice warn card-stale" });
  const show = (c) => {
    thumb.src = c.url;
    reset.classList.toggle("hidden", !c.own);
    notice.classList.toggle("hidden", !stale || c.own);
  };
  const save = async (button, picture) => {
    if (!state.mod) { say(w.no_mod, "error"); return; }
    button.disabled = true;
    try {
      const r = await api().look_card(u.address, await picture());
      show(r.card);
      say(r.message, "ok");
    } catch (err) { problem(err); } finally { button.disabled = false; }
  };
  use.addEventListener("click", () => save(use, () => cardShot(card)));
  reset.addEventListener("click", async () => {
    try { const r = await api().look_card_reset(u.address); show(r.card); say(r.message, "ok"); }
    catch (err) { problem(err); }
  });
  const take = el("button", { type: "button", textContent: w.card_take, title: w.tip_card_take });
  take.addEventListener("click", () => save(take, () => { unitViewHome(uview.gl); return cardShot(card); }));
  const file = el("input", { type: "file", accept: "image/png,image/jpeg", className: "hidden" });
  const choose = el("button", { type: "button", className: "ghost", textContent: w.card_choose, title: w.tip_card_choose });
  choose.addEventListener("click", () => file.click());
  file.addEventListener("change", () => {
    const f = file.files && file.files[0];
    file.value = "";
    if (f) save(choose, () => cardFromFile(f, card));
  });
  notice.append(el("p", { className: "small", textContent: w.card_stale }), el("div", { className: "actions" }, take, choose, file));
  show(card);
  return el("div", { className: "card-row-wrap" }, notice, el("div", { className: "card-row" }, thumb,
    el("div", {}, el("p", { className: "muted small", textContent: w.card_note }), el("div", { className: "actions" }, use, reset))));
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
    const oldRow = box.querySelector(".card-row-wrap");
    if (oldRow) oldRow.remove();
    uview.frame = null;
    if (info.card) {
      const frame = el("div", { className: "card-frame" }, el("span", { textContent: w.card_frame }));
      host.append(frame);
      uview.frame = { el: frame, aspect: info.card.width / info.card.height };
      placeCardFrame();
      box.append(cardRow(u, info.card, painted > 0));
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
// --- a building's look (StudioApi.building_look, building_look_import, building_look_change, building_look_remove,
// look_card; rusemod.buildinglook; the owner, 2026-10-18: "The asset importer and building importers" ... "For
// buildings, you also need to be able to change the icon in the in-game menu"): its picture in the build menu, and a
// new building's 3D model in the place of one piece of the look it copies (biggest first: the main building, for a
// factory or a headquarters). A building has no one model of its own the 3D view could show: its look is a layout of
// pieces the game puts down where it's built ---
function buildingLookBox(u, startNew) {
  const w = state.words, address = u.address;
  const body = el("div", { className: "muted small", textContent: w.building_look_working });
  const box = el("div", { className: "group look" }, el("h2", { textContent: w.building_look_title }), body);
  const draw = (info) => {
    if (!info.building) { box.remove(); return; }
    const parts = [];
    if (info.card) parts.push(buildingCardRow(u, info.card));
    if (info.new_unit && state.mod) parts.push(buildingModelBox(address, info, draw));
    else if (!info.new_unit && u.can_copy && u.editable) {
      const go = el("button", { type: "button", textContent: w.model_want_button, title: w.tip_model_want,
        disabled: !startNew });
      if (startNew) go.addEventListener("click", startNew);
      parts.push(el("div", { className: "model-own" }, el("h3", { textContent: w.building_model_title }),
        el("p", { className: "muted small", textContent: w.building_model_want }), el("div", { className: "actions" }, go)));
    }
    body.className = "new-unit";
    body.replaceChildren(...parts);
  };
  api().building_look(address).then(draw).catch((err) => { body.textContent = (err && err.message) || String(err); });
  return box;
}

// Its picture in the build menu: Choose a picture… (fitted to the menu's size), or the game's again
function buildingCardRow(u, card) {
  const w = state.words;
  const thumb = el("img", { className: "card-thumb", src: card.url, alt: w.card_now, title: w.card_now });
  const reset = el("button", { type: "button", className: "ghost", textContent: w.card_reset, title: w.tip_card_reset });
  const file = el("input", { type: "file", accept: "image/png,image/jpeg", className: "hidden" });
  const choose = el("button", { type: "button", textContent: w.card_choose, title: w.tip_card_choose });
  const show = (c) => { thumb.src = c.url; reset.classList.toggle("hidden", !c.own); };
  choose.addEventListener("click", () => {
    if (!state.mod) { say(w.no_mod, "error"); return; }
    file.click();
  });
  file.addEventListener("change", async () => {
    const f = file.files && file.files[0];
    file.value = "";
    if (!f) return;
    choose.disabled = true;
    try {
      const r = await api().look_card(u.address, await cardFromFile(f, card));
      show(r.card);
      say(r.message, "ok");
    } catch (err) { problem(err); } finally { choose.disabled = false; }
  });
  reset.addEventListener("click", async () => {
    try { const r = await api().look_card_reset(u.address); show(r.card); say(r.message, "ok"); }
    catch (err) { problem(err); }
  });
  show(card);
  return el("div", { className: "model-own" }, el("h3", { textContent: w.building_card_title }),
    el("div", { className: "card-row" }, thumb, el("div", {},
      el("p", { className: "muted small", textContent: w.building_card_how }),
      el("div", { className: "actions" }, choose, reset, file))));
}

// A new building's 3D model: which piece of the copied look it takes the place of, its size (times that piece's), and
// Import model…; once it has one, what it is, Replace…, Save size and Remove
function buildingModelBox(address, info, draw) {
  const w = state.words, own = info.own;
  const piece = el("select", { className: "building-piece", title: w.tip_building_piece });
  for (const p of info.pieces) {
    piece.append(el("option", { value: p.type, textContent: fill(w.building_piece_row, { name: p.name,
      w: p.size[0], d: p.size[1], h: p.size[2], n: p.count }) }));
  }
  if (own) piece.value = own.piece;
  piece.disabled = Boolean(own);  // (another piece: Remove first)
  const size = el("input", { type: "number", min: "0.01", max: "100", step: "0.05", value: String(own ? own.size : 1),
    className: "model-size", title: w.tip_building_size });
  const licence = el("select", { title: w.tip_asset_licence });
  for (const [v, t] of [["", w.asset_licence_own], ["CC0", w.asset_licence_free], ["CC-BY", w.asset_licence_credit]]) {
    licence.append(el("option", { value: v, textContent: t }));
  }
  const credit = (own && own.credit) || {};
  licence.value = ["CC0", "CC-BY"].includes(credit.licence) ? credit.licence : "";
  const author = el("input", { type: "text", value: credit.author || "", placeholder: w.asset_author, title: w.tip_asset_author });
  const source = el("input", { type: "text", value: credit.source || "", placeholder: w.asset_source, title: w.tip_asset_source });
  const pick = el("button", { type: "button", textContent: own ? w.model_import_again : w.model_import,
    title: w.tip_building_import, disabled: !info.pieces.length });
  pick.addEventListener("click", async () => {
    pick.disabled = true;
    say(w.building_importing);
    try {
      const r = await api().building_look_import(address, own ? own.piece : piece.value, null, Number(size.value) || 1,
        false, source.value.trim(), author.value.trim(), licence.value);
      if (r.done) say(w.building_done, "ok");
      draw(r);
    } catch (err) { problem(err); } finally { pick.disabled = false; }
  });
  const box = el("div", { className: "model-own" }, el("h3", { textContent: w.building_model_title }),
    el("p", { className: "muted small", textContent: w.building_model_how }),
    el("label", { className: "small" }, w.building_piece, " ", piece),
    el("label", { className: "small" }, w.asset_size, " ", size),
    el("label", { className: "small" }, w.asset_licence, " ", licence), author, source,
    el("div", { className: "actions" }, pick));
  if (!info.pieces.length) box.append(el("p", { className: "notice warn", textContent: w.building_no_pieces }));
  if (own) {
    const v = own.versions || {}, n = (x) => (x === null || x === undefined ? "?" : x.toLocaleString());
    box.append(el("p", { className: "small", textContent: fill(w.building_own, { file: own.file,
      triangles: n(own.triangles), middle: n((v.medium || {}).triangles), far: n((v.far || {}).triangles) }) }));
    const save = el("button", { type: "button", className: "ghost", textContent: w.asset_save, title: w.tip_building_save });
    save.addEventListener("click", async () => {
      try {
        draw(await api().building_look_change(address, Number(size.value) || 1, null, source.value.trim(),
          author.value.trim(), licence.value));
        say(w.asset_saved, "ok");
      } catch (err) { problem(err); }
    });
    const remove = el("button", { type: "button", className: "ghost danger", textContent: w.building_remove,
      title: w.tip_building_remove });
    remove.addEventListener("click", async () => {
      try { draw(await api().building_look_remove(address)); say(w.building_removed, "ok"); } catch (err) { problem(err); }
    });
    box.append(el("div", { className: "actions" }, save, remove));
  }
  return box;
}

function lookBox(u, brought, startNew) {
  if (u.kind === "buildings" || u.class === "TBatimentDescriptor") return buildingLookBox(u, startNew);
  const w = state.words;
  const address = u.address;
  const body = el("div", { className: "muted small", textContent: w.look_working });
  const box = el("div", { className: "group look" }, el("h2", { textContent: w.unit_look, title: w.tip_unit_look }), body);
  const draw = (info) => {
    if (!info.models || !info.models.length) {
      // a new unit's box stays, saying why it has no model to change (a modder's report, 2026-10-17: "the window for
      // changing the model never opens"; it was taken away without a word). Ammo, weapons and the like: no box
      if (!info.new_unit) { box.remove(); return; }
      body.className = "new-unit";
      body.replaceChildren(el("p", { className: "notice warn", textContent: w.model_none }));
      return;
    }
    const parts = [];
    // a squad's look is its uniform: the game's (Default, worn by other squads and the gun and vehicle crews too, so
    // never repainted here) or its own (Custom: its own copy of its soldiers), which Blender paints (the owner,
    // 2026-10-11: "have, like, default uniform, and then ... do you want a custom uniform?")
    if (info.soldiers) parts.push(uniformBox(address, info, draw, brought));
    const paintable = !info.soldiers || info.own_copy;  // (Blender's buttons come with a custom uniform)
    if (paintable && !info.blender) {
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
    } else if (paintable) {
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
      parts.push(el("p", { className: paintable ? "small" : "notice warn",
        textContent: fill(paintable ? w.look_painted : w.uniform_shared_paint, { n: info.painted.length }) }));
    }
    let model = null;  // (a squad's soldiers aren't swapped for an imported model)
    if (!info.soldiers && info.new_unit && state.mod) parts.push(model = modelBox(address, info, draw, brought));
    else if (!info.soldiers && !info.new_unit && u.can_copy && u.editable) parts.push(modelWant(startNew));  // (no mod: no startNew)
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
// A model's size on a slider beside its number box (the owner, 2026-10-10: "make it a slider. So if people want to
// have like super big planes or make them realistic to how they are in real life compared, like maybe have the slider
// label those points" ... "even do a tiny"): the importer's sizes, Tiny to Huge, on a log scale (1, the game's size,
// in the middle), with its points named under it (StudioApi.model_size_marks: tiny, game, real when known, huge);
// a point clicked takes the size to it. The number box stays the exact value; the slider follows it.
const SIZE_STEPS = 1000;
const sizeRound = (s) => Number(Number(s).toPrecision(3));
function sizeSlider(box, marks) {
  const w = state.words;
  const lo = Math.log(marks.tiny), hi = Math.log(marks.huge);
  const at = (s) => Math.round((Math.log(Math.min(marks.huge, Math.max(marks.tiny, s))) - lo) / (hi - lo) * SIZE_STEPS);
  const sizeAt = (p) => Math.exp(lo + (p / SIZE_STEPS) * (hi - lo));
  const range = el("input", { type: "range", min: "0", max: String(SIZE_STEPS), step: "1", className: "size-range",
    title: w.tip_size_slider });
  Object.assign(range.dataset, { stepper: "beside", click: "20" });   // (its marks are drawn along it)
  range.setAttribute("aria-label", w.model_size);
  const follow = () => { const v = Number(box.value); if (Number.isFinite(v) && v > 0) range.value = String(at(v)); };
  const take = (s) => { box.value = String(sizeRound(s)); follow(); box.dispatchEvent(new Event("input")); };
  range.addEventListener("input", () => take(sizeAt(Number(range.value))));
  if (box.sizeFollow) box.removeEventListener("input", box.sizeFollow);  // (a slider made again for the same box)
  box.sizeFollow = follow;
  box.addEventListener("input", follow);
  follow();
  const points = [["tiny", marks.tiny, w.size_tiny, w.tip_size_tiny],
    ["game", marks.game, w.size_game, fill(w.tip_size_game, { unit: marks.start || "?" })],
    ...(marks.real ? [["real", marks.real, w.size_real, w.tip_size_real]] : []),
    ["huge", marks.huge, w.size_huge, w.tip_size_huge]].sort((a, b) => a[1] - b[1]);
  let last = -1, low = false;
  const labels = points.map(([key, s, label, tip]) => {
    const pct = (at(s) / SIZE_STEPS) * 100;
    low = last >= 0 && pct - last < 14 ? !low : false;  // two points close together: the next on the line below
    last = pct;
    const b = el("button", { type: "button", className: `size-mark size-${key}${low ? " low" : ""}`,
      textContent: `${label} (${sizeRound(s)})`, title: tip });
    b.style.left = `${pct}%`;
    b.addEventListener("click", () => take(s));
    return b;
  });
  return el("div", { className: "size-slider" }, range, el("div", { className: "size-marks" }, ...labels));
}

// Every plane (or ground unit) of the mod with a model of its own, resized at once (StudioApi.models_resize_all, a
// job): to the game's size, to real life, or a step smaller or bigger.
function resizeAllRow(kind, n, changed) {
  const w = state.words;
  const note = el("span", { className: "small", role: "status" });
  const go = async (to, times, buttons) => {
    buttons.forEach((b) => { b.disabled = true; });
    let job;
    try { job = await api().models_resize_all(kind, to, times); } catch (err) { problem(err); buttons.forEach((b) => { b.disabled = false; }); return; }
    let seen = 0;
    const done = [], skipped = [];
    for (;;) {
      let st;
      try { st = await api().job(job.job, seen); } catch (err) { problem(err); break; }
      seen = st.count;
      for (const line of st.lines) {
        const [what, unit, more] = line.split("\t");
        if (what === "resized") done.push(unit); else if (what === "skipped") skipped.push(`${unit}: ${more}`);
      }
      note.textContent = fill(w.models_all_progress, { done: done.length + skipped.length, all: n });
      if (st.state !== "running") break;
      await new Promise((ok) => setTimeout(ok, 700));
    }
    note.textContent = fill(w.models_all_done, { n: done.length })
      + (skipped.length ? " " + fill(w.models_all_skipped, { list: skipped.join(" · ") }) : "");
    say(note.textContent, skipped.length ? "" : "ok");
    buttons.forEach((b) => { b.disabled = false; });
    if (changed) changed();
  };
  const specs = [["game", null, w.size_game, w.tip_models_all_game], ["real", null, w.size_real, w.tip_models_all_real],
    ["times", 0.8, w.models_all_smaller, w.tip_models_all_smaller], ["times", 1.25, w.models_all_bigger, w.tip_models_all_bigger]];
  const buttons = specs.map(([, , label, tip]) => el("button", { type: "button", className: "small ghost", textContent: label, title: tip }));
  buttons.forEach((b, i) => b.addEventListener("click", () => go(specs[i][0], specs[i][1], buttons)));
  return el("div", { className: "actions resize-all" },
    el("span", { className: "small", textContent: fill(kind === "air" ? w.models_all_air : w.models_all_ground, { n }) }),
    ...buttons, note);
}

function modelBox(address, info, draw, changed) {
  const w = state.words;
  const own = info.own_model;
  const size = el("input", { type: "number", min: "0.05", max: "20", step: "any", value: "1", className: "model-size",
    title: w.tip_model_size });
  // its size now, the slider's points, Resize (fitted again from its own file) and every plane at once
  const sizing = el("div", { className: "model-sizing" });
  const resize = el("button", { type: "button", className: "small", textContent: w.model_resize, title: w.tip_model_resize,
    disabled: true });
  resize.addEventListener("click", async () => {
    const s = Number(size.value);
    if (!Number.isFinite(s)) return;
    resize.disabled = true;
    say(w.model_resizing);
    try {
      const r = await api().model_resize(address, s);
      say(fill(w.model_resized, { size: sizeRound(s) }), "ok");
      if (changed) changed();
      draw(r);
    } catch (err) { problem(err); resize.disabled = false; }
  });
  (own ? api().model_sizes(address, state.lang) : api().model_size_marks(address, state.lang).then((marks) => ({ marks })))
    .then((s) => {
      if (!s) return;
      if (s.size) size.value = String(sizeRound(s.size));
      resize.disabled = !s.resizable;
      if (own && !s.resizable) resize.title = w.tip_model_resize_gone;
      sizing.append(sizeSlider(size, s.marks));
      if (own && s.same_kind > 1) {
        sizing.append(resizeAllRow(s.kind, s.same_kind, () => api().look(address).then(draw).catch(problem)));
      }
    }).catch(() => {});  // (no slider: the number box still takes a size)
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
  // its own copy of the model it copies (StudioApi.model_copy; the owner, 2026-10-11: "duplicate that part"): the same
  // model with textures of its own, so Repaint in Blender above changes this unit only
  const copyAction = (call, button) => async () => {
    button.disabled = true;
    try {
      const r = await api()[call](address);
      say(r.message, "ok");
      draw(r);
      if (changed) changed();
    } catch (err) { problem(err); button.disabled = false; }
  };
  if (info.own_copy) {
    const back = el("button", { type: "button", className: "ghost", textContent: w.model_copy_remove, title: w.tip_model_copy_remove });
    back.addEventListener("click", copyAction("model_copy_remove", back));
    box.append(el("p", { className: "small", textContent: w.model_copy_has }), el("div", { className: "actions" }, back));
    box.pick = back;
    return box;  // (one model per unit: no import while it has a copy)
  }
  if (!own) {
    const copy = el("button", { type: "button", textContent: w.model_copy, title: w.tip_model_copy });
    copy.addEventListener("click", copyAction("model_copy", copy));
    box.append(el("p", { className: "muted small", textContent: w.model_copy_how }), el("div", { className: "actions" }, copy));
  }
  if (own) {
    box.append(el("p", { className: "small", textContent: fill(w.model_own, { file: own.file || "",
      points: (own.vertices || 0).toLocaleString(), triangles: (own.triangles || 0).toLocaleString() }) }));
    const turret = Object.entries(own.parts || {}).filter(([, role]) => role === "turret" || role === "gun").map(([name]) => name);
    if (turret.length) box.append(el("p", { className: "muted small", textContent: fill(w.model_turret, { parts: turret.join(", ") }) }));
    // its propeller discs (rusemod.modelin.fit_discs): spinning as the game's, or left out and why
    const props = own.propellers || {};
    if (props.kept) box.append(el("p", { className: "muted small", textContent: fill(w.model_propellers, { n: props.kept }) }));
    if (props.left_out) {
      box.append(el("p", { className: "notice warn", textContent: fill(props.why === "none" ? w.model_propellers_none
        : w.model_propellers_far, { n: props.left_out }) }));
    }
    if (own.missing && own.missing.length) {
      box.append(el("p", { className: "notice warn", textContent: fill(w.model_missing, { names: own.missing.join(", ") }) }));
    }
    const drop = el("button", { type: "button", className: "ghost", textContent: w.model_remove, title: w.tip_model_remove });
    drop.addEventListener("click", async () => {
      try { draw(await api().model_import_remove(address)); if (changed) changed(); } catch (err) { problem(err); }
    });
    box.append(el("div", { className: "actions" }, el("label", { className: "small" }, w.model_size, " ", size), resize),
      sizing, el("p", { className: "muted small", textContent: w.model_size_when }), el("div", { className: "actions" }, pick, drop));
  } else {
    box.append(el("p", { className: "muted small", textContent: w.model_how }),
      el("div", { className: "actions" }, pick, el("label", { className: "small" }, w.model_size, " ", size)), sizing);
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
// A squad's uniform (api.model_copy, model_copy_remove: its own copy of its soldiers, the game's squads' too): Default
// is the game's picture, which other squads and the gun and vehicle crews wear as well (T48: one squad repainted turned
// every US soldier blue); Custom is this squad's own, and Repaint in Blender paints it.
function uniformBox(address, info, draw, changed) {
  const w = state.words;
  const box = el("div", { className: "model-own uniform" }, el("h3", { textContent: w.uniform_title }));
  const act = (call, button) => async () => {
    if (!state.mod) { say(w.no_mod, "error"); return; }
    button.disabled = true;
    try {
      const r = await api()[call](address);
      say(r.message, "ok");
      draw(r);
      if (changed) changed();
    } catch (err) { problem(err); button.disabled = false; }
  };
  if (info.own_copy) {
    const back = el("button", { type: "button", className: "ghost", textContent: w.uniform_default_again,
      title: w.tip_uniform_default_again });
    back.addEventListener("click", act("model_copy_remove", back));
    box.append(el("p", { className: "small", textContent: w.uniform_has }), el("div", { className: "actions" }, back));
  } else {
    const custom = el("button", { type: "button", textContent: w.uniform_custom, title: w.tip_uniform_custom,
      disabled: !state.mod });
    custom.addEventListener("click", act("model_copy", custom));
    box.append(el("p", { className: "muted small", textContent: w.uniform_default }), el("div", { className: "actions" }, custom));
    if (!state.mod) box.append(el("p", { className: "notice", textContent: w.no_mod }));
  }
  return box;
}

// The truck a squad or a gun rides in on the roads (api.rides_in, rides_in_set; the owner, 2026-10-11: "rangers versus
// GI, getting a different truck"): the game's trucks of its kind, every nation's, and the mod's copies of a truck,
// which get a look of their own on their own page (Give it its own copy, then Repaint in Blender).
function ridesInBox(u) {
  const w = state.words;
  const box = el("div", { className: "group rides-in" }, el("h2", { textContent: w.rides_in, title: w.tip_rides_in }));
  const draw = (info) => {
    if (!info || !info.choices) { box.remove(); return; }
    const pick = el("select", { title: w.tip_rides_in, disabled: !state.mod || !u.editable });
    for (const c of info.choices) {
      const mark = c.address === info.game ? ` ${w.rides_in_game}` : c.new ? ` ${w.rides_in_mine}` : "";
      pick.append(el("option", { value: c.address, textContent: `${c.name} (${c.code})${mark}`,
        selected: c.address === info.now }));
    }
    pick.addEventListener("change", async () => {
      pick.disabled = true;
      try { const r = await api().rides_in_set(u.address, pick.value, state.lang); say(r.message, "ok"); draw(r); }
      catch (err) { problem(err); draw(info); }
    });
    const open = el("button", { type: "button", className: "ghost small", textContent: w.rides_in_open,
      title: w.tip_rides_in_open });
    open.addEventListener("click", () => showUnit(pick.value));
    box.replaceChildren(box.firstChild, el("p", { className: "muted small", textContent: w.rides_in_how }),
      el("div", { className: "actions" }, pick, open));
    if (!state.mod) box.append(el("p", { className: "notice", textContent: w.no_mod }));
  };
  api().rides_in(u.address, state.lang).then(draw).catch(() => box.remove());
  return box;
}

function modelWant(startNew) {
  const w = state.words;
  const go = el("button", { type: "button", textContent: w.model_want_button, title: w.tip_model_want,
    disabled: !startNew });
  if (startNew) go.addEventListener("click", startNew);
  return el("div", { className: "model-own" }, el("h3", { textContent: w.model_title }),
    el("p", { className: "muted small", textContent: w.model_want }), el("div", { className: "actions" }, go));
}

// --- research: what taking out a unit others are researched from does (the modder's choice in Settings > Research,
// kept as the preference "research_gone": warn first, refuse, or re-link them; StudioApi.RESEARCH_GONE), and research
// times typed in seconds or minutes (kept as whole seconds; that the game counts them in seconds isn't timed in the
// game yet; kept as "research_time_unit") ---
const RESEARCH_GONE = ["warn", "refuse", "relink"];
const TIME_UNITS = { s: 1, min: 60 };

function timeUnit() {
  const u = (state.prefs || {}).research_time_unit;
  return TIME_UNITS[u] ? u : "s";
}

function keepPref(key, value) {
  state.prefs = { ...(state.prefs || {}), [key]: value };
  Promise.resolve().then(() => api().set_pref(key, value)).catch(problem);
}

// a time in seconds as its box shows it in `unit` (minutes to two decimals); "" for none
function timeShown(seconds, unit) {
  if (seconds === null || seconds === undefined || seconds === "" || !Number.isFinite(Number(seconds))) return "";
  return unit === "min" ? String(Math.round((Number(seconds) / 60) * 100) / 100) : String(seconds);
}

// what's typed in `unit`, in whole seconds (NaN when it isn't a number)
function timeSeconds(typed, unit) {
  return Number.isFinite(typed) ? Math.round(typed * TIME_UNITS[unit]) : NaN;
}

// The seconds/minutes picker beside a research time box: the time typed stays the same time in the unit picked, and
// the pick is kept for every research time box. `changed(unit)` follows a pick.
function timeUnitPicker(box, changed) {
  const w = state.words;
  const pick = el("select", { title: w.tip_research_time_unit });
  pick.setAttribute("aria-label", w.research_time_unit);
  pick.append(el("option", { value: "s", textContent: w.research_seconds }),
    el("option", { value: "min", textContent: w.research_minutes }));
  pick.value = timeUnit();
  let shown = pick.value;
  const fit = () => {
    box.step = shown === "min" ? "any" : "1";
    box.inputMode = shown === "min" ? "decimal" : "numeric";
  };
  fit();
  pick.addEventListener("change", () => {
    const seconds = timeSeconds(readBox(box), shown);
    shown = pick.value;
    if (Number.isFinite(seconds)) box.value = timeShown(seconds, shown);
    fit();
    keepPref("research_time_unit", shown);
    if (changed) changed(shown);
  });
  return pick;
}

// The warning before taking out a unit others are researched from (StudioApi.delete_unit / era_unit_remove gave
// {ask}): in `box`, who's researched from it, Take it out anyway (`goAhead`), Cancel (`cancel`), and the way to
// Settings > Research, where the modder can choose to refuse or re-link instead
function researchAsk(box, name, children, goAhead, cancel) {
  const w = state.words;
  const anyway = el("button", { type: "button", className: "ghost danger", textContent: w.research_gone_anyway,
    title: w.tip_research_gone_anyway });
  const keep = el("button", { type: "button", className: "ghost", textContent: w.cancel, title: w.tip_cancel });
  const settings = el("button", { type: "button", className: "link", textContent: w.research_gone_settings,
    title: w.tip_research_gone_settings });
  anyway.addEventListener("click", () => { anyway.disabled = true; goAhead(); });
  keep.addEventListener("click", cancel);
  settings.addEventListener("click", () => window.openSettings("research"));
  box.classList.remove("hidden");
  box.replaceChildren(el("p", { className: "notice warn", textContent: fill(w.research_gone_ask,
    { name, names: children.map((c) => c.name).join(", ") }) }), el("div", { className: "actions" }, anyway, keep, settings));
  anyway.focus();
}

// After a unit went: `done`, then what became of the units researched from it (re-linked to its own parent or made
// buyable from the start; or left researched from a unit that's gone, which the check bar then lists)
function researchTold(res, done) {
  const w = state.words;
  const lines = [done, ...(res.relinked || []).map((r) => r.to ? fill(w.research_relinked, { name: r.name, to: r.to.name })
    : fill(w.research_relinked_none, { name: r.name }))];
  const left = res.left || [];
  if (left.length) lines.push(fill(w.research_left, { names: left.map((c) => c.name).join(", ") }));
  say(lines.join(" "), left.length ? "warn" : "ok");
  if (left.length || (res.relinked || []).length) checkMod();
}

// A unit's place in the upgrade chains and its research (StudioApi.upgrade, set_upgrade, set_research; LittleGroove's
// "Upgrade chain"): the unit it's researched from, picked among the same nation's units in the same build menu, the
// units researched from it, and its research price and time (the time in seconds or minutes: timeUnitPicker)
function upgradeGroup(u) {
  const w = state.words;
  const can = Boolean(state.mod && u.editable);
  const pick = el("select", { disabled: !can, title: w.tip_upgrade_from });
  const was = el("div", { className: "was" });
  const kids = el("p", { className: "muted small" });
  const table = el("table");
  const head = el("tr", {}, el("th", { textContent: w.upgrade_from,
    title: numberTip(numberEntry(u.class, "UpgradeRequire")) || w.tip_upgrade_from }), el("td", {}, pick, was));
  const gone = el("p", { className: "notice warn hidden", textContent: w.upgrade_parent_gone });
  const researchRow = (prop, r) => {
    // the research time in the unit picked beside it (the game keeps whole seconds); the price as it is
    const time = prop === "UpgradeTime";
    let unit = time ? timeUnit() : "s";
    const shown = (seconds) => (time ? timeShown(seconds, unit) : String(seconds ?? ""));
    const box = numberBox({ type: "int32" }, "", r.label);
    box.value = shown(r.value ?? r.game ?? "");
    box.disabled = !can;
    let now = r.value;  // the mod's value (null: the game's)
    const rwas = el("div", { className: "was" });
    const mark = (value) => {
      now = value;
      const edited = value !== null && value !== r.game;
      cell.classList.toggle("edited", edited);
      if (!edited) { rwas.replaceChildren(); return; }
      const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_upgrade_undo });
      undo.addEventListener("click", async () => {
        try {
          const res = await api().set_research(u.address, prop, null);
          box.value = shown(res.value ?? "");
          mark(null);
        } catch (err) { problem(err); }
      });
      rwas.replaceChildren(el("span", { textContent: w.was.replace("{v}", r.game === null ? "–" : shown(r.game)) }), undo);
    };
    const units = time ? timeUnitPicker(box, (picked) => { unit = picked; mark(now); }) : null;
    if (units) units.disabled = !can;
    const cell = el("td", {}, el("div", { className: "boxes" }, box, ...(units ? [units] : [])), rwas);
    box.addEventListener("change", async () => {
      const n = time ? timeSeconds(readBox(box), unit) : readBox(box);
      box.setAttribute("aria-invalid", String(!Number.isFinite(n)));
      if (!Number.isFinite(n)) return;
      try {
        const res = await api().set_research(u.address, prop, n);
        box.value = shown(res.value);
        mark(res.value);
        say(w.saved.replace("{file}", res.saved), "ok");
      } catch (err) { problem(err); }
    });
    mark(r.value);
    // what it is, from the number guide, on the name (as the unit's other numbers have it)
    const entry = numberEntry(u.class, prop);
    return el("tr", {}, el("th", { textContent: r.label, title: numberTip(entry),
      className: entry ? "has-meaning" : "" }), cell);
  };
  const show = (info) => {
    const current = info.parent ? info.parent.address : "", game = info.game_parent ? info.game_parent.address : "";
    // researched from a unit no longer in the mod (taken out after the warning): said, and shown as picked until
    // another is
    gone.classList.toggle("hidden", !info.parent_gone);
    pick.replaceChildren(el("option", { value: "", textContent: w.upgrade_none, selected: !current }),
      ...(info.parent_gone ? [el("option", { value: current, disabled: true, selected: true,
        textContent: fill(w.upgrade_gone_option, { name: info.parent.name }) })] : []),
      ...info.choices.map((c) => el("option", { value: c.address, textContent: c.name, selected: c.address === current })));
    head.classList.toggle("edited", current !== game);
    if (current === game) was.replaceChildren();
    else {
      const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_upgrade_undo });
      undo.addEventListener("click", () => choose(game || null));
      was.replaceChildren(el("span", { textContent: w.was.replace("{v}", info.game_parent ? info.game_parent.name : w.upgrade_none) }), undo);
    }
    kids.textContent = info.children.length
      ? fillText(w.upgrade_children, { names: info.children.map((c) => c.name).join(", ") }) : "";
    table.replaceChildren(head, ...Object.entries(info.research).map(([prop, r]) => researchRow(prop, r)));
  };
  const choose = async (parent) => {
    try {
      const res = await api().set_upgrade(u.address, parent, state.lang);
      show(res);
      say(w.saved.replace("{file}", res.saved), "ok");
      if ((state.problems || []).some((p) => p.unit)) checkMod();  // a link to a unit that's gone may be mended now
    } catch (err) { problem(err); }
  };
  pick.addEventListener("change", () => choose(pick.value || null));
  api().upgrade(u.address, state.lang).then(show).catch(problem);
  return el("div", { className: "group" }, el("h2", { textContent: w.upgrade_title }),
    el("p", { className: "muted small", textContent: w.upgrade_help }), gone, table, kids);
}

// A unit's armour, picked as one of the game's levels (StudioApi.armour / set_armour): the level's own picture is the
// shield on its card and in its build menu, so the card and the fights always match (a player's report, 2026-10-10:
// armour raised inside the armour part fought as 4 while the card still said 2)
function armourGroup(u) {
  const w = state.words;
  const can = Boolean(state.mod && u.editable);
  const pick = el("select", { disabled: !can, title: w.tip_armour_pick });
  const was = el("div", { className: "was" });
  const old = el("p", { className: "notice warn hidden", textContent: w.armour_old_way });
  const head = el("tr", {}, el("th", { textContent: w.armour_level, title: w.tip_armour_pick }), el("td", {}, pick, was));
  const label = (levels, value) => {
    const l = levels.find((x) => x.value === value);
    return l ? fill(w[l.word], { n: l.n }) : w.armour_building;
  };
  const show = (info) => {
    const current = info.value ?? info.game;
    const known = info.levels.some((l) => l.value === current);
    pick.replaceChildren(
      ...(known ? [] : [el("option", { value: "", disabled: true, selected: true, textContent: label(info.levels, current) })]),
      ...info.levels.map((l) => el("option", { value: String(l.value), textContent: fill(w[l.word], { n: l.n }),
        selected: l.value === current })));
    pick.disabled = !can || !info.editable;
    old.classList.toggle("hidden", info.old === null || info.old === undefined);
    const edited = info.value !== null && info.value !== info.game;
    head.classList.toggle("edited", edited);
    if (!edited) { was.replaceChildren(); return; }
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_armour_undo });
    undo.addEventListener("click", () => choose(null));
    was.replaceChildren(el("span", { textContent: w.was.replace("{v}", label(info.levels, info.game)) }), undo);
  };
  const choose = async (value) => {
    try {
      const res = await api().set_armour(u.address, value, state.lang);
      show(res);
      say(w.saved.replace("{file}", res.saved), "ok");
    } catch (err) { problem(err); }
  };
  pick.addEventListener("change", () => choose(pick.value === "" ? null : Number(pick.value)));
  api().armour(u.address, state.lang).then(show).catch(problem);
  return el("div", { className: "group" }, el("h2", { textContent: w.armour_title }),
    el("p", { className: "muted small", textContent: w.armour_help }), old, el("table", {}, head));
}

async function showUnit(address, via) {
  via = via || "";
  state.eraPage = null;
  if (!state.page || state.page.via !== via) state.mode = "own";  // a new way in: "only this unit" first
  state.selected = address;
  for (const b of $("unit-list").querySelectorAll("button")) {
    b.setAttribute("aria-current", String(b.dataset.address === (via || address)));  // the unit we're inside
  }
  let u;
  try { u = await api().unit(address, state.lang, via); } catch (err) { problem(err); return; }
  if (!knownNumbers) {  // each number's meaning and the game modes' names, before the rows are drawn
    try { knownNumbers = await api().numbers(state.lang); } catch { knownNumbers = null; }
  }
  state.page = { address, via };
  const inside = u.named ? u.address : via;  // the named unit its parts are opened from
  const mode = u.share ? (u.share.via ? state.mode : "shared") : "";
  const w = state.words;
  const copy = el("button", { type: "button", textContent: w.copy_address, title: w.tip_copy_address });
  copy.addEventListener("click", () => navigator.clipboard && navigator.clipboard.writeText(u.address));
  const allValues = el("button", { type: "button", textContent: w.values_open_all, title: w.tip_values_open_all,
    className: u.in_game ? "" : "hidden" });  // the All values tab shows the game's objects (a mod's new unit isn't one)
  allValues.addEventListener("click", () => openAllValues(u.address));
  const parts = [el("h1", { textContent: u.name }),
    // with the code names, the name a player knows; and the game's own line for it, as on its card in the game
    ...(state.lang === "base" && u.game_name && u.game_name !== u.name
      ? [el("div", { className: "game-name", textContent: u.game_name })] : []),
    ...(u.desc ? [el("p", { className: "unit-desc", textContent: u.desc })] : []),
    el("div", { className: "address" }, el("code", { textContent: u.address }), copy, allValues),
    el("div", { className: "meta", textContent: u.class })];
  if ((u.named || u.new) && window.BoardView) parts.push(window.BoardView.unitLink(u));  // its building (board.js)
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
  if (u.ammo_texts && u.ammo_texts.length) parts.push(ammoTextsGroup(u));
  for (const g of u.groups) {
    const table = el("table");
    for (const r of g.rows) table.append(row(u, r, mode));
    const group = el("div", { className: "group" }, el("h2", { textContent: g.name }), table);
    if (u.editable && g.rows.some((r) => r.locked)) group.append(el("p", { className: "muted small", textContent: w.locked }));
    parts.push(group);
  }
  if (u.has_armour) parts.push(armourGroup(u));
  if (u.class === "TAvionDescriptor" && (u.named || u.new) && u.editable) parts.push(roleGroup(u));
  if (u.class === "TUniteAuSolDescriptor" && (u.named || u.new) && u.editable) parts.push(groundRoleGroup(u));
  if (u.has_weapons && u.editable) parts.push(weaponsGroup(u));
  if (u.can_upgrade) parts.push(upgradeGroup(u));
  if (u.named || u.new) parts.push(unitSoundsGroup(u));  // its sounds, each changed in RUSE Decoy (decoy.js)
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
  parts.push(notesBox(`obj:${u.address}`));  // (the same note as on its All values page)
  if (u.named || u.new) {  // a unit: its model beside its values, with the Blender buttons under it
    const view = unitView(u);
    const side = el("aside", { className: "unit-side" }, view,
      lookBox(u, () => view.reload(), copyForm && copyForm.openForm), ridesInBox(u));
    $("detail").replaceChildren(...parts.slice(0, head),
      el("div", { className: "unit-page" }, el("div", { className: "unit-main" }, ...parts.slice(head)), side));
    return;
  }
  $("detail").replaceChildren(...parts);
}

// --- test the mod in the game ---
async function follow(jobId, log, done, onLine) {   // onLine: each new line as it comes (a job's card)
  let seen = 0;
  const tick = async () => {
    let j;
    try { j = await api().job(jobId, seen); } catch (err) { problem(err); done(false); return; }
    for (const line of j.lines) log.textContent += line + "\n";
    if (onLine && j.lines.length) onLine(j.lines[j.lines.length - 1]);
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
  const w = state.words;
  const showLog = { label: w.toast_log, tip: w.tip_toast_log, act: () => $("test-panel").classList.remove("hidden") };
  const card = jobCard(w.test_running);   // its latest line while the copy is built, then its result
  addToastAction(card.card, showLog);
  const finish = (ok, message, j) => {
    button.dataset.running = "0";
    button.disabled = !state.mod;
    if (state.view === "settings") renderBackup();
    if (message) lastSaid = message;
    const report = { label: w.report, tip: w.tip_report, act: () => api().report_problem(message || "").catch(() => {}) };
    card.done(ok, message, ok ? [showLog] : [showLog, ...(w.report ? [report] : [])]);
    // mistakes in the mods: each one listed with its fix, not the troubleshooter (it can't fix a mod)
    if (!ok && j && j.errors && j.errors.length) showTestProblems();
    else if (!ok) offerTroubleshoot();
  };
  try {
    const { job } = await api().test_in_game();
    follow(job, log, finish, (line) => card.line(line));
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

// Text to the clipboard: the window's clipboard call, else the old way from a hidden box. False (and says so) when
// neither works.
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); } catch {
    const box = el("textarea", { value: text, readOnly: true, className: "sr-only" });
    document.body.append(box);
    box.select();
    const copied = document.execCommand("copy");
    box.remove();
    if (!copied) { say(state.words.test_copy_failed, "error"); return false; }
  }
  return true;
}

// The test's log and its message, for a bug report or Discord
async function copyTestLog() {
  const text = $("test-log").textContent + (lastSaid ? "\n" + lastSaid : "");
  if (await copyText(text)) say(state.words.doc_copied, "ok");
}

// --- the troubleshooter (StudioApi.troubleshoot, rusemod.doctor): what can stop a test, checked in one go, each
// finding with a fix button when the app can run one; the report goes into a bug report or on Discord ---
const DOC_MARKS = { ok: "✔︎", info: "ℹ︎", warn: "⚠︎", fail: "✖︎" };  // ︎: drawn as text, not emoji
let doctorReport = "";

// A failed test: a link to the troubleshooter beside its message (a game left running from the copy, or a leftover
// copy Windows won't delete, stopped every second test for a player, 2026-09-30)
function offerTroubleshoot() {
  const w = state.words;
  const action = { label: w.doc_troubleshoot_link, tip: w.doc_intro, act: openDoctor };
  const cards = $("status").querySelectorAll(".toast.error:not(.going)");   // on the newest problem's card
  if (cards.length) addToastAction(cards[cards.length - 1], action); else toast(w.doc_intro, "error", [action]);
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
// A unit's "Sounds and animation": what it has (its engine's sounds, its voice lines) and one button that opens
// RUSE Decoy on exactly those (StudioApi.decoy_unit, DecoyView.unit). Its animations come to RUSE Decoy next.
function unitSoundsGroup(u) {
  const w = state.words;
  const name = u.name || u.address.split("/").pop();
  const says = el("p", { className: "small", textContent: w.decoy_unit_reading });
  const go = el("button", { type: "button", className: "primary", textContent: w.decoy_unit_open_all, title: w.tip_decoy_unit_open });
  const group = el("div", { className: "group" }, el("h2", { textContent: w.decoy_unit_title }), says,
    el("p", { className: "muted small", textContent: w.decoy_unit_more_all }), el("div", { className: "music-actions" }, go));
  let count = 0;
  api().decoy_unit(u.address).then((d) => {
    count = d.count + (d.clips || 0);
    says.textContent = count ? fill(w.decoy_unit_has_all, { voices: d.voices, engine: d.engine, clips: d.clips || 0 })
      : w.decoy_unit_none;
    go.disabled = !count;
  }).catch((err) => { says.textContent = (err && err.message) || String(err); });
  go.addEventListener("click", () => { window.DecoyView.unit(u.address, name, count); showView("decoy"); });
  return group;
}

// All values and files (the owner, 2026-10-22: "all values and files should be put together and just called all
// values and files"): one tab, its two parts (the All values tab and the Files tab they were) picked by the switch on
// top of each part's list
const PARTS = [["values", "values_tab", "tip_tab_values"], ["files", "files_tab", "tip_tab_files"]];

function partSwitches() {
  const w = state.words || {};
  for (const box of document.querySelectorAll(".part-switch")) {
    box.setAttribute("aria-label", w.values_files_tab || "");
    box.replaceChildren(...PARTS.map(([view, word, tip]) => {
      const b = el("button", { type: "button", className: "mode-chip", textContent: w[word] || view, title: w[tip] || "" });
      b.setAttribute("role", "radio");
      b.setAttribute("aria-checked", String(state.view === view));
      b.addEventListener("click", () => { if (state.view !== view) showView(view); });
      return b;
    }));
  }
}

function showView(view) {
  if (view === "economy") view = "ai";  // the Economy tab is the first half of AI and player settings now
  state.view = view;
  $("units-view").classList.toggle("hidden", view !== "units");
  $("nations-view").classList.toggle("hidden", view !== "nations");
  $("ai-view").classList.toggle("hidden", view !== "ai");
  $("values-view").classList.toggle("hidden", view !== "values");
  $("decoy-view").classList.toggle("hidden", view !== "decoy");
  $("files-view").classList.toggle("hidden", view !== "files");
  $("maps-view").classList.toggle("hidden", view !== "maps");
  $("settings-view").classList.toggle("hidden", view !== "settings");
  $("tab-units").setAttribute("aria-selected", String(view === "units"));
  $("tab-nations").setAttribute("aria-selected", String(view === "nations"));
  $("tab-ai").setAttribute("aria-selected", String(view === "ai"));
  $("tab-values").setAttribute("aria-selected", String(view === "values" || view === "files"));  // its two parts
  $("tab-decoy").setAttribute("aria-selected", String(view === "decoy"));
  $("tab-maps").setAttribute("aria-selected", String(view === "maps"));
  if (view === "values" || view === "files") {
    state.valuesPart = view;  // the tab opens again on the part last used
    partSwitches();
  }
  $("tab-settings").setAttribute("aria-selected", String(view === "settings"));
  $("pick-mod").classList.toggle("hidden", view === "maps");  // Units, AI and player settings, All values and RUSE Decoy edit a mod, Maps a map
  $("pick-map").classList.toggle("hidden", view !== "maps");
  // "No game index yet" (and the index's build, a minute or more) covers the tabs that read it, Units, AI and player
  // settings, All values and RUSE Decoy: the Maps tab and Settings (where the installer's clean backup shows how far it
  // is) can be used meanwhile
  $("no-index").classList.toggle("off-tab", !["units", "nations", "ai", "values", "decoy"].includes(view));
  if (view !== "decoy") window.SoundView.leave();  // a sound playing stops with its tab
  if (view === "nations") { window.NationsView.open(state.words, state.lang); return; }
  if (view === "ai") { renderPlay(); return; }
  if (view === "values") { renderValues(); return; }
  if (view === "decoy") { window.DecoyView.open(state.words, state.lang); return; }
  if (view === "files") { window.FilesView.open(state.words); return; }  // (reads the packs, not the game index)
  if (view === "settings") { renderSettings(); loadBackup(); return; }
  if (view !== "maps") return;
  const open = () => window.MapView.open(api(), state.words, state.lang).catch(problem);
  if (window.MapView) open();
  else window.addEventListener("mapview-ready", open, { once: true });
}

// --- AI and player settings, its players' half (the Economy tab before 10-22; StudioApi.economy, rusemod.economy, our
// own code; LittleGroove's Economy editor had it first): starting money, income, supply depots, production limits and
// ruse cards; the economy's values for every computer player (its computer and decoys groups: the number guide's
// "computer" values) go in the computer players' half. A change is saved in the current mod at once, for every game
// mode (the game has these values twice: its usual modes and the Nuclear mode), or for one of the two where they're
// shown apart (economyRow) ---
async function renderEconomy() {
  const w = state.words;
  $("play-players-title").textContent = w.play_players_title;
  $("play-rules-title").textContent = w.play_rules_title;
  $("play-rules-help").textContent = w.play_rules_help;
  $("economy-help").textContent = state.mod ? w.economy_help : w.no_mod;
  $("economy-buildings").textContent = w.economy_buildings;
  $("ai-all-title").textContent = w.ai_all_title;
  $("ai-all-help").textContent = w.ai_all_help;
  if (!knownNumbers) {  // each value's meaning, from the number guide (rusemod/numberinfo.toml)
    try { knownNumbers = await api().numbers(state.lang); } catch { knownNumbers = null; }
  }
  let data;
  try { data = await api().economy(state.lang); } catch (err) { problem(err); return; }
  if (state.view !== "ai") return;  // another tab was picked meanwhile
  const groups = data.groups.filter((g) => g.rows.length);
  const depotLine = el("p", { className: "muted small", title: w.tip_economy_depot });
  const depotMaps = el("div", { className: "economy-depots" });  // Depots on the maps (renderEconomyDepots)
  const drawn = (g) => {
    const table = el("table");
    for (const r of g.rows) table.append(economyRow(r, g.id === "supply" ? () => showEconomyDepot(depotLine) : null));
    const group = el("div", { className: "group" }, el("h2", { textContent: w[`economy_group_${g.id}`] || g.id }), table);
    if (g.id === "supply") group.append(depotLine, depotMaps);
    return group;
  };
  // each group in its part of the tab (StudioApi.economy section): what players get, the game rules, the computers'
  const none = () => [el("p", { className: "muted", textContent: w.economy_none })];
  for (const [section, box] of [["players", "economy-groups"], ["rules", "rules-groups"], ["computers", "ai-economy-groups"]]) {
    const mine = groups.filter((g) => (g.section || "players") === section);
    $(box).replaceChildren(...(data.ready && mine.length ? mine.map(drawn) : none()));
  }
  showEconomyDepot(depotLine);
  renderEconomyDepots(depotMaps);
}

// Depots on the maps (StudioApi.economy_depots / economy_depots_set, the mod's depots.toml): every depot's trucks on
// every map, or on the one map picked (the owner, 2026-10-10: "you would check like one map or all the maps. And then
// if it was just one map, you would choose the specific map"); the build sets each depot by it, and a depot given its
// own trucks on the Maps tab keeps them. How often convoys leave is one value for every map (the row above).
async function renderEconomyDepots(box) {
  const w = state.words;
  let data;
  try { data = await api().economy_depots(state.lang); } catch (err) { box.replaceChildren(); problem(err); return; }
  const m = data.money || {};
  const worth = (trucks) => Math.round(trucks * m.per_convoy * m.per_truck).toLocaleString();
  const ruleText = (r) => r.times !== null && r.times !== undefined ? w.economy_depots_x.replace("{n}", String(r.times))
    : w.economy_depots_n.replace("{n}", Number(r.trucks).toLocaleString());
  const save = async (where, trucks, times) => {
    try {
      await api().economy_depots_set(where, trucks, times);
      say(w.saved.replace("{file}", "depots.toml"), "ok");
      renderEconomyDepots(box);
    } catch (err) { problem(err); }
  };
  // where: all maps, or one map picked from the game's list
  const all = el("input", { type: "radio", name: "depots-where", checked: true, disabled: !data.can });
  const one = el("input", { type: "radio", name: "depots-where", disabled: !data.can });
  const pick = el("select", { className: "small", disabled: true, title: w.tip_economy_depots_where },
    ...data.maps.map((x) => el("option", { value: x.pack, textContent: x.name })));
  for (const r of [all, one]) r.addEventListener("change", () => { pick.disabled = !one.checked; preview(); });
  const where = el("div", { className: "economy-depots-row", title: w.tip_economy_depots_where },
    el("label", {}, all, " ", w.economy_depots_all), " ",
    el("label", {}, one, " ", w.economy_depots_one), " ", pick);
  // how much: times their trucks, or trucks each
  const number = el("input", { type: "number", min: "0", step: "any", value: "2", className: "short",
    disabled: !data.can, title: w.tip_economy_depots_amount });
  const how = el("select", { className: "small", disabled: !data.can, title: w.tip_economy_depots_amount },
    el("option", { value: "times", textContent: w.scen_depots_times }),
    el("option", { value: "trucks", textContent: w.scen_depots_each }));
  const apply = el("button", { type: "button", className: "small", textContent: w.scen_depots_apply,
    disabled: !data.can, title: w.tip_economy_depots_amount });
  const said = el("span", { className: "muted small" });
  function preview() {
    const n = Number(number.value);
    const ok = number.value.trim() !== "" && Number.isFinite(n) && n >= 0 && (how.value === "times" || Number.isInteger(n));
    number.setAttribute("aria-invalid", String(!ok));
    said.textContent = ok && m.ready ? w.economy_depots_preview.replace("{trucks}", String(m.usual))
      .replace("{money}", worth(how.value === "times" ? m.usual * n : n)) : "";
    return ok ? n : null;
  }
  number.addEventListener("input", preview);
  how.addEventListener("change", () => { number.value = how.value === "trucks" ? "50" : "2"; preview(); });
  apply.addEventListener("click", () => {
    const n = preview();
    if (n === null) { number.focus(); return; }
    const at = one.checked ? pick.value : "all";
    save(at, how.value === "trucks" ? n : null, how.value === "times" ? n : null);
  });
  const amount = el("div", { className: "economy-depots-row", title: w.tip_economy_depots_amount },
    number, " ", how, " ", apply, " ", said);
  // the changes made so far, each with a way to take it off
  const rules = data.rules.length ? el("ul", { className: "economy-depots-rules" }, ...data.rules.map((r) => {
    const off = el("button", { type: "button", className: "link", textContent: w.economy_depots_take_off,
      title: w.tip_economy_depots_take_off, disabled: !data.can });
    off.addEventListener("click", () => save(r.map, null, null));
    const name = r.map === "all" ? w.economy_depots_all : r.name;
    return el("li", {}, w.economy_depots_rule.replace("{map}", name).replace("{what}", ruleText(r)), " ", off);
  })) : el("p", { className: "muted small", textContent: w.economy_depots_none });
  box.replaceChildren(el("h3", { textContent: w.economy_depots_title }),
    el("p", { className: "muted small", textContent: data.can ? w.economy_depots_help : w.no_mod }),
    where, amount, rules, el("p", { className: "muted small", textContent: w.economy_depots_often }));
  preview();
}

// Under Supply depots: what a depot of the game's usual trucks holds with these values (StudioApi.depot_money), and
// where a depot's own trucks are changed (the owner, 2026-10-10: "no way to increase max amt of money in supply depot")
async function showEconomyDepot(line) {
  let m;
  try { m = await api().depot_money(); } catch { line.textContent = ""; return; }
  line.textContent = m.ready ? state.words.economy_depot_money
    .replace("{trucks}", String(m.usual))
    .replace("{money}", Math.round(m.usual * m.per_convoy * m.per_truck).toLocaleString()) : "";
}

// One economy value: its name, what it does (the number guide, rusemod/numberinfo.toml) and its boxes. Where the game's
// usual modes and the Nuclear mode have it apart (r.split: the game's two copies differ, or the mod's do), each mode
// has its own boxes (the owner, 2026-10-17: "separate normal and nuclear for sure"); elsewhere one change sets both.
function economyRow(r, saved = null) {
  const w = state.words;
  const th = el("th", { textContent: r.label });
  if (state.lang !== "base" && r.label !== r.prop) th.append(el("small", { textContent: r.prop }));
  const entry = numberEntry("TTunableConstante", r.prop);
  if (entry) {
    th.title = numberTip(entry);
    th.append(el("small", { className: "about", textContent: entry.does }));
  }
  const tr = el("tr", {}, th);
  const cell = el("td");
  const edited = new Set();  // the modes the mod changes
  const part = (mode, game, value) => {
    game = r.list ? game : [game];
    let mine = value === null || value === undefined ? null : r.list ? value : [value];
    // a colour (r.colour: [red, green, blue, how solid]) is a colour picker and a 0 to 255 box; other values a box each
    const boxes = r.colour ? colourBoxes(r) : (mine || game).map((n, i) => numberBox(r, n, r.list ? `${r.label} [${i}]` : r.label));
    const read = () => r.colour ? [...hexColour(boxes[0].value), readBox(boxes[1])] : boxes.map(readBox);
    const plain = el("span", { className: "muted small number-plain" });
    const was = el("div", { className: "was" });
    // in plain units only where that says more than the number ("25%" for 0.25; not "about 200 $" for 200)
    const scale = entry && knownNumbers && knownNumbers.plain[entry.unit];
    const showPlain = (numbers) => {
      plain.textContent = r.list || !scale || scale[0] === 1 ? "" : numberPlain(entry, Number(numbers[0]));
    };
    const show = (numbers) => {
      if (r.colour) {
        boxes[0].value = colourHex(numbers);
        boxes[1].value = String(numbers[3]);
      } else {
        boxes.forEach((b, i) => { if (b.type === "checkbox") b.checked = Boolean(numbers[i]); else b.value = String(numbers[i]); });
      }
      boxes.forEach((b) => b.setAttribute("aria-invalid", "false"));
      showPlain(numbers);
    };
    const showWas = () => {
      if (mine === null) edited.delete(mode); else edited.add(mode);
      tr.classList.toggle("edited", edited.size > 0);
      if (mine === null) { was.replaceChildren(); return; }
      const undo = el("button", { type: "button", className: "link", textContent: w.reset,
        title: mode ? w.tip_economy_reset_one : w.tip_economy_reset });
      undo.addEventListener("click", async () => {
        try {
          await api().economy_reset(r.prop, mode);
          mine = null;
          show(game);
          showWas();
          say("");
          if (saved) saved();
        } catch (err) { problem(err); }
      });
      const gameText = r.colour ? colourText(game) : game.join(" · ");
      was.replaceChildren(...(r.colour ? [colourSwatch(game), " "] : []),
        el("span", { textContent: w.was.replace("{v}", gameText) }), undo);
    };
    const save = async (box) => {
      const numbers = read();
      const bad = r.colour ? (Number.isInteger(numbers[3]) && numbers[3] >= 0 && numbers[3] <= 255 ? -1 : 1)
        : numbers.findIndex((n) => !Number.isFinite(n));
      boxes.forEach((b, i) => b.setAttribute("aria-invalid", String(i === bad)));
      if (bad >= 0) { box.focus(); return; }
      try {
        const res = await api().economy_edit(r.prop, r.list ? numbers : numbers[0], mode);
        const got = r.list ? res.value : [res.value];
        show(got);
        mine = sameNumbers(got, game) ? null : got;
        showWas();
        say(w.saved.replace("{file}", res.saved), "ok");
        if (saved) saved();
      } catch (err) { problem(err); }
    };
    for (const box of boxes) box.addEventListener("change", () => save(box));
    if (r.colour) show(mine || game); else showPlain(mine || game);
    showWas();
    const row = el("div", { className: "boxes" }, ...boxes, plain);
    if (mode) {
      row.prepend(el("span", { className: "mode-name small", textContent: mode === "atomic" ? w.economy_nuclear : w.economy_normal,
        title: mode === "atomic" ? w.tip_economy_nuclear : w.tip_economy_normal }));
    }
    return el("div", { className: mode ? `economy-mode economy-${mode}` : "economy-mode" }, row, was);
  };
  if (r.split) {
    cell.append(part("normal", r.game, r.value), part("atomic", r.atomic === null ? r.game : r.atomic, r.atomic_value));
  } else {
    cell.append(part(null, r.game, r.value));
  }
  tr.append(cell);
  return tr;
}

// --- the AI tab (StudioApi.ai, rusemod.ai, our own code; LittleGroove's AI editor had it first): how the computer
// players play (Default, the difficulties and the profiles the game's lobby picks: a set of values each, mixed in a
// battle), the units they're keener to build, and the ruse cards (every player's). A change is saved in the current
// mod at once ---
// The whole AI and player settings tab: the players' half (renderEconomy) and the computer players' (renderAI, which
// alone is drawn again after a change of the computer players': what each value comes to in a battle)
async function renderPlay() {
  renderEconomy();
  await renderAI();
}

async function renderAI() {
  const w = state.words;
  $("ai-title").textContent = w.ai_title;
  $("ai-intro").textContent = w.ai_intro;
  $("play-ai-title").textContent = w.play_ai_title;
  $("ai-help").textContent = state.mod ? w.ai_help : w.no_mod;
  $("ai-how-title").textContent = w.ai_how_title;
  $("ai-mix").textContent = w.ai_mix;
  $("ai-bonus-title").textContent = w.ai_bonus_title;
  $("ai-bonus-help").textContent = w.ai_bonus_help;
  $("ai-cards-title").textContent = w.ai_cards_title;
  $("ai-cards-help").textContent = w.ai_cards_help;
  renderAIScripts();  // its own list, read once per language
  let data;
  try { data = await api().ai(state.lang); } catch (err) { problem(err); return; }
  if (state.view !== "ai") return;  // another tab was picked meanwhile
  if (!data.ready) {
    $("ai-pick").replaceChildren();
    $("ai-hint").textContent = "";
    $("ai-groups").replaceChildren(el("p", { className: "muted", textContent: w.ai_none }));
    $("ai-bonuses").replaceChildren();
    $("ai-cards").replaceChildren();
    return;
  }
  if (!data.profiles.some((p) => p.id === state.aiProfile)) state.aiProfile = data.profiles.length ? data.profiles[0].id : null;
  state.aiData = data;  // the battle values and the bonus lists' names, for each row (aiRow, aiValue)
  if (!knownNumbers) {  // each value's meaning, from the number guide (rusemod/numberinfo.toml)
    try { knownNumbers = await api().numbers(state.lang); } catch { knownNumbers = null; }
    if (state.view !== "ai") return;
  }
  renderAIPick(data);
  renderAIProfile(data);
  $("ai-bonuses").replaceChildren(...data.bonuses.map((b) => {
    const table = el("table");
    for (const r of b.rows) table.append(aiRow(b.id, r, r.list ? renderAI : null));
    return el("div", { className: "group" }, aiBonusSummary(b), table);
  }));
  renderAICards(data);
}

// A bonus in one sentence: in which battles (game modes, difficulties, profiles) which units get how much more
// preference (the owner, 2026-10-17: "not very clear what profile goes to what number ... or the unit by number").
// An empty list matches any.
function aiBonusSummary(b) {
  const w = state.words;
  const row = (prop) => b.rows.find((r) => r.prop === prop);
  const all = (state.aiData && state.aiData.choices) || {};
  const names = (prop, any) => {  // an empty list, or one holding every choice there is: "any difficulty"
    const r = row(prop);
    const now = r ? (r.value === null ? r.game : r.value) : [];
    const every = all[prop] && all[prop].length && all[prop].every((c) => now.includes(c.n));
    return r && r.names && r.names.length && !every ? r.names.join(", ") : w[any];
  };
  const value = row("BonusValue");
  const v = value ? (value.value === null ? value.game : value.value) : 0;
  return el("p", { className: "ai-bonus-summary", textContent: fill(w.ai_bonus_summary, {
    modes: names("WarModes", "ai_bonus_any_mode"), difficulties: names("AIDifficulties", "ai_bonus_any_difficulty"),
    profiles: names("AIProfiles", "ai_bonus_any_profile"), v: (v > 0 ? "+" : "") + Number(v).toLocaleString(),
    units: names("UnitIDs", "ai_bonus_any_unit") }) });
}

// A value as its unit shows it: "3,000 m", "5 min", "$100", "50%", else the number.
function aiShown(entry, v) {
  const w = state.words, p = entry && knownNumbers && knownNumbers.plain[entry.unit];
  if (!p || !Number.isFinite(Number(v))) return Number(v).toLocaleString();
  const x = Number(v) / p[0];
  const n = Math.abs(x) >= 100 ? Math.round(x).toLocaleString() : Number(x.toPrecision(3)).toLocaleString();
  return entry.unit === "money" ? `$${n}` : `${n} ${w[p[1]] || ""}`.trim();
}

// What a value comes to in a battle (StudioApi.ai battle: the game's rule mixing Default, the difficulty and the
// personality): each difficulty's, and the personalities whose own value wins on any difficulty.
function aiBattleLine(r) {
  const w = state.words, data = state.aiData;
  const b = data && data.battle && data.battle[r.prop];
  if (!b || r.cls !== "TIAProfil") return null;
  const entry = numberEntry(r.cls, r.prop);
  const parts = b.difficulties.map(([name, v]) => `${name} ${aiShown(entry, v)}`).join(" · ");
  const wins = b.personalities.map(([name, v]) => `${name} ${aiShown(entry, v)}`).join(", ");
  return el("div", { className: "small ai-battle", title: w.tip_ai_battle,
    textContent: fill(w.ai_battle, { values: parts }) + (wins ? ` — ${fill(w.ai_battle_wins, { list: wins })}` : "") });
}

function renderAIPick(data) {
  const w = state.words, words = data.words || {};
  const button = (p) => {
    // the number the game gives it (a bonus's lists name them by it), beside its name
    const b = el("button", { type: "button", className: "chip",
      textContent: p.kind === "default" ? w.ai_default : `${p.name || ""} (${p.index})`.trim() });
    b.setAttribute("aria-pressed", String(p.id === state.aiProfile));
    b.addEventListener("click", () => { state.aiProfile = p.id; renderAI(); });  // fresh: another set may have changed
    return b;
  };
  const row = (label, kind) => {
    const ps = data.profiles.filter((p) => p.kind === kind);
    if (!ps.length) return null;
    return el("div", { className: "ai-pick-row" }, el("span", { className: "muted small", textContent: label }),
      el("div", { className: "chips" }, ...ps.map(button)));
  };
  $("ai-pick").replaceChildren(...[row("", "default"), row(words.difficulty || "", "difficulty"),
    row(words.profile || "", "personality")].filter(Boolean));
}

function renderAIProfile(data) {
  const w = state.words;
  const p = data.profiles.find((x) => x.id === state.aiProfile);
  $("ai-hint").textContent = (p && p.hint) || "";
  if (!p) { $("ai-groups").replaceChildren(); return; }
  // every value of the set (StudioApi.ai): one it doesn't list in the game shows the 0 the game counts (aiRow)
  $("ai-groups").replaceChildren(...p.groups.filter((g) => g.rows.length).map((g) => {
    const table = el("table");
    for (const r of g.rows) table.append(aiRow(p.id, r, renderAI));  // drawn again: what it comes to in a battle
    return el("div", { className: "group" }, el("h2", { textContent: w[`ai_group_${g.id}`] || g.id }), table);
  }), notesBox(`obj:${p.id}`));
}

// A private Notes box (LittleGroove's): the modder's own words about this unit, object or profile, kept in the mod's
// notes.json (StudioApi.note / note_set) and saved when the box is left; never in the game's data or an exported mod.
function notesBox(key, kind = "mod") {
  const w = state.words;
  const area = el("textarea", { className: "notes-area", rows: 3, placeholder: w.notes_hint, title: w.tip_notes,
    disabled: true });
  area.setAttribute("aria-label", w.notes_title);
  const said = el("div", { className: "muted small" });
  let last = "";
  api().note(key, kind).then((res) => {
    area.value = last = res.text;
    area.disabled = !res.can;
    if (!res.can) said.textContent = w.no_mod;
  }).catch(() => { said.textContent = w.no_mod; });
  area.addEventListener("blur", async () => {
    if (area.value === last) return;
    try {
      const res = await api().note_set(key, area.value, kind);
      last = area.value = res.text;
      said.textContent = w.notes_saved;
    } catch (err) { problem(err); }
  });
  return el("div", { className: "group notes" }, el("h2", { textContent: w.notes_title, title: w.tip_notes }), area, said);
}

function renderAICards(data) {
  const w = state.words, cards = data.cards;
  if (!cards.length) { $("ai-cards").replaceChildren(); return; }
  const props = ["LifeDuration", "ShowInMenu", "PositionInMenu"];
  const label = (prop) => (cards.flatMap((c) => c.rows).find((r) => r.prop === prop) || {}).label || prop;
  const head = el("tr", {}, el("th"), ...props.map((prop) => {
    const entry = numberEntry("TBluffCardDescriptor", prop);  // what it does, from the number guide
    const th = el("th", { textContent: label(prop), title: numberTip(entry) });
    if (entry) th.classList.add("has-meaning");
    return th;
  }));
  const table = el("table", { className: "ai-cards" }, head);
  for (const c of cards) {
    const th = el("th", { textContent: c.name });
    if (c.about) th.append(el("small", { className: "about", textContent: c.about }));
    const tr = el("tr", {}, th);
    for (const prop of props) {
      const r = c.rows.find((x) => x.prop === prop);
      if (r) tr.append(aiValue(c.id, r).cell);
      else tr.append(el("td", { className: "muted small", textContent: prop === "ShowInMenu" ? w.ai_not_in_menu : "" }));
    }
    table.append(tr);
  }
  $("ai-cards").replaceChildren(el("div", { className: "group" }, table));
}

// One value of the AI tab, in its own cell: its box (or boxes, for a list), "was … Undo" once changed, the names of a
// list's numbers (units, game modes, difficulties, profiles), and for a difficulty's or profile's value whether it is
// Default's (then it doesn't count: StudioApi.ai). `after`: called once a change is saved (a list's names come from
// the game index again).
// A bonus's list item picked by name (difficulty, profile, game mode, unit: StudioApi.ai choices), the number the
// game uses beside it; a number with no name stays as itself.
function aiChoiceBox(r, value, label, choices) {
  const box = el("select", { disabled: !state.mod, title: state.words.tip_ai_choice });
  const option = (c) => el("option", { value: String(c.n),
    textContent: c.nation ? `${c.name} · ${c.nation} (${c.n})` : `${c.name} (${c.n})` });
  box.append(...choices.map(option));
  const ensure = (n) => {
    if (![...box.options].some((o) => o.value === String(n))) box.append(option({ n, name: String(n) }));
    box.value = String(n);
  };
  ensure(value);
  box.ensure = ensure;
  box.setAttribute("aria-label", label);
  return box;
}

function aiValue(target, r, after = null) {
  const w = state.words;
  const game = r.list ? r.game : [r.game];
  let mine = r.value === null ? null : r.list ? r.value : [r.value];
  const choices = state.aiData && state.aiData.choices && state.aiData.choices[r.prop];
  const boxes = (mine || game).map((n, i) => {
    const label = r.list ? `${r.label} [${i}]` : r.label;
    return choices ? aiChoiceBox(r, n, label, choices) : numberBox(r, n, label);
  });
  const was = el("div", { className: "was" });
  const note = el("div", { className: "muted small" });
  const entry = numberEntry(r.cls, r.prop);
  const plain = el("span", { className: "muted small number-plain" });  // "about 3,000 m"
  const showPlain = () => { plain.textContent = r.list || choices ? "" : numberPlain(entry, readBox(boxes[0])); };
  const cell = el("td", {}, el("div", { className: "boxes" }, ...boxes, plain), was, note);
  const showNote = (same) => {
    // a picker already shows the names; a plain list of numbers gets them below
    note.textContent = [r.names && !choices ? r.names.join(" · ") : "", same ? w.ai_same_default : ""]
      .filter(Boolean).join(" — ");
  };
  const show = (numbers) => boxes.forEach((b, i) => {
    if (b.type === "checkbox") b.checked = Boolean(numbers[i]);
    else if (b.ensure) b.ensure(numbers[i]);
    else b.value = String(numbers[i]);
    b.setAttribute("aria-invalid", "false");
  });
  for (const b of boxes) b.addEventListener("input", showPlain);
  showPlain();
  const showWas = () => {
    cell.classList.toggle("edited", mine !== null);
    if (mine === null) { was.replaceChildren(); return; }
    const undo = el("button", { type: "button", className: "link", textContent: w.reset, title: w.tip_ai_reset });
    undo.addEventListener("click", async () => {
      try {
        const res = await api().ai_reset(target, r.prop);
        mine = null;
        show(game);
        showPlain();
        showWas();
        showNote(res.same_default);
        say("");
        if (after) after();
      } catch (err) { problem(err); }
    });
    was.replaceChildren(el("span", { textContent: w.was.replace("{v}", game.join(" · ")) }), undo);
  };
  const save = async (box) => {
    const numbers = boxes.map(readBox);
    const bad = numbers.findIndex((n) => !Number.isFinite(n));
    boxes.forEach((b, i) => b.setAttribute("aria-invalid", String(i === bad)));
    if (bad >= 0) { box.focus(); return; }
    try {
      const res = await api().ai_edit(target, r.prop, r.list ? numbers : numbers[0]);
      const value = r.list ? res.value : [res.value];
      show(value);
      showPlain();
      mine = sameNumbers(value, game) ? null : value;
      showWas();
      showNote(res.same_default);
      say(w.saved.replace("{file}", res.saved), "ok");
      if (after) after();
    } catch (err) { problem(err); }
  };
  for (const box of boxes) box.addEventListener("change", () => save(box));
  showWas();
  showNote(r.same_default);
  return { cell };
}

// One row of the AI tab: the value's name, what it does in the game (the number guide; its name shows the whole
// entry and how sure we are when hovered), its box, and for a profile's value what it comes to in a battle.
function aiRow(target, r, after = null) {
  const w = state.words;
  const th = el("th", { textContent: r.label });
  if (state.lang !== "base" && r.label !== r.prop) th.append(el("small", { textContent: r.prop }));
  // a value the game doesn't set for this set (StudioApi.ai unlisted): it counts as 0 until the mod gives it a number
  if (r.unlisted) th.append(el("small", { className: "ai-added", textContent: w.ai_unlisted, title: w.tip_ai_unlisted }));
  const entry = numberEntry(r.cls, r.prop);
  if (entry) {
    th.title = numberTip(entry);  // (no dotted underline: the meaning is written out below the name)
    th.append(el("small", { className: "about", textContent: entry.does }));
    if (entry.sure === "name") th.append(el("small", { className: "muted ai-sure", textContent: w.ai_sure_name }));
  }
  const { cell } = aiValue(target, r, after);
  const battle = aiBattleLine(r);
  if (battle) cell.append(battle);
  return el("tr", {}, th, cell);
}

// The game's map and mission scripts, shown as Python to read (StudioApi.ai_scripts / ai_script; LittleGroove's
// script viewer): picked from a list grouped by map, one turned into text at a time (a big one takes seconds)
async function renderAIScripts() {
  const w = state.words;
  $("ai-scripts-title").textContent = w.ai_scripts_title;
  $("ai-scripts-help").textContent = w.ai_scripts_help;
  $("ai-script-copy").textContent = w.ai_scripts_copy;
  $("ai-script-copy").title = w.tip_ai_scripts_copy;
  $("ai-script-edit").textContent = w.ai_script_edit;
  $("ai-script-editing-help").textContent = w.ai_script_editing_help;
  for (const [id, word, tip] of [["ai-script-check", "ai_script_check", "tip_ai_script_check"],
    ["ai-script-save", "ai_script_save", "tip_ai_script_save"], ["ai-script-reset", "ai_script_reset", "tip_ai_script_reset"],
    ["ai-script-close", "ai_script_close", "tip_ai_script_close"]]) {
    $(id).textContent = w[word];
    $(id).title = w[tip] || "";
  }
  $("ai-script-area").title = w.tip_ai_script_area;
  $("ai-script").title = w.tip_ai_script_pick;
  $("ai-outline-title").textContent = w.ai_outline_title;
  $("ai-outline-title").title = w.tip_ai_outline;
  $("ai-ref-title").textContent = w.ai_ref_title;
  $("ai-ref-title").title = w.tip_ai_ref;
  $("ai-ref-find").placeholder = w.ai_ref_find;
  $("ai-ref-find").title = w.tip_ai_ref_find;
  $("ai-ref-kind").title = w.tip_ai_ref_kind;
  renderScriptEditButton();
  const pick = $("ai-script");
  if (pick.dataset.lang === state.lang) return;  // built for this language already: the script shown stays as it is
  if (!state.aiScripts || state.aiScripts.lang !== state.lang) {
    try { state.aiScripts = { lang: state.lang, ...(await api().ai_scripts(state.lang)) }; } catch (err) { problem(err); return; }
  }
  pick.dataset.lang = state.lang;
  const { scripts, missing } = state.aiScripts;
  pick.disabled = Boolean(missing);
  if (missing) {
    pick.replaceChildren();
    $("ai-script-about").textContent = fillText(w.ai_scripts_missing, { why: missing });
    return;
  }
  const groups = new Map();
  for (const s of scripts) {
    if (!groups.has(s.map)) groups.set(s.map, el("optgroup", { label: s.map }));
    // a script the mod changes says so in the list
    groups.get(s.map).append(el("option", { value: s.path, textContent: [s.part, s.file].filter(Boolean).join(" · ")
      + (s.mine ? `  ✎ ${w.ai_scripts_changed}` : ""), title: s.detail, selected: s.path === state.aiScriptPath }));
  }
  pick.replaceChildren(el("option", { value: "", textContent: w.ai_scripts_pick, disabled: true,
    selected: !state.aiScriptPath }), ...groups.values());
  if (state.aiScriptPath) showAIScript(state.aiScriptPath);
}

async function showAIScript(path) {
  const w = state.words, s = (state.aiScripts.scripts || []).find((x) => x.path === path);
  if (!s) return;
  if (state.aiScriptPath !== path) closeScriptEditor();  // another script: the editor starts again on it
  state.aiScriptPath = path;
  const name = `${s.map} · ${[s.part, s.file].filter(Boolean).join(" · ")}`;
  $("ai-script-about").textContent = fillText(w.ai_scripts_opening, { name });
  $("ai-script-copy").disabled = true;
  $("ai-script-edit").disabled = true;
  $("ai-script").disabled = true;  // one at a time
  try {
    const res = await api().ai_script(path, "mod");
    if (state.aiScriptPath !== path) return;
    state.aiScript = { ...res, name, detail: s.detail };
    $("ai-script-text").textContent = res.mine ?? res.text;  // what the game will run with the mod
    if ($("ai-script-editor").classList.contains("hidden")) $("ai-script-text").classList.remove("hidden");
    $("ai-script-about").textContent = fillText(w.ai_scripts_shown, { name, n: res.lines, file: s.detail })
      + (res.mine !== null && res.mine !== undefined ? " " + w.ai_script_mine : "");
    $("ai-script-copy").disabled = false;
  } catch (err) { problem(err); $("ai-script-about").textContent = ""; } finally {
    $("ai-script").disabled = false;
    renderScriptEditButton();
  }
}

async function copyAIScript() {
  if (await copyText($("ai-script-text").textContent)) say(state.words.ai_scripts_copied, "ok");
}

// --- changing a mission script (StudioApi.ai_script_check / ai_script_save / ai_script_reset / script_outline /
// script_reference; LittleGroove's Mission Script editor): the whole text, checked with the game's own Python before
// it's saved in the mod, the mission's steps to jump to, and his reference of the game's script parts to insert ---
function renderScriptEditButton() {
  const w = state.words, b = $("ai-script-edit"), res = state.aiScript;
  const why = !res ? w.tip_ai_script_edit : res.compiler_missing ? fillText(w.ai_script_no_compiler, { why: res.compiler_missing })
    : !state.mod ? w.no_mod : w.tip_ai_script_edit;
  b.disabled = !res || Boolean(res.compiler_missing) || !state.mod || !$("ai-script-editor").classList.contains("hidden");
  b.title = why;
}

let scriptSaved = "";  // the editor's text as last saved or opened: anything else is "not saved yet"

function editAIScript() {
  const res = state.aiScript;
  if (!res) return;
  const area = $("ai-script-area");
  area.value = res.mine ?? res.text;
  scriptSaved = area.value;
  $("ai-script-text").classList.add("hidden");
  $("ai-script-editor").classList.remove("hidden");
  renderScriptEditButton();
  scriptState();
  refreshOutline();
  if (!$("ai-ref-list").childNodes.length) findScriptParts();
  area.focus();
}

function closeScriptEditor() {
  $("ai-script-editor").classList.add("hidden");
  if (state.aiScript) $("ai-script-text").classList.remove("hidden");
  renderScriptEditButton();
}

function scriptState(text, kind) {
  const w = state.words, s = $("ai-script-state"), changed = $("ai-script-area").value !== scriptSaved;
  s.textContent = text || (changed ? w.ai_script_unsaved : "");
  s.className = "small ai-script-state" + (kind ? " " + kind : changed ? " warn" : "");
}

// Select line `n` of the editor's text, and scroll to it
function goToLine(n) {
  const area = $("ai-script-area"), lines = area.value.split("\n");
  if (!n || n > lines.length) return;
  const start = lines.slice(0, n - 1).reduce((sum, l) => sum + l.length + 1, 0);
  area.focus();
  area.setSelectionRange(start, start + lines[n - 1].length);
  area.scrollTop = Math.max(0, (n - 5) * (area.scrollHeight / Math.max(lines.length, 1)));
}

async function checkAIScript() {
  const w = state.words;
  scriptState(w.ai_script_checking);
  let res;
  try { res = await api().ai_script_check(state.aiScriptPath, $("ai-script-area").value); } catch (err) { problem(err); scriptState(); return; }
  if (res.ok) { scriptState(w.ai_script_ok, "ok"); return true; }
  scriptState(res.line ? fill(w.ai_script_bad, { line: res.line, error: res.error }) : res.error, "error");
  goToLine(res.line);
  return false;
}

async function saveAIScript() {
  const w = state.words, text = $("ai-script-area").value;
  let res;
  try { res = await api().ai_script_save(state.aiScriptPath, text, "mod"); } catch (err) {
    problem(err);
    const m = /\(line (\d+)\)/.exec((err && err.message) || "");
    if (m) goToLine(Number(m[1]));
    return;
  }
  state.aiScript = { ...state.aiScript, ...res };
  scriptSaved = text;
  const mine = res.mine !== null && res.mine !== undefined;
  scriptState(mine ? w.ai_script_saved_here : w.ai_script_game_again, "ok");
  say(fill(mine ? w.ai_script_saved : w.ai_script_back, { name: state.aiScript.name }), "ok");
  $("ai-script-text").textContent = res.mine ?? res.text;
  markScriptInList(mine);
  refreshOutline();
}

async function resetAIScript() {
  const w = state.words;
  let res;
  try { res = await api().ai_script_reset(state.aiScriptPath, "mod"); } catch (err) { problem(err); return; }
  state.aiScript = { ...state.aiScript, ...res };
  $("ai-script-area").value = res.text;
  scriptSaved = res.text;
  $("ai-script-text").textContent = res.text;
  scriptState(w.ai_script_game_again, "ok");
  say(fill(w.ai_script_back, { name: state.aiScript.name }), "ok");
  markScriptInList(false);
  refreshOutline();
}

// The list's line for the script shown says whether the mod changes it
function markScriptInList(mine) {
  const w = state.words, s = (state.aiScripts.scripts || []).find((x) => x.path === state.aiScriptPath);
  if (!s) return;
  s.mine = mine;
  const option = [...$("ai-script").options].find((o) => o.value === s.path);
  if (option) option.textContent = [s.part, s.file].filter(Boolean).join(" · ") + (mine ? `  ✎ ${w.ai_scripts_changed}` : "");
}

let outlineTimer = null;
async function refreshOutline() {
  const w = state.words, text = $("ai-script-area").value;
  let res;
  try { res = await api().script_outline(text); } catch { res = { steps: [] }; }
  $("ai-outline").replaceChildren(...(res.steps.length ? res.steps.map((st) => {
    const b = el("button", { type: "button", className: "link", title: st.line ? fill(w.tip_ai_outline_step, { line: st.line }) : w.tip_ai_outline,
      textContent: st.label || st.ir });
    b.addEventListener("click", () => goToLine(st.line));
    return el("li", { className: `outline-${st.kind || "action"}`, style: `padding-left: ${Math.min(st.depth, 8) * 12}px` }, b);
  }) : [el("li", { className: "muted small", textContent: w.ai_outline_none })]),
    ...(res.more ? [el("li", { className: "muted small", textContent: fill(w.ai_outline_more, { n: res.steps.length, more: res.more }) })] : []));
}

let refTimer = null;
async function findScriptParts() {
  const w = state.words, words = $("ai-ref-find").value.trim(), kind = $("ai-ref-kind").value;
  let res;
  try { res = await api().script_reference(words, kind); } catch (err) { problem(err); return; }
  const pick = $("ai-ref-kind");
  if (pick.options.length !== res.kinds.length + 1) {
    const keep = pick.value;
    pick.replaceChildren(el("option", { value: "", textContent: w.ai_ref_kind_all }),
      ...res.kinds.map((k) => el("option", { value: k, textContent: k })));
    pick.value = keep;
  }
  $("ai-ref-list").replaceChildren(...(res.classes.length ? res.classes.map((c) => {
    const b = el("button", { type: "button", title: `${c.help || c.label}\n${c.name} · ${c.kind} · ${c.category}`,
      textContent: c.label });
    b.append(el("small", { textContent: ` ${c.name}` }));
    b.addEventListener("click", () => showScriptPart(c));
    return el("li", {}, b);
  }) : [el("li", { className: "muted small", textContent: w.ai_ref_none })]));
}

function showScriptPart(c) {
  const w = state.words;
  const insert = el("button", { type: "button", className: "small", textContent: w.ai_ref_insert, title: w.tip_ai_ref_insert });
  insert.addEventListener("click", () => {
    const area = $("ai-script-area"), at = area.selectionStart, text = area.value;
    const lineStart = text.lastIndexOf("\n", at - 1) + 1;  // a line of its own, above the cursor's
    area.value = text.slice(0, lineStart) + c.snippet + "\n" + text.slice(lineStart);
    area.focus();
    area.setSelectionRange(lineStart, lineStart + c.snippet.length);
    scriptState();
    refreshOutline();  // the steps' lines moved down by one
  });
  const rows = c.params.map((p) => el("tr", { title: p.help || "" }, el("th", { textContent: p.name }),
    el("td", { textContent: `${p.type || ""}${p.default !== null && p.default !== undefined ? ` = ${p.default}` : ""}${p.required ? " *" : ""}` })));
  $("ai-ref-detail").replaceChildren(el("strong", { textContent: c.label }), el("code", { textContent: ` ${c.name}` }),
    ...(c.help ? [el("p", { className: "small", textContent: c.help })] : []),
    el("p", { className: "muted small", textContent: fill(w.ai_ref_used, { n: c.used }) + (c.examples.length ? ` (${c.examples.join(", ")})` : "") }),
    ...(rows.length ? [el("table", { className: "ai-ref-params", title: w.ai_ref_params }, ...rows)] : []),
    el("pre", { className: "ai-ref-snippet", textContent: c.snippet }), insert);
}

function scriptEvents() {
  $("ai-script-edit").addEventListener("click", editAIScript);
  $("ai-script-check").addEventListener("click", checkAIScript);
  $("ai-script-save").addEventListener("click", saveAIScript);
  $("ai-script-reset").addEventListener("click", resetAIScript);
  $("ai-script-close").addEventListener("click", closeScriptEditor);
  const area = $("ai-script-area");
  area.addEventListener("input", () => {
    scriptState();
    clearTimeout(outlineTimer);
    outlineTimer = setTimeout(refreshOutline, 1200);
  });
  area.addEventListener("keydown", (e) => {  // Tab indents as Python wants: 4 spaces
    if (e.key !== "Tab" || e.ctrlKey || e.altKey) return;
    e.preventDefault();
    const at = area.selectionStart;
    area.setRangeText("    ", at, area.selectionEnd, "end");
    scriptState();
  });
  $("ai-ref-find").addEventListener("input", () => { clearTimeout(refTimer); refTimer = setTimeout(findScriptParts, 300); });
  $("ai-ref-kind").addEventListener("change", findScriptParts);
}

// --- the All values tab (StudioApi.values_files / values_find / value_object / value_edit / value_reset / value_links,
// rusemod.values, our own code; LittleGroove's raw value editor had it first): any object of the unit data and every
// value it has, as the game's file has it, each changed in the current mod at once; values added and taken out,
// objects made and deleted (value_prop_add / value_prop_delete / value_object_new / value_object_delete, each delete
// asked first with what points at it, value_pointing). For whatever the other tabs don't show. Every
// control says in its tooltip what it is and what changing it does (the owner, 2026-10-07: "everything needs to work
// as if someone not very smart was playing, lots of tooltips") ---
const VALUE_KIND_TIPS = { number: "values_kind_number", bool: "values_kind_bool", text: "values_kind_text",
  key: "values_kind_key", vector: "values_kind_vector", guid: "values_kind_guid", numbers: "values_kind_numbers",
  link: "values_kind_link", part: "values_kind_part", list: "values_kind_written", map: "values_kind_written",
  pair: "values_kind_written", fixed: "values_kind_fixed" };
const VALUE_ITEMS_SHOWN = 30;  // the links and parts a list shows as buttons (the rest: "…")
const VALUE_BOXES = 12;  // a list of numbers up to this long gets a box for each number; a longer one, one text box
let valuesAsk = 0;      // the newest look-up: an older answer that comes back later is dropped
let valuesTimer = null;
let valueLinksAsk = 0;

function valuesEvents() {
  const later = () => { clearTimeout(valuesTimer); valuesTimer = setTimeout(findValues, 400); };
  const now = () => { clearTimeout(valuesTimer); findValues(); };
  for (const id of ["values-find", "values-prop", "values-value"]) {
    $(id).addEventListener("input", later);
    $(id).addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); now(); } });
  }
  $("values-file").addEventListener("change", now);
  $("values-go").addEventListener("click", now);
  $("values-new").addEventListener("click", () => {
    const form = $("values-new-form");
    if (!form.classList.contains("hidden")) { form.classList.add("hidden"); return; }
    valuesNewForm(form);
    form.classList.remove("hidden");
  });
}

// "New object…" needs a mod to keep the object in: without one it's locked, and its tooltip says why
function renderValuesNew() {
  const w = state.words, b = $("values-new");
  b.textContent = w.values_new;
  b.disabled = !state.mod;
  b.title = state.mod ? w.tip_values_new : w.no_mod;
  if (!state.mod) $("values-new-form").classList.add("hidden");
}

// A brand-new object (StudioApi.value_classes / value_object_new; LittleGroove's raw editor's Add): its kind, typed
// with a list of the unit data's kinds to pick from, and its name. Its page opens at once, to give it values.
async function valuesNewForm(form) {
  const w = state.words;
  const kinds = el("datalist", { id: "values-new-kinds" });
  const kind = el("input", { type: "text", className: "values-text", placeholder: w.values_new_kind_hint,
    title: w.tip_values_new_kind, autocomplete: "off" });
  kind.setAttribute("list", "values-new-kinds");
  const name = el("input", { type: "text", className: "values-text", placeholder: w.values_new_name_hint,
    title: w.tip_values_new_name, maxLength: 100, autocomplete: "off" });
  const make = el("button", { type: "button", className: "small primary", textContent: w.values_new_make,
    title: w.tip_values_new_make });
  make.addEventListener("click", async () => {
    if (!kind.value.trim()) { kind.focus(); return; }
    if (!name.value.trim()) { name.focus(); return; }
    make.disabled = true;
    let res;
    try { res = await api().value_object_new(kind.value.trim(), name.value.trim(), state.lang); } catch (err) {
      problem(err);
      make.disabled = false;
      return;
    }
    form.classList.add("hidden");
    if (state.valuePage && state.valuePage.address !== res.address) (state.valueBack = state.valueBack || []).push(state.valuePage.address);
    renderValuePage(res.page);
    say(fill(w.values_new_done, { name: name.value.trim() }), "ok");
    if (state.valuesFound) findValues();
  });
  name.addEventListener("keydown", (e) => { if (e.key === "Enter") { e.preventDefault(); make.click(); } });
  form.replaceChildren(el("p", { className: "muted small", textContent: w.values_new_help }),
    el("label", { className: "values-field" }, el("span", { className: "small", textContent: w.values_new_kind_label }), kind, kinds),
    el("label", { className: "values-field" }, el("span", { className: "small", textContent: w.values_new_name_label }), name),
    el("div", { className: "actions" }, make));
  kind.focus();
  if (!state.valueClasses) {
    try { state.valueClasses = (await api().value_classes()).classes; } catch (err) { problem(err); return; }
  }
  kinds.replaceChildren(...state.valueClasses.map((c) => el("option", { value: c.class,
    label: fill(w.values_new_kind_count, { n: c.count }) })));
}

// $/GFX/Everything/Descriptor_Unit_M4_Sherman:WeaponDescriptor -> Descriptor_Unit_M4_Sherman:WeaponDescriptor
function shortAddress(a) {
  const at = a.indexOf(":"), head = at < 0 ? a : a.slice(0, at);
  return head.split("/").pop() + (at < 0 ? "" : a.slice(at));
}

async function renderValues() {
  const w = state.words;
  $("values-intro").textContent = w.values_help;
  $("values-file-label").textContent = w.values_file_label;
  $("values-find-label").textContent = w.values_find_label;
  $("values-find").placeholder = w.values_find_hint;
  $("values-by-title").textContent = w.values_by_title;
  $("values-by-help").textContent = w.values_by_help;
  $("values-prop-label").textContent = w.values_prop_label;
  $("values-prop").placeholder = w.values_prop_hint;
  $("values-value-label").textContent = w.values_value_label;
  $("values-value").placeholder = w.values_value_hint;
  $("values-go").textContent = w.values_go;
  const tips = { "values-file": "tip_values_file", "values-find": "tip_values_find", "values-by-title": "tip_values_by",
    "values-prop": "tip_values_prop", "values-value": "tip_values_value", "values-go": "tip_values_go" };
  for (const [id, key] of Object.entries(tips)) $(id).title = w[key] || "";
  renderValuesNew();
  if (!knownNumbers) {  // what each value does (the number guide), for the lines under the values' names
    try { knownNumbers = await api().numbers(state.lang); } catch { knownNumbers = null; }
  }
  if (!state.valueFiles) {
    try { state.valueFiles = (await api().values_files()).files; } catch (err) { problem(err); return; }
  }
  const picked = $("values-file").value;
  $("values-file").replaceChildren(el("option", { value: "", textContent: w.values_file_all }),
    ...state.valueFiles.map((f) => el("option", { value: f.path, title: f.path,
      textContent: `${f.path.split("/").slice(-2).join("/")} (${f.objects})` })));
  $("values-file").value = picked;
  if (state.valuesFound) listValues(state.valuesFound);
  else $("values-count").textContent = w.values_start;
  if (state.valuePage) showValueObject(state.valuePage.address, { keep: true });
  else $("values-detail").replaceChildren(el("p", { id: "values-pick", className: "muted", textContent: w.values_pick }));
}

async function findValues() {
  const w = state.words, ask = ++valuesAsk;
  const file = $("values-file").value, words = $("values-find").value.trim();
  const prop = $("values-prop").value.trim(), value = $("values-value").value.trim();
  if (!file && !words && !prop && !value) {  // nothing asked yet: no list of 100,000 objects
    state.valuesFound = null;
    $("values-list").replaceChildren();
    $("values-count").textContent = w.values_start;
    return;
  }
  $("values-count").textContent = w.values_looking;
  let res;
  try { res = await api().values_find(file, words, prop, value, state.lang); } catch (err) {
    if (ask === valuesAsk) { $("values-count").textContent = ""; problem(err); }
    return;
  }
  if (ask !== valuesAsk) return;
  state.valuesFound = res;
  listValues(res);
}

function listValues(res) {
  const w = state.words;
  $("values-count").textContent = !res.total ? w.values_none
    : fill(res.total > res.objects.length ? w.values_some : w.values_count, { shown: res.objects.length, n: res.total });
  $("values-list").replaceChildren(...res.objects.map((o) => {
    const sub = [o.mine ? w.values_mine_mark : null, o.deleted ? w.values_deleted_mark : null,
      o.name ? shortAddress(o.address) : null, o.class, o.match].filter(Boolean).join(" · ");
    const b = el("button", { type: "button", title: `${fill(w.tip_values_object, { kind: o.class, file: o.file })}\n${o.address}` },
      el("span", { className: "name", textContent: o.name || shortAddress(o.address) }),
      el("span", { className: "sub", textContent: sub }));
    b.dataset.address = o.address;
    b.setAttribute("aria-current", String(!!state.valuePage && state.valuePage.address === o.address));
    b.addEventListener("click", () => openValue(o.address, true));
    return el("li", {}, b);
  }));
}

// Open an object's page; `push`: the page shown now goes on the Back list
function openValue(address, push) {
  if (push && state.valuePage && state.valuePage.address !== address) {
    (state.valueBack = state.valueBack || []).push(state.valuePage.address);
  }
  return showValueObject(address);
}

// From a unit's page on the Units tab: the same object, with every value it has
function openAllValues(address) {
  if (state.valuePage && state.valuePage.address !== address) (state.valueBack = state.valueBack || []).push(state.valuePage.address);
  state.valuePage = { address };
  showView("values");
}

async function showValueObject(address, opts) {
  let p;
  try { p = await api().value_object(address, state.lang); } catch (err) { problem(err); return; }
  state.valuePage = { address: p.address };
  if (state.view !== "values") return;  // another tab was picked meanwhile
  renderValuePage(p);
  if (!(opts && opts.keep)) $("values-detail").scrollTop = 0;
}

function valuesWhy(p) {
  const w = state.words;
  return { outside: w.values_why_outside, not_stable: w.values_why_not_stable, no_mod: w.no_mod,
    deleted: w.values_why_deleted }[p.why_not] || p.why_not;
}

function renderValuePage(p) {
  const w = state.words;
  state.valuePage = { address: p.address };
  for (const b of $("values-list").querySelectorAll("button")) b.setAttribute("aria-current", String(b.dataset.address === p.address));
  const nav = el("div", { className: "values-nav" });
  if ((state.valueBack || []).length) {
    const back = el("button", { type: "button", className: "ghost", textContent: w.values_back, title: w.tip_values_back });
    back.addEventListener("click", () => showValueObject(state.valueBack.pop()));
    nav.append(back);
  }
  if (p.owner) {
    const up = el("button", { type: "button", className: "ghost",
      textContent: fill(w.values_part_of, { name: p.owner.name || shortAddress(p.owner.address) }), title: w.tip_values_part_of });
    up.addEventListener("click", () => openValue(p.owner.address, true));
    nav.append(up);
  }
  const copy = el("button", { type: "button", textContent: w.copy_address, title: w.tip_values_copy });
  copy.addEventListener("click", async () => { if (await copyText(p.address)) say(w.values_copied, "ok"); });
  const parts = [el("h1", { textContent: p.name || shortAddress(p.address) })];
  if (nav.childNodes.length) parts.unshift(nav);
  if (p.name) parts.push(el("div", { className: "game-name", textContent: shortAddress(p.address), title: w.tip_values_code_name }));
  parts.push(el("div", { className: "address" }, el("code", { textContent: p.address }), copy),
    el("div", { className: "meta", title: w.tip_values_meta, textContent: p.mine ? fill(w.values_meta_mine, { kind: p.class })
      : fill(w.values_meta, { kind: p.class, file: p.file, n: p.index }) }));
  if (p.mine) parts.push(el("p", { className: "notice new", textContent: w.values_mine }));
  if (p.deleted && p.named && state.mod) {  // deleted by the mod: put it back to change it again
    const back = el("button", { type: "button", className: "small", textContent: w.values_put_back, title: w.tip_values_put_back });
    back.addEventListener("click", async () => {
      back.disabled = true;
      let res;
      try { res = await api().value_object_restore(p.address, state.lang); } catch (err) { problem(err); back.disabled = false; return; }
      renderValuePage(res.page);
      say(fill(w.values_put_back_done, { name: p.name || shortAddress(p.address) }), "ok");
      if (state.valuesFound) findValues();
    });
    parts.push(el("div", { className: "notice warn" }, el("p", { textContent: valuesWhy(p) }), el("div", { className: "actions" }, back)));
  } else if (!p.editable) parts.push(el("p", { className: "notice", textContent: valuesWhy(p) }));
  else {
    parts.push(el("p", { className: "notice", textContent: w.values_how }));
    if (p.shared) parts.push(el("p", { className: "notice warn", textContent: fill(w.values_shared, { n: p.owners }) }));
    else if (p.named && p.users > 1) parts.push(el("p", { className: "notice warn", textContent: fill(w.values_users_warn, { n: p.users }) }));
    if (state.mod) parts.push(valueTools(p));
  }
  const table = el("table", { className: "values-table" });
  for (const r of p.rows) table.append(valueRow(p, r));
  const group = el("div", { className: "group" }, el("h2", { textContent: fill(w.values_rows, { n: p.rows.length }) }), table);
  if (p.rows.some((r) => r.locked)) group.append(el("p", { className: "muted small", textContent: w.locked }));
  parts.push(group);
  if (p.used_by.length) {
    const list = el("ul", { className: "parts" });
    for (const u of p.used_by) {
      const b = el("button", { type: "button", title: `${w.tip_values_user}\n${u.address}` },
        `${u.name || shortAddress(u.address)}  ·  ${u.path}`);
      b.addEventListener("click", () => openValue(u.address, true));
      list.append(el("li", {}, b));
    }
    const more = p.users > p.used_by.length ? [el("p", { className: "muted small", textContent: fill(w.values_users_more, { n: p.users - p.used_by.length }) })] : [];
    parts.push(el("div", { className: "group" }, el("h2", { textContent: fill(w.values_used_by, { n: p.users }) }), list, ...more));
  }
  parts.push(notesBox(`obj:${p.address}`));
  $("values-detail").replaceChildren(...parts);
}

// What the game's value is, in words, for the line under a changed value
function valueGameText(r) {
  const w = state.words;
  if (r.kind === "bool") return r.value ? w.values_yes : w.values_no;
  if (r.kind === "link") return r.to ? shortAddress(r.to) : w.values_link_none;
  if (Array.isArray(r.value)) return r.value.join(", ");
  if (r.value !== null && r.value !== undefined) return String(r.value);
  return r.text || "";
}

function valueRow(p, r) {
  const w = state.words;
  const kindTip = w[VALUE_KIND_TIPS[r.kind] || "values_kind_fixed"] || "";
  // what it does, from the number guide (rusemod/numberinfo.toml), as the Units, Economy and AI tabs say it; a value
  // with no name of its own in labels.toml is called by the guide's ("Weapons", not WeaponDescriptor)
  const entry = numberEntry(p.class, r.prop);
  const label = r.label === r.prop && entry && state.lang !== "base" ? entry.what : r.label;
  const th = el("th", { textContent: label, title: `${kindTip}\n(${r.prop} · ${r.type})` });
  if (state.lang !== "base" && label !== r.prop) th.append(el("small", { textContent: r.prop }));
  if (entry) {
    th.title = `${numberTip(entry)}\n\n${kindTip}\n(${r.prop} · ${r.type})`;
    th.append(el("small", { className: "about", textContent: entry.does }));
  }
  const scale = entry && knownNumbers && knownNumbers.plain[entry.unit];
  const plainOf = (v) => scale && scale[0] !== 1 ? numberPlain(entry, Number(v)) : "";  // ("25%" for 0.25, "about 400 m")
  const now = r.edited && !r.edited.removed ? r.edited : null;  // the mod's value: what the box shows
  const shown = now ? now.value : r.value;
  const text = now ? now.text : r.text;
  const can = r.can && !!state.mod;
  // a box that can't be changed says why: an id, the object (outside the unit data, no mod picked...), or the value
  const tip = can ? kindTip : r.locked ? w.locked : !p.editable ? valuesWhy(p) : !state.mod ? w.no_mod : w.values_cant_row;
  const save = (value) => saveValue(p, r, value);
  const td = el("td");
  const box = (props) => el("input", Object.assign({ disabled: !can, title: tip }, props));
  if (r.kind === "number") {
    const b = box({ type: "number", value: String(shown), step: WHOLE.has(r.type) ? "1" : "any" });
    b.setAttribute("aria-label", r.label);
    b.addEventListener("change", () => { if (b.value.trim() === "") { b.value = String(shown); return; } save(Number(b.value)); });
    const plain = el("span", { className: "muted small number-plain", textContent: plainOf(shown) });
    b.addEventListener("input", () => { plain.textContent = b.value.trim() === "" ? "" : plainOf(b.value); });
    td.append(el("div", { className: "boxes" }, b, plain));
  } else if (r.kind === "bool") {
    const b = box({ type: "checkbox", checked: Boolean(shown) });
    b.setAttribute("aria-label", r.label);
    b.addEventListener("change", () => save(b.checked));
    td.append(el("label", { className: "values-yes", title: tip }, b, " ", w.values_yes));
  } else if (r.kind === "text" || r.kind === "guid") {
    const b = box({ type: "text", value: shown ?? "", className: "values-text" });
    b.setAttribute("aria-label", r.label);
    b.addEventListener("change", () => save(b.value));
    td.append(b);
  } else if (r.kind === "key") {
    const b = box({ type: "text", value: shown ?? "", className: "values-key" });
    b.setAttribute("aria-label", r.label);
    b.addEventListener("change", () => save(b.value.trim()));
    const words = now ? now.words : r.words_mine || r.words;  // the words the key shows: the mod's when it changes them
    const said = el("div", { className: "values-words", title: w.tip_values_words,
      textContent: words ? `“${words}”` : w.values_words_none });
    if (!now && r.words_mine) said.append(" ", el("span", { className: "values-mine", textContent: w.values_words_mine }));
    td.append(b, said);
    if (!now) {  // the words of the key the game has (a key the mod puts there instead: on its own row once saved)
      const edit = el("button", { type: "button", className: "link", textContent: w.values_words_edit,
        title: w.tip_values_words_edit });
      let panel = null;
      edit.addEventListener("click", () => {
        if (panel) { panel.remove(); panel = null; return; }
        panel = wordsPanel(r.value, () => showValueObject(p.address, { keep: true }));
        td.append(panel);
      });
      td.append(edit);
    }
    if (r.can && !r.added) {  // a new text of the mod's own, this value pointed at it (StudioApi.value_text_new; his Mint new)
      const fresh = el("button", { type: "button", className: "link", textContent: w.values_text_new,
        title: w.tip_values_text_new });
      let form = null;
      fresh.addEventListener("click", () => {
        if (form) { form.remove(); form = null; return; }
        const input = el("input", { type: "text", className: "values-text", maxLength: 200,
          placeholder: w.values_text_new_hint, title: w.tip_values_text_new });
        input.setAttribute("aria-label", w.values_text_new);
        const make = el("button", { type: "button", className: "small primary", textContent: w.values_text_new_make,
          title: w.tip_values_text_new });
        make.addEventListener("click", async () => {
          if (!input.value.trim()) { input.focus(); return; }
          make.disabled = true;
          try {
            const res = await api().value_text_new(p.address, r.prop, input.value, state.lang);
            say(w.values_text_new_done, "ok");
            renderValuePage(res.page);
          } catch (err) { problem(err); make.disabled = false; }
        });
        form = el("div", { className: "values-words-box" }, el("p", { className: "muted small", textContent: w.values_text_new_help }),
          input, " ", make);
        td.append(form);
        input.focus();
      });
      td.append(" ", fresh);
    }
  } else if (r.kind === "vector") {
    const items = Array.isArray(shown) ? shown : [];
    const color = r.type === "RGBA";
    const boxes = items.map((x, i) => {
      const b = box({ type: "number", value: String(x), step: color || r.type === "Int2" ? "1" : "any",
        title: `${tip}\n${(color ? ["R", "G", "B", "A"] : ["x", "y", "z", "w"])[i]}` });
      if (color) { b.min = "0"; b.max = "255"; }
      b.setAttribute("aria-label", `${r.label} [${i}]`);
      return b;
    });
    for (const b of boxes) b.addEventListener("change", () => save(boxes.map((x) => x.value.trim() || "0").join(", ")));
    const holder = el("div", { className: "boxes" }, ...boxes);
    if (color && items.length === 4) holder.append(el("span", { className: "values-swatch", title: w.tip_values_swatch,
      style: `background: rgba(${items[0]}, ${items[1]}, ${items[2]}, ${items[3] / 255})` }));
    td.append(holder);
  } else if (r.kind === "numbers") {
    const items = Array.isArray(shown) ? shown : [];
    const key = `${p.address}|${r.prop}`;
    if (!Array.isArray(shown) || items.length > VALUE_BOXES || (state.valuesAsText && state.valuesAsText.has(key))) {
      // the whole list as text, numbers with commas between: to make it longer or shorter
      const b = box({ type: "text", value: Array.isArray(shown) ? shown.join(", ") : (text || ""), className: "values-text" });
      b.setAttribute("aria-label", r.label);
      b.addEventListener("change", () => save(b.value));
      td.append(b, el("div", { className: "muted small", textContent: fill(w.values_items, { n: items.length }) }));
    } else {  // a short list: a box for each number (a tick box for each yes/no), as the Units tab shows a price
      const bool = r.type === "bool";
      const boxes = items.map((x, i) => {
        const b = box(bool ? { type: "checkbox", checked: Boolean(x) }
          : { type: "number", value: String(x), step: WHOLE.has(r.type) ? "1" : "any" });
        b.title = `${tip}\n${fill(w.values_item_n, { n: i + 1 })}`;
        b.setAttribute("aria-label", `${r.label} [${i}]`);
        return b;
      });
      const read = () => boxes.map((b) => bool ? (b.checked ? 1 : 0) : b.value.trim() === "" ? NaN : Number(b.value));
      for (const b of boxes) {
        b.addEventListener("change", () => {
          const now = read();
          if (now.some((n) => !Number.isFinite(n))) { showValueObject(p.address, { keep: true }); return; }  // emptied: put it back
          save(now);
        });
      }
      const asText = el("button", { type: "button", className: "link", textContent: w.values_as_text,
        title: w.tip_values_as_text, disabled: !can });
      asText.addEventListener("click", () => {
        (state.valuesAsText = state.valuesAsText || new Set()).add(key);
        showValueObject(p.address, { keep: true });
      });
      // a price or shown-in-menu list: one value per game mode, each box with its mode's name (as on the Units tab)
      const modes = MODE_LISTS.has(r.prop) && items.length === 5 ? modeNames() : null;
      if (modes) boxes.forEach((b, i) => { b.title = `${tip}\n${modes[i]}`; b.setAttribute("aria-label", `${r.label} [${modes[i]}]`); });
      const cells = modes ? boxes.map((b, i) => el("label", { className: "mode-box" }, el("small", { textContent: modes[i] }), b))
        : boxes;
      td.append(el("div", { className: "boxes" }, ...cells), asText);
    }
  } else if (r.kind === "link") {
    td.append(valueLink(p, r, shown, can, tip, save));
  } else if (r.kind === "part") {
    const b = el("button", { type: "button", className: "chip", disabled: !r.to, title: w.tip_values_part,
      textContent: `${w.values_open_part} · ${r.type}` });
    b.addEventListener("click", () => openValue(r.to, true));
    td.append(b);
  } else if (r.kind === "list" || r.kind === "map" || r.kind === "pair") {
    td.append(el("div", { className: "muted small", textContent: fill(w.values_items, { n: r.count }) }));
    const items = (r.items || []).filter((x) => x.to);
    if (items.length) {
      const list = el("div", { className: "values-items" });
      for (const x of items.slice(0, VALUE_ITEMS_SHOWN)) {
        const b = el("button", { type: "button", className: "chip", title: x.part ? w.tip_values_part : w.tip_values_open,
          textContent: `${x.path.slice(r.prop.length)}  ${x.part ? x.class : shortAddress(x.to)}` });
        b.addEventListener("click", () => openValue(x.to, true));
        list.append(b);
      }
      if (items.length > VALUE_ITEMS_SHOWN) list.append(el("span", { className: "muted small", textContent: "…" }));
      td.append(list);
    }
    if (text !== null && text !== undefined) {
      const area = el("textarea", { className: "values-written", value: text, disabled: !can, title: tip, spellcheck: false,
        rows: Math.min(8, Math.max(2, Math.ceil(text.length / 90))) });
      area.setAttribute("aria-label", r.label);
      area.addEventListener("change", () => save(area.value));
      td.append(area);
    }
  } else {
    td.append(el("span", { className: "muted", title: w.values_kind_fixed, textContent: r.value || w.values_kind_fixed }));
  }
  if (r.edited) {
    td.classList.add("edited");
    // a value the mod adds (or gives an object it makes) is taken back out; any other gets the game's value back
    const reset = el("button", { type: "button", className: "link", textContent: r.added ? w.values_take_out : w.values_reset,
      title: r.added ? w.tip_values_take_out_added : w.tip_values_reset, disabled: !state.mod });
    reset.addEventListener("click", () => resetValue(p, r));
    const was = r.edited.removed ? w.values_removed : r.added ? (p.mine ? w.values_given : w.values_added)
      : fill(w.values_game, { value: valueGameText(r) });
    td.append(el("div", { className: "was" }, was, " ", reset));
  }
  if (r.deletable && state.mod) {  // one of the game's values taken out of the object (his Del prop), asked first
    const out = el("button", { type: "button", className: "link", textContent: w.values_take_out, title: w.tip_values_take_out });
    let ask = null;
    out.addEventListener("click", () => {
      if (ask) { ask.remove(); ask = null; return; }
      ask = valueTakeOutAsk(p, r, () => { if (ask) ask.remove(); ask = null; });
      td.append(ask);
    });
    td.append(el("div", { className: "values-row-tools" }, out));
  }
  return el("tr", {}, th, td);
}

// Add a value… and Delete this object… on an object's page (LittleGroove's Add prop and Delete): each opens its box
// under the buttons, one at a time
function valueTools(p) {
  const w = state.words;
  const holder = el("div", { className: "values-tools" });
  let open = null;
  const show = (box) => { if (open) open.remove(); open = box; if (box) holder.append(box); };
  const add = el("button", { type: "button", textContent: w.values_add, title: w.tip_values_add });
  add.addEventListener("click", () => show(open && open.dataset.kind === "add" ? null : valueAddForm(p)));
  const buttons = el("div", { className: "values-nav" }, add);
  if (p.named || p.mine) {  // a part goes with a value of the object it's part of (Take out on that row)
    const del = el("button", { type: "button", className: "ghost danger", textContent: w.values_delete, title: w.tip_values_delete });
    del.addEventListener("click", () => show(open && open.dataset.kind === "delete" ? null : valueDeleteAsk(p, () => show(null))));
    buttons.append(del);
  }
  holder.append(buttons);
  return holder;
}

// A value this object hasn't got, picked from the ones other objects of its kind have (StudioApi.value_prop_choices),
// its box starting as another's value; Add saves it in the mod (value_prop_add) and it gets its own row
function valueAddForm(p) {
  const w = state.words;
  const box = el("div", { className: "values-words-box" }, el("p", { className: "muted small", textContent: w.values_add_help }));
  box.dataset.kind = "add";
  api().value_prop_choices(p.address, state.lang).then((res) => {
    const can = res.props.filter((x) => x.can);
    const cant = res.props.length - can.length;
    if (!can.length) {
      box.append(el("p", { className: "muted small", textContent: w.values_add_none }));
      if (cant) box.append(el("p", { className: "muted small", textContent: fill(w.values_add_some_cant, { n: cant }) }));
      return;
    }
    const pick = el("select", { title: w.tip_values_add_pick });
    pick.append(...can.map((x) => el("option", { value: x.prop, title: w[VALUE_KIND_TIPS[x.kind]] || "",
      textContent: x.label !== x.prop ? `${x.label} (${x.prop})` : x.prop })));
    const holder = el("span", { className: "values-add-value" });
    let input = null;
    const fillValue = () => {  // a tick box for a yes/no, a number box for a number, else a text box
      const x = can.find((c) => c.prop === pick.value);
      input = x.kind === "bool" ? el("input", { type: "checkbox", checked: x.start === "1", title: w.tip_values_add_value })
        : el("input", { type: x.kind === "number" ? "number" : "text", value: x.start, step: "any",
          className: "values-text", title: w.tip_values_add_value });
      holder.replaceChildren(input);
    };
    pick.addEventListener("change", fillValue);
    fillValue();
    const go = el("button", { type: "button", className: "small primary", textContent: w.values_add_go, title: w.tip_values_add_go });
    go.addEventListener("click", async () => {
      const x = can.find((c) => c.prop === pick.value);
      go.disabled = true;
      let done;
      try { done = await api().value_prop_add(p.address, x.prop, x.kind === "bool" ? input.checked : input.value, state.lang); }
      catch (err) { problem(err); go.disabled = false; return; }
      renderValuePage(done.page);
      say(fill(w.values_added_done, { name: x.label }), "ok");
    });
    box.append(el("div", { className: "values-words-grid" },
      el("span", { className: "small", textContent: w.values_add_pick_label, title: w.tip_values_add_pick }), pick,
      el("span", { className: "small", textContent: w.values_add_value_label, title: w.tip_values_add_value }), holder),
    el("div", { className: "actions" }, go));
    if (cant) box.append(el("p", { className: "muted small", textContent: fill(w.values_add_some_cant, { n: cant }) }));
  }).catch(problem);
  return box;
}

// What points at what's about to go (StudioApi.value_pointing): each one a button that opens it, the mod's own
// changes marked, and the mod's changes inside it that go with it
function pointingParts(res) {
  const w = state.words, out = [];
  if (res.total) {
    const list = el("ul", { className: "parts" });
    for (const u of res.users) {
      const b = el("button", { type: "button", title: `${w.tip_values_user}\n${u.address}` },
        `${u.name || shortAddress(u.address)}  ·  ${u.path}${u.mine ? `  ·  ${w.values_your_change}` : ""}`);
      b.addEventListener("click", () => openValue(u.address, true));
      list.append(el("li", {}, b));
    }
    out.push(el("p", { className: "notice warn", textContent: fill(w.values_points_at, { n: res.total }) }), list);
    if (res.total > res.users.length) out.push(el("p", { className: "muted small", textContent: fill(w.values_users_more, { n: res.total - res.users.length }) }));
    out.push(el("p", { className: "small", textContent: w.values_points_after }));
  }
  if (res.inside) out.push(el("p", { className: "small", textContent: fill(w.values_inside_go, { n: res.inside }) }));
  return out;
}

// "Take out" on a row: asked first, saying what points at it (a part or a list of them), then taken out in the mod
// (StudioApi.value_prop_delete: `delete Prop`)
function valueTakeOutAsk(p, r, close) {
  const w = state.words;
  const box = el("div", { className: "values-words-box" }, el("p", { className: "muted small", textContent: w.values_looking }));
  api().value_pointing(p.address, r.prop, state.lang).then((res) => {
    const yes = el("button", { type: "button", className: "small ghost danger", textContent: w.values_take_out_yes,
      title: w.tip_values_take_out });
    const no = el("button", { type: "button", className: "small ghost", textContent: w.cancel, title: w.tip_cancel });
    no.addEventListener("click", close);
    yes.addEventListener("click", async () => {
      yes.disabled = true;
      let done;
      try { done = await api().value_prop_delete(p.address, r.prop, state.lang); } catch (err) { problem(err); yes.disabled = false; return; }
      renderValuePage(done.page);
      say(fill(w.values_took_out, { name: r.label }), "ok");
    });
    box.replaceChildren(el("p", { textContent: fill(w.values_take_out_sure, { name: r.label }) }), ...pointingParts(res),
      el("div", { className: "actions" }, yes, no));
    yes.focus();
  }).catch((err) => { problem(err); close(); });
  return box;
}

// "Delete this object…": asked first, saying what points at it (StudioApi.value_pointing); a unit the game's unit list
// names can't be deleted, and the box says so. Then deleted in the mod (value_object_delete: `delete $/...`), or, for
// one the mod made, taken out of the mod
function valueDeleteAsk(p, close) {
  const w = state.words, name = p.name || shortAddress(p.address);
  const box = el("div", { className: "values-words-box" }, el("p", { className: "muted small", textContent: w.values_looking }));
  box.dataset.kind = "delete";
  api().value_pointing(p.address, "", state.lang).then((res) => {
    const no = el("button", { type: "button", className: "small ghost", textContent: w.cancel, title: w.tip_cancel });
    no.addEventListener("click", close);
    if (res.blocked) {
      box.replaceChildren(el("p", { className: "notice warn", textContent: fill(w.values_delete_listed, { name }) }),
        el("div", { className: "actions" }, no));
      return;
    }
    const yes = el("button", { type: "button", className: "small ghost danger", textContent: w.values_delete_yes,
      title: w.tip_values_delete_yes });
    yes.addEventListener("click", async () => {
      yes.disabled = true;
      let done;
      try { done = await api().value_object_delete(p.address, state.lang); } catch (err) { problem(err); yes.disabled = false; return; }
      say(fill(w.values_deleted_done, { name }), "ok");
      if (done.page) renderValuePage(done.page);
      else {  // one the mod made: gone
        state.valuePage = null;
        $("values-detail").replaceChildren(el("p", { id: "values-pick", className: "muted", textContent: w.values_pick }));
      }
      if (state.valuesFound) findValues();
    });
    box.replaceChildren(el("p", { textContent: fill(p.mine ? w.values_delete_sure_mine : w.values_delete_sure, { name }) }),
      ...pointingParts(res), el("div", { className: "actions" }, yes, no));
    no.focus();
  }).catch((err) => { problem(err); close(); });
  return box;
}

// The words a game text key shows, one box per language, each named in its own words (StudioApi.value_words /
// value_words_set, LittleGroove's "Save text": rename a unit in every language). Languages left as they are keep the
// game's words. `saved()`: what to show again once saved (the All values page; the Maps tab's town name). `kind`
// "map": kept in the map project, as the Maps tab's changes are (a town's name), else in the unit mod. `helpNew`: what
// the box says over a text of the mod's own (a new label's, by default).
function wordsPanel(key, saved, kind = "mod", helpNew = null) {
  const w = state.words, has = kind === "map" ? Boolean(state.map || state.mod) : Boolean(state.mod);
  const box = el("div", { className: "values-words-box" },
    el("p", { className: "muted small", textContent: w.values_words_help }));
  api().value_words(key, kind).then((res) => {
    if (!res.table) { box.append(el("p", { className: "muted small", textContent: w.values_words_no_text })); return; }
    if (res.new) box.firstChild.textContent = helpNew || w.values_words_help_new;  // the mod's own text: no game words
    const inputs = {}, grid = el("div", { className: "values-words-grid" });
    for (const x of res.words) {
      const name = (state.languages.find((l) => l.code === x.lang) || {}).name || x.lang;
      const input = el("input", { type: "text", value: x.mine ?? x.game ?? "", className: "values-text",
        title: fill(w.tip_values_words_lang, { lang: name }), disabled: !has });
      input.setAttribute("aria-label", name);
      if (x.mine !== null && x.mine !== undefined && x.mine !== x.game) input.classList.add("changed");
      inputs[x.lang] = input;
      grid.append(el("span", { className: "small", textContent: name, title: fill(w.tip_values_words_lang, { lang: name }) }), input);
    }
    const send = async (texts, word) => {
      try { await api().value_words_set(key, texts, kind); } catch (err) { problem(err); return; }
      say(fill(word, { key }), "ok");
      if (saved) saved();
    };
    const save = el("button", { type: "button", className: "small primary", textContent: w.values_words_save,
      title: w.tip_values_words_save, disabled: !has });
    save.addEventListener("click", () => send(Object.fromEntries(Object.entries(inputs).map(([k, i]) => [k, i.value])),
      w.values_words_saved));
    const back = el("button", { type: "button", className: "small ghost", textContent: w.values_words_reset,
      title: w.tip_values_words_reset, disabled: !has || !res.words.some((x) => x.mine !== null && x.mine !== undefined) });
    back.addEventListener("click", () => send(Object.fromEntries(res.words.map((x) => [x.lang, x.game || ""])),
      w.values_words_back));
    box.append(grid, el("div", { className: "actions" }, save, ...(res.new ? [] : [back])));
    if (!has) box.append(el("p", { className: "muted small", textContent: w.no_mod }));
  }).catch(problem);
  return box;
}

// A link: the address it points at, a list to pick another from (StudioApi.value_links, filled as you type), and Open
function valueLink(p, r, shown, can, tip, save) {
  const w = state.words;
  const id = `values-links-${++valueLinksAsk}`;
  const options = el("datalist", { id });
  const b = el("input", { type: "text", value: shown || "", className: "values-text", disabled: !can, title: tip,
    placeholder: w.values_link_none });
  b.setAttribute("list", id);
  b.setAttribute("aria-label", r.label);
  let timer = null, asked = 0;
  const suggest = () => {
    clearTimeout(timer);
    timer = setTimeout(async () => {
      const ask = ++asked;
      let res;
      try { res = await api().value_links(p.address, r.prop, b.value.trim().split("/").pop(), state.lang); } catch { return; }
      if (ask !== asked) return;
      options.replaceChildren(...res.objects.map((o) => el("option", { value: o.address,
        label: [o.name, o.class].filter(Boolean).join(" · ") })));
    }, 250);
  };
  b.addEventListener("focus", suggest);
  b.addEventListener("input", suggest);
  b.addEventListener("change", () => save(b.value.trim()));
  const target = shown || r.to;
  const open = el("button", { type: "button", className: "ghost", textContent: w.values_open, title: w.tip_values_open,
    disabled: !target });
  open.addEventListener("click", () => openValue(target, true));
  return el("div", { className: "values-link" }, b, options, open);
}

async function saveValue(p, r, value) {
  const w = state.words;
  let res;
  try { res = await api().value_edit(p.address, r.prop, value, state.lang); } catch (err) {
    problem(err);
    showValueObject(p.address, { keep: true });  // the box shows what's saved again
    return;
  }
  renderValuePage(res.page);
  const after = res.page.rows.find((x) => x.prop === r.prop);
  say(fill(after && after.edited ? w.values_saved : w.values_same, { name: r.label }), "ok");
}

async function resetValue(p, r) {
  let res;
  try { res = await api().value_reset(p.address, r.prop, state.lang); } catch (err) { problem(err); return; }
  renderValuePage(res.page);
  say(fill(r.added ? state.words.values_took_out : state.words.values_same, { name: r.label }), "ok");
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
  { id: "research", async render() {  // what taking out a unit others are researched from does; seconds or minutes
    const w = state.words;
    try { state.prefs = (await api().prefs()) || {}; } catch { /* the ones read at the start */ }
    const gone = $("research-gone"), unit = $("research-unit"), note = $("research-gone-note");
    $("research-gone-label").textContent = w.research_gone_label;
    $("research-unit-label").textContent = w.research_time_unit;
    gone.title = w.tip_research_gone;
    unit.title = w.tip_research_time_unit;
    gone.replaceChildren(...RESEARCH_GONE.map((k) => el("option", { value: k, textContent: w[`research_gone_${k}`] })));
    unit.replaceChildren(el("option", { value: "s", textContent: w.research_seconds }),
      el("option", { value: "min", textContent: w.research_minutes }));
    gone.value = RESEARCH_GONE.includes(state.prefs.research_gone) ? state.prefs.research_gone : "warn";
    unit.value = timeUnit();
    note.textContent = w[`tip_research_gone_${gone.value}`];
    gone.onchange = () => { note.textContent = w[`tip_research_gone_${gone.value}`]; keepPref("research_gone", gone.value); };
    unit.onchange = () => keepPref("research_time_unit", unit.value);
  } },
  { id: "start", render() { if (window.StartFlow) return window.StartFlow.renderSetting(); } },  // (startflow.js)
  { id: "game", async render() {
    const w = state.words, g = await api().game_folder();
    $("set-game-path").textContent = g.message || (g.path ? fill(w.set_game_path, { path: g.path }) : w.set_game_none);
    $("set-game-change").textContent = w.set_game_change;
  } },
  { id: "copies", async render() { renderCopies(await api().copies_folder()); } },
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
  renderSettings();  // another game folder: its own recommended place for modded copies (SETTINGS "copies")
  loadBackup();  // and its own backups
  if (g.message) $("set-game-path").textContent = g.message;
  return g;
}

// --- where modded copies go (rusemod.play.instances_dir through api.copies_folder): the folder chosen here, else
// $RUSE_INSTANCES, else the recommended place, RUSE-Instances on the game's drive (the owner, 2026-10-09: "user should
// be able to choose where files go"). A change only says where the next Test in game builds: the old folder stays
// until the modder deletes it by hand, and the game's clean backup goes beside the new folder ---
function renderCopies(v, note, noteKind) {
  const w = state.words, how = v.how || "";
  // the folder and why it's that one: chosen here, $RUSE_INSTANCES, the recommended place, or given at the start
  $("set-copies-path").textContent = !v.path ? w.set_copies_none
    : how === "fixed" ? fill(w.set_copies_fixed, { path: v.path })
      : fill(w["doc_copies_" + how] || w.doc_copies_recommended, { path: v.path });
  $("set-copies-drive").textContent = v.other_drive  // on another drive: a full copy of the game, slower and bigger
    ? fill(w.doc_copies_other_drive, { path: v.path, drive: v.drive || "", recommended: v.recommended || "" }) : "";
  $("set-copies-drive").classList.toggle("hidden", !v.other_drive);
  const fixed = how === "fixed", change = $("set-copies-change"), back = $("set-copies-default");
  change.textContent = w.set_copies_change;
  back.textContent = w.set_copies_default;
  change.disabled = fixed;
  change.title = fixed ? w.tip_copies_fixed : w.tip_copies_change;  // a locked button says why
  back.disabled = fixed || how === "recommended";
  back.title = fixed ? w.tip_copies_fixed : how === "recommended" ? w.tip_copies_default_off : w.tip_copies_default;
  const line = $("set-copies-note");
  line.textContent = note || "";
  line.className = "small" + (note && noteKind ? " " + noteKind : "");
}

async function changeCopies(choose) {
  const w = state.words, was = (await api().copies_folder()).path;
  const v = await (choose ? api().choose_copies_folder() : api().use_recommended_copies());
  if (v.message) renderCopies(v, v.message, "bad");
  else renderCopies(v, v.path && v.path !== was ? fill(w.set_copies_changed, { path: v.path }) : "", "good");
  loadBackup();  // the clean backup goes beside the copies
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
  try { state.update = await api().update_check(state.lang); } catch { state.update = null; }
  renderUpdate();
}

// The language changed: what's new again, in it (the release's notes in every language, English for one they lack)
function recheckUpdate() {
  if (!state.update || !state.update.available) return;
  api().update_check(state.lang).then((u) => { state.update = u; renderUpdate(); }).catch(() => {});
}

// A release note's line with its **bold** and `code` shown as such (nothing of the notes is taken as HTML)
function richText(s) {
  const out = document.createDocumentFragment();
  for (const part of String(s || "").split(/(\*\*[^*]+\*\*|`[^`]+`)/)) {
    if (!part) continue;
    if (part.length > 4 && part.startsWith("**") && part.endsWith("**")) out.append(el("strong", { textContent: part.slice(2, -2) }));
    else if (part.length > 2 && part.startsWith("`") && part.endsWith("`")) out.append(el("code", { textContent: part.slice(1, -1) }));
    else out.append(part);
  }
  return out;
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
      el("td", { className: "before" }, r.before ? richText(r.before) : "\u2014"), el("td", {}, richText(r.now))))))
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
  $("tab-nations").addEventListener("click", () => showView("nations"));
  $("tab-ai").addEventListener("click", () => showView("ai"));
  $("tab-values").addEventListener("click", () => showView(state.valuesPart || "values"));
  valuesEvents();
  $("tab-decoy").addEventListener("click", () => showView("decoy"));
  $("ai-script").addEventListener("change", (e) => { if (e.target.value) showAIScript(e.target.value); });
  $("ai-script-copy").addEventListener("click", copyAIScript);
  scriptEvents();
  $("tab-maps").addEventListener("click", () => showView("maps"));
  $("tab-settings").addEventListener("click", () => showView("settings"));
  $("set-game-change").addEventListener("click", () => chooseGame().catch(problem));
  $("set-copies-change").addEventListener("click", () => changeCopies(true).catch(problem));
  $("set-copies-default").addEventListener("click", () => changeCopies(false).catch(problem));
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
  $("flag-guide-close").addEventListener("click", () => $("flag-guide").close());
  $("flag-guide-search").addEventListener("input", renderFlagGuide);
  $("edit-mods-close").addEventListener("click", () => $("edit-mods").close());
  $("edit-mods-search").addEventListener("input", renderEditMods);
  $("test").addEventListener("click", testInGame);
  $("test-log-close").addEventListener("click", () => $("test-panel").classList.add("hidden"));
  $("test-log-copy").addEventListener("click", copyTestLog);
  let timer = null;
  $("unit-group").addEventListener("change", (e) => { state.group = e.target.value; refreshList(); });
  $("search").addEventListener("input", (e) => {
    state.search = e.target.value;
    renderSearchHints();
    clearTimeout(timer);
    timer = setTimeout(refreshList, 150);
  });
  $("search").addEventListener("focus", renderSearchHints);
  $("search").addEventListener("blur", () => { keepSearch($("search").value); renderSearchHints(); });
  $("search").addEventListener("keydown", (e) => { if (e.key === "Enter") keepSearch($("search").value); });
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
  // the start screen (startflow.js, loaded after this file: the page's scripts all read first)
  if (document.readyState === "loading") await new Promise((ok) => document.addEventListener("DOMContentLoaded", ok, { once: true }));
  if (window.StartFlow) await window.StartFlow.atStart(status.ready);
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

// --- closing with something not saved yet (the owner, 2026-10-16: "a warning before closing with unsaved
// changes"): most of the Studio saves each change as it's made, so what can be lost is a script edited and not saved,
// text typed in a box and not yet entered (a box takes its text on Enter or when the focus leaves it, and closing
// the window does neither), the music editor holding a sound not used yet, and a save or a Test in game still running.
// The page says which to the window (StudioApi.unsaved), which asks before closing (rusemod.webui); in a web browser
// the browser's own "Leave site?" asks. ---
let typedAt = null;  // the box being typed in, with its text when the focus came to it (or when it last took it)
document.addEventListener("focusin", (e) => {
  const t = e.target;
  const box = t && (t.tagName === "TEXTAREA" || (t.tagName === "INPUT" && ["text", "number", ""].includes(t.type)));
  typedAt = box && !t.readOnly && !t.disabled ? { el: t, value: t.value } : null;
});
document.addEventListener("change", (e) => { if (typedAt && e.target === typedAt.el) typedAt.value = e.target.value; });

function unsavedReasons() {
  const w = state.words, out = [], area = $("ai-script-area");
  if (area && area.value !== scriptSaved && !area.disabled && area.value.trim()) out.push(w.unsaved_script);
  const t = typedAt;
  if (t && t.el.isConnected && document.activeElement === t.el && t.el.value !== t.value && t.el !== area) {
    out.push(w.unsaved_typed);
  }
  if (window.SoundView && SoundView.editing && SoundView.editing()) out.push(w.unsaved_music);
  if ((window.MapView && MapView.busy && MapView.busy()) || (window.MissionView && MissionView.busy && MissionView.busy())
    || (window.SoundView && SoundView.busy && SoundView.busy())) out.push(w.unsaved_saving);
  if ($("test") && $("test").dataset.running === "1") out.push(w.unsaved_test);
  return out.filter(Boolean);
}

let unsavedSaid = "";
function tellUnsaved() {
  if (!started || !window.pywebview || !window.pywebview.api || !window.pywebview.api.unsaved) return;
  const w = state.words, reasons = unsavedReasons(), key = reasons.join("\n");
  if (key === unsavedSaid) return;
  unsavedSaid = key;
  const ask = reasons.length ? { title: w.unsaved_title, text: `${w.unsaved_text}\n\n${reasons.map((r) => `• ${r}`).join("\n")}\n\n${w.unsaved_close}` } : null;
  Promise.resolve(api().unsaved(ask)).catch(() => { unsavedSaid = ""; });  // (said again on the next look)
}
setInterval(tellUnsaved, 700);
window.addEventListener("beforeunload", (e) => {
  if (!unsavedReasons().length) return;
  e.preventDefault();
  e.returnValue = "";  // the browser asks "Leave site?" (its own words)
});

// --- search with tags (the owner's Studio 1.0 list, item 11; the design: studio-tools-design §11.3; StudioApi.units
// and ammo say the "tags" of the list): every word must match, #tags narrow it (#us, #air, #armor, #new...). Typing #
// shows the tags there are, a click finishes the word; an empty box shows the recent searches, kept by the Studio
// (prefs "searches", RECENT_SEARCHES of them). Shown while the box has the focus. ---
const RECENT_SEARCHES = 8;
let searchTags = [];   // [{tag, label}]: the tags of the list shown

function recentSearches() {
  const kept = state.prefs && state.prefs.searches;
  return Array.isArray(kept) ? kept.filter((s) => typeof s === "string" && s.trim()) : [];
}

function keepSearch(text) {
  const said = (text || "").trim();
  if (!said || recentSearches()[0] === said) return;
  const list = [said, ...recentSearches().filter((s) => s !== said)].slice(0, RECENT_SEARCHES);
  state.prefs = { ...state.prefs, searches: list };
  Promise.resolve().then(() => api().set_pref("searches", list)).catch(() => {});
}

function setSearch(text) {
  const box = $("search");
  box.value = text;
  state.search = text;
  box.focus();
  refreshList();
  renderSearchHints();
}

function renderSearchHints() {
  const w = state.words || {}, box = $("search-hints"), input = $("search");
  if (!box || !input) return;
  const v = input.value, last = v.split(/\s+/).pop() || "";
  const chip = (text, tip, then) => {
    const c = el("button", { type: "button", className: "chip", textContent: text, title: tip || "" });
    c.addEventListener("mousedown", (e) => e.preventDefault());   // (the box keeps the focus)
    c.addEventListener("click", then);
    return c;
  };
  let chips = [];
  if (last.startsWith("#")) {   // the tags that start with what's typed, the ones already in the search left out
    const part = last.slice(1).toLowerCase(), before = v.slice(0, v.length - last.length);
    const used = new Set(before.toLowerCase().split(/\s+/).filter((t) => t.startsWith("#")).map((t) => t.slice(1)));
    chips = searchTags.filter((t) => t.tag.startsWith(part) && !used.has(t.tag)).slice(0, 16)
      .map((t) => chip("#" + t.tag, fill(w.tip_search_tag, { tag: t.tag, label: t.label }), () => setSearch(before + "#" + t.tag + " ")));
    if (chips.length) chips.unshift(el("span", { className: "muted small", textContent: w.search_tags || "" }));
  } else if (!v.trim()) {
    chips = recentSearches().map((s) => chip(s, w.tip_search_recent, () => setSearch(s)));
    if (chips.length) chips.unshift(el("span", { className: "muted small", textContent: w.search_recent || "" }));
  }
  box.replaceChildren(...chips);
  box.classList.toggle("hidden", document.activeElement !== input || !chips.length);
}

// --- number rows: every slider shown as [−] number [+] (the owner's Studio 1.0 list, item 11: "+/- number rows instead
// of sliders"; the design: studio-tools-design §11.1, rows typed or stepped, steps landing on round numbers). The
// slider stays, hidden, so the code that reads it, sets it and listens to it is unchanged: typing or stepping sets its
// value and sends it the input and change events a drag would, and a value set by code shows in the row. A slider's
// data-stepper: "buttons", − and + alone (its value is a place on a scale, or it has a number box of its own beside
// it); "beside", the slider kept with − and + round it (its marks are drawn along it); "none", left alone.
// data-click: a click's step when the slider's own is too fine (a step of 1 m on a range of kilometres).
const STEP_HOLD_MS = 400, STEP_REPEAT_MS = 70;   // held: one step, then a step every 70 ms after 0.4 s
const NATIVE_VALUE = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");

function holdToRepeat(button, act, end) {
  let timer = null;
  const stop = () => {
    if (timer === null) return;
    clearTimeout(timer);
    timer = null;
    window.removeEventListener("pointerup", stop);
    end();
  };
  button.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 || button.disabled) return;
    e.preventDefault();
    act();
    const again = () => { act(); timer = setTimeout(again, STEP_REPEAT_MS); };
    timer = setTimeout(again, STEP_HOLD_MS);
    window.addEventListener("pointerup", stop);   // (a button turned off at the end of its range gets no pointerup)
  });
  button.addEventListener("pointerleave", stop);
  button.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    e.preventDefault();
    act();
    end();
  });
}

function stepperOf(range) {
  const how = range.dataset.stepper || "";
  if (range.dataset.stepped || how === "none") return;
  range.dataset.stepped = "1";
  const less = el("button", { type: "button", className: "step-btn", textContent: "−" });
  const more = el("button", { type: "button", className: "step-btn", textContent: "+" });
  const box = how ? null : el("input", { type: "number", className: "step-value" });
  const row = el("span", { className: "stepper" + (how === "beside" ? " beside" : "") });
  range.after(row);
  row.append(less);
  if (how === "beside") row.append(range);   // the slider between the two
  else range.classList.add("stepped");       // (hidden: the row stands for it)
  if (box) row.append(box);
  row.append(more);
  const read = () => NATIVE_VALUE.get.call(range);
  const num = (v, d) => (v !== "" && Number.isFinite(Number(v)) ? Number(v) : d);
  const lim = () => ({ lo: num(range.min, 0), hi: num(range.max, 100), step: num(range.step, 1) || 1 });
  const places = (s) => { const t = String(s); return t.includes(".") ? t.length - t.indexOf(".") - 1 : 0; };
  const sync = () => {
    const w = state.words || {}, { lo, hi, step } = lim(), t = typed();
    const v = t ? num(t.value, Number(read())) : Number(read());
    less.disabled = range.disabled || v <= (t ? num(t.min, lo) : lo);
    more.disabled = range.disabled || v >= (t ? num(t.max, hi) : hi);
    const what = range.title || (range.closest("[title]") || {}).title || range.getAttribute("aria-label") || "";
    less.title = w.tip_step_less || "";
    more.title = w.tip_step_more || "";
    less.setAttribute("aria-label", w.step_less || "−");
    more.setAttribute("aria-label", w.step_more || "+");
    if (box && box.isConnected) {
      Object.assign(box, { min: String(lo), max: String(hi), step: String(step), disabled: range.disabled, title: what });
      if (document.activeElement !== box) box.value = read();
    }
  };
  Object.defineProperty(range, "value", {   // a value set by code shows in the row
    configurable: true,
    get() { return NATIVE_VALUE.get.call(this); },
    set(v) { NATIVE_VALUE.set.call(this, v); sync(); } });
  const put = (v, done) => {
    const { lo, hi, step } = lim();
    const kept = Math.min(hi, Math.max(lo, Number((Math.round((v - lo) / step) * step + lo).toFixed(places(step)))));
    if (String(kept) !== read()) {
      NATIVE_VALUE.set.call(range, String(kept));
      range.dispatchEvent(new Event("input", { bubbles: true }));
    }
    if (done) range.dispatchEvent(new Event("change", { bubbles: true }));
    sync();
  };
  // the tool's own typed box (maps.js typedBeside: a value past the slider's ends, the owner's "all of them",
  // 2026-10-10), when it has one: it's the row's number, and the steps go through it (as far as it takes)
  const typed = () => row.querySelector("input.typed-number");
  const next = (v, dir) => {   // the next round number of the click's step (7 + 5 -> 10, not 12)
    const c = num(range.dataset.click, lim().step);
    return dir > 0 ? (Math.floor(v / c + 1e-9) + 1) * c : (Math.ceil(v / c - 1e-9) - 1) * c;
  };
  const by = (dir) => {
    const t = typed();
    if (!t) { put(next(Number(read()), dir), false); return; }
    const lo = num(t.min, -Infinity), hi = num(t.max, Infinity);
    t.value = String(Math.min(hi, Math.max(lo, Number(next(num(t.value, 0), dir).toFixed(6)))));
    t.dispatchEvent(new Event("change"));   // (its own check, then the tool's value: maps.js typedBeside)
    sync();
  };
  const changed = () => { if (!typed()) range.dispatchEvent(new Event("change", { bubbles: true })); };
  holdToRepeat(less, () => by(-1), changed);
  holdToRepeat(more, () => by(1), changed);
  range._adoptTyped = (t) => {   // its typed box comes in between − and +, in the place of the row's own
    if (box) box.remove();
    more.before(t);
    t.addEventListener("change", sync);
    sync();
  };
  if (box) {
    box.addEventListener("input", () => {   // live while it's a number in range; kept in range when done
      const { lo, hi } = lim(), v = num(box.value, NaN);
      if (v >= lo && v <= hi) put(v, false);
    });
    box.addEventListener("change", () => put(num(box.value, Number(read())), true));
    box.addEventListener("keydown", (e) => { if (e.key === "Enter") box.blur(); });
  }
  new MutationObserver(sync).observe(range, { attributes: true, attributeFilter: ["min", "max", "step", "disabled", "title"] });
  sync();
}

function steppersIn(root) {
  for (const r of root.querySelectorAll('input[type="range"]')) stepperOf(r);
}
// a typed box put beside a slider that has its row (maps.js typedBeside: slider.after(box)): taken into the row
function adoptTyped(t) {
  const range = t.previousElementSibling;
  if (range && range.matches('input[type="range"]') && range._adoptTyped) range._adoptTyped(t);
}
steppersIn(document);
new MutationObserver((changes) => {   // sliders made later (a tray, a unit's page, a dialog) get their rows too
  for (const c of changes) {
    for (const n of c.addedNodes) {
      if (n.nodeType !== 1) continue;
      if (n.matches('input[type="range"]')) stepperOf(n);
      else if (n.matches("input.typed-number")) adoptTyped(n);
      else steppersIn(n);
    }
  }
}).observe(document.body, { childList: true, subtree: true });

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start().catch(problem);
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
