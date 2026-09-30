// The home screen (PLAN.md L5, screen 6): mod sets on the left with the mod library under them, the active set and
// Play on the right. Mod sets are made and changed here (new, edit, rename, duplicate, delete); mods come into the
// library from a file dialog or by dropping them on the window. It talks to LauncherApi (ruse_launcher/api.py)
// through window.pywebview.api; in a normal browser, open index.html?fake to use the made-up API in fake-api.js.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { lang: "us", words: {}, languages: [], status: null, sets: [], library: [], active: "vanilla",
  playing: false, editing: null,   // editing: { id (null for a new set), name, mods: [entries in order] }
  browse: null,                    // browse: the mod index on screen { mods, source, as_of, message, search, busy }
  importing: null };               // importing: a pasted load order { text, check (what the launcher found), name }

function api() {
  return window.pywebview.api;
}

function el(tag, props, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props || {});
  for (const c of children) node.append(c);
  return node;
}

function text(node, value) {
  node.textContent = value || "";
}

function fill(word, values) {
  return Object.entries(values || {}).reduce((s, [k, v]) => s.split(`{${k}}`).join(String(v)), word || "");
}

// The language is kept by the launcher (settings.json in the platform folder, api.set_pref): the window's own
// storage is lost every start (its address changes), and on an update or a reinstall.
async function loadLang() {
  try {
    const kept = (await api().prefs()).lang;
    if (kept) return kept;
  } catch { /* an older launcher: the window's storage */ }
  try { return localStorage.getItem("launcher.lang"); } catch { return null; }
}

function saveLang(lang) {
  try { localStorage.setItem("launcher.lang", lang); } catch { /* private window: fine */ }
  Promise.resolve().then(() => api().set_pref("lang", lang)).catch(() => {});
}

// --- messages ---
function setMessage(message, kind) {
  const node = $("play-message");
  text(node, message);
  node.className = "message" + (kind ? " " + kind : "");
}

function problem(err) {
  setMessage((err && err.message) || String(err), "bad");
}

// --- words ---
async function setLanguage(lang) {
  state.lang = lang;
  saveLang(lang);
  state.words = await api().strings(lang);
  renderUpdate();
  const w = state.words;
  text($("lang-label"), w.language);
  $("lang").replaceChildren(...state.languages.map((l) =>
    el("option", { value: l.code, textContent: l.name, selected: l.code === lang })));
  text($("choose"), w.choose_folder);
  text($("settings-open"), w.settings_tab);
  text($("sets-title"), w.mod_sets);
  text($("new-set"), w.new_set);
  text($("library-title"), w.library);
  text($("add-mod"), w.add_mod);
  text($("drop-hint"), w.drop_hint);
  text($("library-empty"), w.library_empty);
  text($("details"), w.details);
  text($("join"), w.join);
  text($("browse"), w.browse);
  $("join").title = w.coming_soon;
  text($("browse-title"), w.browse);
  $("browse-search").placeholder = w.search_mods;
  text($("browse-refresh"), w.refresh_list);
  text($("browse-back"), w.back);
  text($("browse-help"), w.browse_help);
  text($("drop-text"), w.drop_here);
  text($("import-set"), w.import_order);
  text($("guide-title"), w.guide_title);
  text($("guide-add"), w.guide_add);
  text($("guide-set"), w.guide_set);
  text($("guide-play"), w.guide_play);
  text($("share-title"), w.share_title);
  text($("share-help"), w.share_help);
  text($("share-copy"), w.copy);
  text($("share-close"), w.cancel);
  text($("import-title"), w.import_order);
  text($("import-help"), w.import_help);
  $("import-text").placeholder = w.import_paste;
  text($("import-check"), w.check_order);
  text($("import-cancel"), w.cancel);
  if (state.status) renderStatus(state.status); else text($("status"), w.looking);
  render();
}

// --- the game ---
function renderStatus(status) {
  state.status = status;
  const node = $("status");
  text(node, status.message);
  node.className = "status " + (status.found ? "good" : "bad");
  $("choose").classList.toggle("hidden", status.found);
}

// --- what's on screen ---
function render() {
  renderSets();
  renderLibrary();
  $("settings-view").classList.add("hidden");
  if (state.settings) renderSettings();
  else if (state.browse) renderBrowse(); else if (state.importing) renderImport(); else if (state.editing) renderEditor();
  else renderActive();
}

// --- Settings: one entry per section (its words are set_<id>_title); a new setting is one more entry and its
// section in index.html. What they change is kept by the launcher (settings.json), not by the window.
const SETTINGS = [
  { id: "language", render() {} },  // the list is filled at start and saved on change
  { id: "game", render() {
    const w = state.words, s = state.status || {};
    text($("set-game-path"), s.found ? fill(w.set_game_path, { path: s.game_dir || "" }) : (s.message || w.set_game_none));
    text($("set-game-change"), w.set_game_change);
  } },
  { id: "updates", render() {
    const w = state.words, u = state.update || {};
    text($("set-updates-text"), u.checking ? w.set_updates_checking : u.available ? fill(w.update_out, { app: APP_NAME, version: u.version })
      : u.error ? u.error : fill(w.set_updates_latest, { version: u.version || "" }));
    text($("set-updates-check"), w.set_updates_check);
  } },
];

function renderSettings() {
  const w = state.words;
  for (const id of ["set-view", "editor", "import-view", "browse-view"]) $(id).classList.add("hidden");
  $("settings-view").classList.remove("hidden");
  text($("settings-title"), w.settings_title);
  text($("settings-back"), w.back || "Back");
  for (const s of SETTINGS) {
    text($(`set-${s.id}-title`), w[`set_${s.id}_title`] || s.id);
    s.render();
  }
}

function useLists(res) {
  state.sets = res.sets;
  state.library = res.library;
  state.checks = {};  // the library may have changed (a mod replaced by a newer version): check sets again
  if (res.set) state.active = res.set;
  if (!state.sets.some((s) => s.id === state.active)) state.active = "vanilla";
  render();
}

async function refresh() {
  try {
    renderStatus(await api().status());
    useLists({ sets: await api().mod_sets(), library: await api().library() });
  } catch (err) { problem(err); }
}

function activeSet() {
  return state.sets.find((s) => s.id === state.active) || state.sets[0];
}

function setName(set) {
  return set.id === "vanilla" ? state.words.vanilla : set.name;
}

function modCount(set) {
  const w = state.words;
  if (set.error) return w.has_mistake;
  if (!set.mods.length) return w.no_mods;
  return set.mods.length === 1 ? w.one_mod : fill(w.n_mods, { n: set.mods.length });
}

// --- the list of mod sets ---
function renderSets() {
  $("set-list").replaceChildren(...state.sets.map((set) => {
    const card = el("button", { type: "button", className: "set-card" },
      el("span", { className: "name", textContent: setName(set) }),
      el("span", { className: set.error ? "warn" : "meta", textContent: modCount(set) }));
    card.setAttribute("aria-pressed", String(set.id === state.active));
    card.addEventListener("click", () => {
      if (state.playing) return;
      state.active = set.id;
      state.editing = null;
      state.browse = null;
      state.importing = null;
      state.settings = false;
      render();
    });
    return el("li", {}, card);
  }));
  $("new-set").disabled = state.playing;
  $("import-set").disabled = state.playing;
  $("browse").disabled = state.playing;
}

// --- the active set ---
function confirmRow(question, yesText, onYes, holder, trigger) {
  const w = state.words;
  const row = el("div", { className: "confirm" }, el("span", { textContent: question }));
  const yes = el("button", { type: "button", className: "small danger", textContent: yesText });
  const no = el("button", { type: "button", className: "small ghost", textContent: w.cancel });
  yes.addEventListener("click", async () => {
    yes.disabled = true;
    try { await onYes(); } catch (err) { problem(err); if (trigger) trigger.disabled = false; }
    row.remove();
  });
  no.addEventListener("click", () => { row.remove(); if (trigger) trigger.disabled = false; });
  row.append(yes, no);
  holder.append(row);
  yes.focus();
}

function renderActive() {
  const w = state.words;
  const set = activeSet();
  $("set-view").classList.remove("hidden");
  $("editor").classList.add("hidden");
  $("browse-view").classList.add("hidden");
  $("import-view").classList.add("hidden");
  for (const row of $("set-view").querySelectorAll(".confirm")) row.remove();  // a question left from before
  if (!set) return;
  text($("active-name"), setName(set));
  text($("active-description"), set.id === "vanilla" ? w.vanilla_desc : set.description);
  // new players: how mods get into a game, shown on Vanilla (and until the library has a mod)
  $("guide").classList.toggle("hidden", !(set.id === "vanilla" || !state.library.length));
  if ($("share-box").dataset.set !== set.id) $("share-box").classList.add("hidden");
  const actions = $("set-actions");
  actions.replaceChildren();
  if (set.editable && !state.playing) {
    const edit = el("button", { type: "button", className: "small ghost", textContent: w.edit });
    edit.addEventListener("click", () => openEditor(set));
    const rename = el("button", { type: "button", className: "small ghost", textContent: w.rename });
    rename.addEventListener("click", () => renameSet(set));
    const dup = el("button", { type: "button", className: "small ghost", textContent: w.duplicate });
    dup.addEventListener("click", async () => {
      dup.disabled = true;
      try {
        useLists(await api().duplicate_set(set.id, fill(w.copy_name, { name: set.name })));
        setMessage(fill(w.set_saved, { name: activeSet().name }), "good");
      } catch (err) { problem(err); dup.disabled = false; }
    });
    const del = el("button", { type: "button", className: "small ghost danger", textContent: w.delete });
    del.addEventListener("click", () => {
      del.disabled = true;
      confirmRow(fill(w.really_delete_set, { name: set.name }), w.delete, async () => {
        useLists(await api().delete_set(set.id));
        setMessage(fill(w.set_deleted, { name: set.name }), "good");
      }, $("set-view"), del);
    });
    const share = el("button", { type: "button", className: "small ghost", textContent: w.share });
    share.disabled = !set.mods.length;
    share.addEventListener("click", () => shareSet(set));
    actions.append(edit, rename, dup, share, del);
  }
  $("active-mods").replaceChildren(...set.mod_names.map((n) => el("li", { textContent: n })));
  const err = $("active-error");
  text(err, set.error ? fill(w.set_mistake, { error: set.error }) : "");
  err.classList.toggle("hidden", !set.error);
  const play = $("play");
  text(play, set.id === "vanilla" ? w.play : fill(w.play_set, { name: set.name }));
  const check = set.error ? null : checkOf(set.mods, () => { if (!state.editing && activeSet() === set) renderActive(); });
  renderClashes($("active-clashes"), check, set.editable ? async () => {
    try {
      useLists(await api().best_order(set.id));
      setMessage(fill(w.best_order_done, { name: set.name }), "good");
    } catch (e) { problem(e); }
  } : null);
  play.disabled = state.playing || Boolean(set.error) || Boolean(check && check.hard.length);
}

// --- mods that don't go together (rusemod.rmod.clashes): asked for whenever a set is shown or its mods change ---
// state.checks: mods (in order, joined) -> { hard, soft } from the launcher; a missing entry is being fetched.
function checkOf(mods, then) {
  if (mods.length < 2) return { hard: [], soft: [] };
  const key = mods.join("\n");
  state.checks = state.checks || {};
  const known = state.checks[key];
  if (known) return known;
  if (!state.checking) state.checking = {};
  if (!state.checking[key]) {
    state.checking[key] = api().check_mods(mods).then((res) => { state.checks[key] = res; then(res); })
      .catch(problem).finally(() => { delete state.checking[key]; });
  }
  return null;  // not known yet: the boxes stay empty until the answer comes
}

function clashText(c) {
  const w = state.words;
  const kinds = { "script": w.kind_script, "script archive": w.kind_script_archive, "video": w.kind_video, "sound": w.kind_sound,
    "sound archive": w.kind_sound_archive, "picture": w.kind_picture, "map file": w.kind_map_file, "text file": w.kind_text_file,
    "game data": w.kind_game_data };
  const values = { a: c.a, b: c.b, n: c.count, example: c.what, file: c.what.split("/").pop(), kind: kinds[c.file_kind] || w.kind_game_data };
  if (c.kind === "file" || c.kind === "script") return fill(w.clash_file, values);
  if (c.kind === "archive") return fill(w.clash_archive, values);
  if (c.kind === "create") return fill(w.clash_create, values);
  if (c.kind === "text") return fill(c.count === 1 ? w.clash_text_one : w.clash_text, values);
  return fill(c.count === 1 ? w.clash_value_one : w.clash_value, values);
}

// onBest: puts the mods in the best order (check.best: rusemod.rmod.best_order), offered in the box of overwrites
function renderClashes(holder, check, onBest) {
  const w = state.words;
  holder.replaceChildren();
  if (!check) return;
  const item = (c) => {
    const li = el("li", { textContent: clashText(c) });
    if ((c.kind === "file" || c.kind === "script") && c.what.includes("/")) li.append(" ", el("span", { className: "path", textContent: c.what }));
    return li;
  };
  if (check.hard.length) {  // open, since Play is off because of it; folds like the yellow one (a 75-mod set lists dozens)
    const box = el("details", { className: "clash-box hard", role: "alert" },
      el("summary", {}, el("span", { textContent: w.clash_cant_play }), " ", el("span", { className: "count", textContent: `(${check.hard.length})` })),
      el("ul", {}, ...check.hard.map(item)));
    box.open = true;
    holder.append(box);
  }
  if (check.soft.length) {
    const box = el("details", { className: "clash-box soft" }, el("summary", { textContent: fill(w.clash_overwrites, { n: check.soft.length }) }),
      el("ul", {}, ...check.soft.map(item)));
    box.open = check.soft.length <= 3 || Boolean(check.best && onBest);
    if (check.best && onBest) {
      const button = el("button", { type: "button", className: "small", textContent: w.best_order });
      button.addEventListener("click", async () => { button.disabled = true; try { await onBest(check.best); } finally { button.disabled = false; } });
      const why = el("p", { className: "muted", textContent: w.best_order_why });
      if (check.helped && check.helped.length) why.append(" ", fill(w.best_order_helps, { names: check.helped.join(", ") }));
      box.append(el("div", { className: "best-order" }, why, button));
    }
    holder.append(box);
  }
}

function renameSet(set) {
  const w = state.words;
  const head = $("active-name");
  const box = el("input", { value: set.name, maxLength: 60, className: "rename" });
  box.setAttribute("aria-label", w.set_name);
  const save = el("button", { type: "button", className: "small", textContent: w.save });
  const cancel = el("button", { type: "button", className: "small ghost", textContent: w.cancel });
  const form = el("form", { className: "rename-form" }, box, save, cancel);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!box.value.trim()) return;
    save.disabled = true;
    try {
      useLists(await api().save_set(set.id, box.value.trim()));
      setMessage(fill(w.set_saved, { name: box.value.trim() }), "good");
    } catch (err) { problem(err); save.disabled = false; }
  });
  save.addEventListener("click", () => form.requestSubmit());
  cancel.addEventListener("click", () => renderActive());
  head.replaceChildren(form);
  $("set-actions").replaceChildren();
  box.focus();
  box.select();
}

// --- sharing a load order: the text RUSE Mod Manager copies and reads too (rusemod/loadorder.py) ---
async function shareSet(set) {
  const box = $("share-box");
  try {
    const res = await api().share_set(set.id);
    $("share-text").value = res.text;
    box.dataset.set = set.id;
    box.classList.remove("hidden");
    text($("share-note"), "");
    copyShared();
  } catch (err) { problem(err); }
}

async function copyShared() {
  const area = $("share-text");
  try {
    await navigator.clipboard.writeText(area.value);
    text($("share-note"), state.words.copied);
  } catch {
    area.focus();
    area.select();  // no clipboard access here: selected, so Ctrl+C copies it
  }
}

function openImport() {
  state.editing = null;
  state.browse = null;
  state.settings = false;
  state.importing = { text: "", check: null, name: "" };
  render();
  $("import-text").value = "";
  $("import-text").focus();
}

function renderImport() {
  const w = state.words, imp = state.importing;
  $("set-view").classList.add("hidden");
  $("editor").classList.add("hidden");
  $("browse-view").classList.add("hidden");
  $("import-view").classList.remove("hidden");
  const out = $("import-result");
  out.replaceChildren();
  const c = imp.check;
  if (!c) return;
  const total = c.found.length + c.missing.length;
  const lines = [el("p", { className: c.found.length ? "good" : "bad",
    textContent: fill(w.import_found, { n: c.found.length, total }) })];
  if (c.wrong_game) lines.push(el("p", { className: "warn", textContent: w.import_wrong_game }));
  if (c.missing.length) {
    lines.push(el("p", { className: "warn", textContent: fill(w.import_missing, {
      names: c.missing.map((m) => (m.version ? `${m.name} (v${m.version})` : m.name)).join(", ") }) }));
  }
  if (c.other_version.length) {
    lines.push(el("p", { className: "muted", textContent: fill(w.import_version, {
      list: c.other_version.map((m) => `${m.name} (${m.have || "?"} / ${m.wanted})`).join(", ") }) }));
  }
  const order = el("ol", { className: "mods" }, ...c.found.map((m) => el("li", { textContent: m.version
    ? `${m.name} · ${fill(w.version_v, { v: m.version })}` : m.name })));
  const name = el("input", { value: imp.name, maxLength: 60, placeholder: w.set_name, autocomplete: "off" });
  name.setAttribute("aria-label", w.set_name);
  name.addEventListener("input", () => { imp.name = name.value; });
  const make = el("button", { type: "button", className: "small", textContent: w.make_set, disabled: !c.found.length });
  make.addEventListener("click", async () => {
    make.disabled = true;
    try {
      const res = await api().import_set(imp.text, imp.name.trim());
      state.importing = null;
      useLists(res);
      setMessage(fill(w.import_done, { name: activeSet().name }), "good");
    } catch (err) { problem(err); make.disabled = false; }
  });
  out.append(...lines, order, el("label", { className: "field" }, el("span", { textContent: w.set_name }), name),
    el("div", { className: "actions" }, make));
}

async function checkImport() {
  const imp = state.importing;
  imp.text = $("import-text").value;
  try {
    imp.check = await api().import_check(imp.text);
    if (!imp.name) imp.name = imp.check.set_name || "";
    renderImport();
  } catch (err) {
    imp.check = null;
    renderImport();
    $("import-result").replaceChildren(el("p", { className: "bad", textContent: (err && err.message) || String(err) }));
  }
}

// --- the editor: a new mod set, or a set's mods and their order ---
function openEditor(set) {
  state.settings = false;
  state.editing = set ? { id: set.id, name: set.name, mods: set.mods.slice(), names: set.mod_names.slice() }
    : { id: null, name: "", mods: [], names: [] };
  render();
}

function renderEditor() {
  const w = state.words;
  const ed = state.editing;
  $("set-view").classList.add("hidden");
  $("browse-view").classList.add("hidden");
  $("import-view").classList.add("hidden");
  const form = $("editor");
  form.classList.remove("hidden");
  const name = el("input", { value: ed.name, maxLength: 60, required: true, placeholder: w.set_name, autocomplete: "off" });
  name.setAttribute("aria-label", w.set_name);
  name.addEventListener("input", () => { ed.name = name.value; });
  const rows = el("ul", { className: "pick-list" });
  const known = new Map(state.library.map((m) => [m.id, m]));
  const inSet = ed.mods.map((entry, i) => ({ entry, name: ed.names[i], mod: known.get(entry) || null, on: true }));
  const others = state.library.filter((m) => !ed.mods.includes(m.id)).map((m) => ({ entry: m.id, name: m.name, mod: m, on: false }));
  for (const [i, r] of inSet.concat(others).entries()) {
    const tick = el("input", { type: "checkbox", checked: r.on });
    tick.addEventListener("change", () => {
      if (tick.checked) { ed.mods.push(r.entry); ed.names.push(r.name); }
      else { const k = ed.mods.indexOf(r.entry); ed.mods.splice(k, 1); ed.names.splice(k, 1); }
      renderEditor();
    });
    const label = el("label", {}, tick, " ", el("span", { className: "name", textContent: r.name }));
    if (r.mod && r.mod.version) label.append(el("span", { className: "meta", textContent: " " + fill(w.version_v, { v: r.mod.version }) }));
    if (!r.mod) label.append(el("span", { className: "meta", textContent: " · " + w.from_folder }));
    const li = el("li", {}, label);
    if (r.on) {
      const up = el("button", { type: "button", className: "small ghost arrow", textContent: "↑", title: w.move_up, disabled: i === 0 });
      const down = el("button", { type: "button", className: "small ghost arrow", textContent: "↓", title: w.move_down,
        disabled: i === inSet.length - 1 });
      up.setAttribute("aria-label", w.move_up);
      down.setAttribute("aria-label", w.move_down);
      const swap = (a, b) => {
        [ed.mods[a], ed.mods[b]] = [ed.mods[b], ed.mods[a]];
        [ed.names[a], ed.names[b]] = [ed.names[b], ed.names[a]];
        renderEditor();
      };
      up.addEventListener("click", () => swap(i, i - 1));
      down.addEventListener("click", () => swap(i, i + 1));
      li.append(el("span", { className: "order" }, up, down));
    }
    rows.append(li);
  }
  const save = el("button", { type: "submit", className: "small", textContent: ed.id ? w.save : w.create });
  const cancel = el("button", { type: "button", className: "small ghost", textContent: w.cancel });
  cancel.addEventListener("click", () => { state.editing = null; render(); });
  // the ticked mods checked against each other as they're ticked and moved, so a clash shows before the set is saved
  const clashes = el("div", { className: "clashes" });
  const toBest = (best) => {  // the editor's own order changes; Save keeps it
    const names = Object.fromEntries(ed.mods.map((m, i) => [m, ed.names[i]]));
    ed.mods = best.slice();
    ed.names = best.map((m) => names[m]);
    renderEditor();
  };
  renderClashes(clashes, checkOf(ed.mods, (res) => { if (state.editing === ed) renderClashes(clashes, res, toBest); }), toBest);
  form.replaceChildren(
    el("h1", { textContent: ed.id ? w.edit : w.new_set }),
    el("label", { className: "field" }, el("span", { textContent: w.set_name }), name),
    el("p", { className: "muted", textContent: state.library.length || ed.mods.length ? w.tick_mods : w.library_empty_for_set }),
    rows,
    clashes,
    el("div", { className: "actions" }, save, cancel));
  form.onsubmit = async (e) => {
    e.preventDefault();
    if (!ed.name.trim()) { name.focus(); return; }
    save.disabled = true;
    try {
      const res = ed.id ? await api().save_set(ed.id, ed.name.trim(), ed.mods) : await api().new_set(ed.name.trim(), ed.mods);
      state.editing = null;
      useLists(res);
      setMessage(fill(w.set_saved, { name: ed.name.trim() }), "good");
    } catch (err) { problem(err); save.disabled = false; }
  };
  if (!ed.id && !ed.name) name.focus();
}

// --- Browse mods: the mod index (MOD_FORMAT §15), installs checked against it ---
async function openBrowse(fresh) {
  state.settings = false;
  state.editing = null;
  state.importing = null;
  state.browse = state.browse || { mods: [], source: "", as_of: "", message: "", search: "", busy: {} };
  state.browse.loading = true;
  render();
  try {
    const res = await api().browse(state.browse.search, Boolean(fresh));
    Object.assign(state.browse, res, { loading: false });
  } catch (err) { state.browse.loading = false; problem(err); }
  render();
}

function browseMessage(message, kind) {
  const node = $("browse-message");
  text(node, message);
  node.className = "message" + (kind ? " " + kind : "");
}

function renderBrowse() {
  const w = state.words;
  const b = state.browse;
  $("set-view").classList.add("hidden");
  $("editor").classList.add("hidden");
  $("import-view").classList.add("hidden");
  $("browse-view").classList.remove("hidden");
  if ($("browse-search").value !== b.search) $("browse-search").value = b.search;
  const note = $("browse-note");
  if (b.source === "cache") text(note, fill(w.offline_note, { date: b.as_of }));
  else if (b.source === "none") text(note, fill(w.list_failed, { why: b.message }));
  else if (!b.loading && !b.mods.length) text(note, w.list_empty);
  else text(note, "");
  note.classList.toggle("hidden", !note.textContent);
  $("browse-list").replaceChildren(...b.mods.map((mod) => {
    const meta = [mod.version ? fill(w.version_v, { v: mod.version }) : "", mod.author ? fill(w.by, { authors: mod.author }) : "",
      mod.size_text, mod.game_build ? fill(w.for_build, { build: mod.game_build }) : ""].filter(Boolean).join(" · ");
    const li = el("li", { className: "mod-card browse-card" },
      el("span", { className: "name", textContent: mod.name }),
      el("span", { className: "meta", textContent: meta }));
    if (mod.description) li.append(el("span", { className: "desc", textContent: mod.description }));
    if (mod.tags && mod.tags.length) li.append(el("span", { className: "tags", textContent: mod.tags.join(" · ") }));
    if (mod.homepage) {
      const link = el("button", { type: "button", className: "link", textContent: w.more_info });
      link.addEventListener("click", () => api().open_link(mod.homepage).catch(problem));
      li.append(link);
    }
    const busy = Boolean(b.busy[mod.id]);
    const label = busy ? w.installing : mod.state === "installed" ? w.installed
      : mod.state === "update" ? fill(w.update_to, { v: mod.version }) : w.install;
    const button = el("button", { type: "button", className: "small", textContent: label,
      disabled: busy || mod.state === "installed" || state.playing });
    button.addEventListener("click", () => installFromIndex(mod));
    li.append(button);
    return li;
  }));
}

function followJob(job, onEnd) {
  let seen = 0;
  const tick = async () => {
    let j;
    try { j = await api().job(job, seen); } catch (err) { onEnd({ state: "failed", message: err.message }); return; }
    seen = j.count;
    if (j.state === "running") { setTimeout(tick, 400); return; }
    onEnd(j);
  };
  tick();
}

async function installFromIndex(mod) {
  const b = state.browse;
  b.busy[mod.id] = true;
  browseMessage(fill(state.words.installing, {}), "");
  renderBrowse();
  let job;
  try { ({ job } = await api().install_from_index(mod.id)); }
  catch (err) { delete b.busy[mod.id]; browseMessage(err.message, "bad"); renderBrowse(); return; }
  followJob(job, async (j) => {
    if (j.state === "done") {
      try {
        useLists({ sets: await api().mod_sets(), library: await api().library() });
        if (state.browse) Object.assign(state.browse, await api().browse(b.search, false));
      } catch (err) { problem(err); }
    }
    delete b.busy[mod.id];
    browseMessage(j.message, j.state === "done" ? "good" : "bad");
    render();
  });
}

// --- the mod library ---
function buildNote(mod) {
  const w = state.words;
  if (!mod.builds.length) return "";
  let note = fill(w.made_for, { builds: mod.builds.join(", ") });
  const build = state.status && state.status.build;
  if (build && !mod.builds.includes(build)) note += "; " + fill(w.your_build, { build });
  return note;
}

function renderLibrary() {
  const w = state.words;
  $("library-empty").classList.toggle("hidden", state.library.length > 0);
  $("mod-list").replaceChildren(...state.library.map((mod) => {
    const meta = [mod.version ? fill(w.version_v, { v: mod.version }) : "", mod.author ? fill(w.by, { authors: mod.author }) : "",
      mod.used_in ? (mod.used_in === 1 ? w.used_in_one : fill(w.used_in, { n: mod.used_in })) : ""].filter(Boolean).join(" · ");
    const li = el("li", { className: "mod-card" },
      el("span", { className: "name", textContent: mod.name }),
      el("span", { className: "meta", textContent: meta }));
    if (mod.description) li.append(el("span", { className: "meta", textContent: mod.description }));
    const note = buildNote(mod);
    if (note) li.append(el("span", { className: "meta", textContent: note }));
    if (mod.error) li.append(el("span", { className: "warn", textContent: `${w.has_mistake}: ${mod.error}` }));
    const remove = el("button", { type: "button", className: "small ghost danger", textContent: w.remove, disabled: state.playing });
    remove.addEventListener("click", () => {
      remove.disabled = true;
      confirmRow(fill(w.really_remove_mod, { name: mod.name }), w.remove, async () => {
        useLists(await api().remove_mod(mod.id));
        setMessage(fill(w.mod_removed, { name: mod.name }), "good");
      }, li, remove);
    });
    li.append(remove);
    return li;
  }));
  $("add-mod").disabled = state.playing;
}

function added(res) {
  const w = state.words;
  useLists(res);
  if (!res.mod) return;
  setMessage(res.replaced ? fill(w.mod_updated, { name: res.mod.name, v: res.mod.version }) : fill(w.mod_added, { name: res.mod.name }), "good");
}

async function addModFile() {
  const button = $("add-mod");
  button.disabled = true;
  try { added(await api().add_mod_file()); } catch (err) { problem(err); }
  button.disabled = state.playing;
}

// Dropping a mod on the window: the page can't see a dropped file's path, so the window's own side adds the mod and
// tells the page with a "mod-dropped" event (ruse_launcher/app.py; fake-api.js does the same for the preview).
function dropping(on) {
  $("drop-zone").classList.toggle("hidden", !on);
}

function watchDrops() {
  let depth = 0;
  window.addEventListener("dragenter", (e) => { e.preventDefault(); depth += 1; dropping(true); });
  window.addEventListener("dragover", (e) => { e.preventDefault(); });
  window.addEventListener("dragleave", () => { depth = Math.max(0, depth - 1); if (!depth) dropping(false); });
  window.addEventListener("drop", (e) => {
    e.preventDefault();
    depth = 0;
    dropping(false);
    if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length) setMessage(state.words.adding, "");
  });
  window.addEventListener("mod-dropped", (e) => {
    const res = e.detail;
    if (res.ok) added(res); else setMessage(res.message, "bad");
  });
}

// --- play ---
async function play() {
  state.playing = true;
  render();
  const log = $("log");
  log.textContent = "";
  $("progress").classList.remove("hidden");
  setMessage(state.words.getting_ready);
  let job;
  try { ({ job } = await api().play(state.active)); } catch (err) { problem(err); state.playing = false; render(); return; }
  let seen = 0;
  const tick = async () => {
    let j;
    try { j = await api().job(job, seen); } catch (err) { problem(err); state.playing = false; render(); return; }
    for (const line of j.lines) log.textContent += line + "\n";
    log.scrollTop = log.scrollHeight;
    seen = j.count;
    if (j.state === "running") {
      setTimeout(tick, 400);
      return;
    }
    state.playing = false;
    setMessage(j.message, j.state === "done" ? "good" : "bad");
    if (j.state === "failed") $("progress").open = true;
    render();
  };
  tick();
}

async function start() {
  state.languages = await api().languages();
  state.lang = (await loadLang()) || await api().default_language();
  if (!state.languages.some((l) => l.code === state.lang)) state.lang = "us";
  $("lang").addEventListener("change", (e) => setLanguage(e.target.value).catch(problem));
  $("settings-open").addEventListener("click", () => { state.settings = true; render(); });
  $("settings-back").addEventListener("click", () => { state.settings = false; render(); });
  $("set-game-change").addEventListener("click", async () => {
    try { renderStatus(await api().choose_game_folder()); await refresh(); } catch (err) { problem(err); }
    if (state.settings) renderSettings();
  });
  $("set-updates-check").addEventListener("click", async () => {
    state.update = { checking: true };
    renderSettings();
    try { state.update = await api().update_check(); } catch (err) { state.update = { error: (err && err.message) || String(err) }; }
    renderUpdate();
    renderSettings();
  });
  $("play").addEventListener("click", play);
  $("new-set").addEventListener("click", () => { state.importing = null; openEditor(null); });
  $("import-set").addEventListener("click", openImport);
  $("import-check").addEventListener("click", checkImport);
  $("import-cancel").addEventListener("click", () => { state.importing = null; render(); });
  $("share-copy").addEventListener("click", copyShared);
  $("share-close").addEventListener("click", () => $("share-box").classList.add("hidden"));
  $("add-mod").addEventListener("click", addModFile);
  $("browse").addEventListener("click", () => openBrowse(true));
  $("browse-refresh").addEventListener("click", () => openBrowse(true));
  $("browse-back").addEventListener("click", () => { state.browse = null; render(); });
  let searching = null;
  $("browse-search").addEventListener("input", (e) => {
    if (!state.browse) return;
    state.browse.search = e.target.value;
    clearTimeout(searching);
    searching = setTimeout(() => openBrowse(false), 200);
  });
  $("choose").addEventListener("click", async () => {
    try { renderStatus(await api().choose_game_folder()); await refresh(); } catch (err) { problem(err); }
  });
  window.addEventListener("focus", () => {
    if (!state.playing && !state.editing && !state.browse && !state.importing) refresh();  // changed while away
  });
  watchDrops();
  $("update-now").addEventListener("click", installUpdate);
  $("update-info").addEventListener("click", () => api().update_page().catch(() => {}));
  await setLanguage(state.lang);
  await refresh();
  checkUpdate();
}

// --- a newer release (rusemod/update.py): offered in the header; Update downloads it, checks it and installs it,
// then the app closes and the installer opens it again ---
const APP_NAME = "RUSE Launcher";

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

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start().catch(problem);
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
