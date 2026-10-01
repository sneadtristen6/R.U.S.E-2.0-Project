// The home screen (PLAN.md L5, screen 6): mod sets on the left with the mod library under them, the active set and
// Play on the right. Mod sets are made and changed here (new, edit, rename, duplicate, delete); mods come into the
// library from a file dialog or by dropping them on the window. It talks to LauncherApi (ruse_launcher/api.py)
// through window.pywebview.api; in a normal browser, open index.html?fake to use the made-up API in fake-api.js.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { lang: "us", words: {}, languages: [], status: null, sets: [], library: [], active: "vanilla",
  playing: false, editing: null,   // editing: { id (null for a new set), name, mods: [entries in order] }
  browse: null,                    // browse: the mod index on screen { mods, source, as_of, message, search, ticked, … }
  welcome: null,                   // welcome: the first run's "Choose your mods", the same shape as browse
  importing: null,                 // importing: a pasted load order { text, check (what the launcher found), name }
  doctor: null };                  // doctor: the troubleshooter's dialog { busy, findings, report, note, noteKind }

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
  const node = $("play-message"), w = state.words || {};
  text(node, message);
  node.className = "message" + (kind ? " " + kind : "");
  if (kind === "bad" && message && w.doc_troubleshoot_link) {  // the troubleshooter may find what stopped it
    const doc = el("button", { type: "button", className: "link", textContent: w.doc_troubleshoot_link });
    doc.addEventListener("click", openDoctor);
    node.append(" ", doc);
  }
  if (kind === "bad" && message && w.report) {  // a problem can go straight into a bug report (the player posts it)
    const report = el("button", { type: "button", className: "link", textContent: w.report, title: w.tip_report || "" });
    report.addEventListener("click", () => api().report_problem(message).catch(() => {}));
    node.append(" ", report);
  }
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
  text($("doc-open"), w.doc_button);
  text($("doc-title"), w.doc_title);
  text($("doc-intro"), w.doc_intro);
  text($("doc-again"), w.doc_again);
  text($("doc-copy"), w.doc_copy);
  text($("doc-close"), w.doc_close);
  text($("help"), w.help);
  $("help").title = w.tip_help;
  text($("report"), w.report_problem);
  $("report").title = w.tip_report_problem;
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
  $("welcome-view").classList.add("hidden");
  if (state.welcome) renderWelcome();
  else if (state.settings) renderSettings();
  else if (state.browse) renderBrowse(); else if (state.importing) renderImport(); else if (state.editing) renderEditor();
  else renderActive();
  if (state.doctor) renderDoctor();  // its words, and its fixes on or off as Play starts and ends
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
  { id: "backup", render() { renderBackup(); } },  // loaded when Settings opens (loadBackup)
  { id: "updates", render() {
    const w = state.words, u = state.update || {};
    text($("set-updates-text"), u.checking ? w.set_updates_checking : u.available ? fill(w.update_out, { app: APP_NAME, version: u.version })
      : u.error ? u.error : fill(w.set_updates_latest, { version: u.version || "" }));
    text($("set-updates-check"), w.set_updates_check);
  } },
];

// --- the clean game backup (rusemod.backup through api.backup_*): made while the game is clean, then a check of the
// game's files against it, and a restore of what other mod managers or hand edits changed. The only way the launcher
// writes into the game's own folder, and only after the player says yes. Its jobs' lines are their progress ("37%";
// a restore checks first: "check 37%"), and a finished job brings what it found or did as its "result" ---
const BACKUP_LIST = 40;  // file names shown per kind (changed, missing, added); the rest are counted

function backupState() {
  return state.backup || (state.backup = { status: null, busy: "", phase: "", pct: "", found: null, note: "", noteKind: "",
    asking: false });
}

function errorText(err) {
  return (err && err.message) || String(err);
}

async function loadBackup() {
  const b = backupState();
  try { b.status = await api().backup_status(); } catch (err) { Object.assign(b, { note: errorText(err), noteKind: "bad" }); }
  if (state.settings) renderBackup();
}

function renderBackup() {
  const w = state.words, b = backupState(), s = b.status;
  text($("set-backup-help"), w.set_backup_help);
  let line = "";
  if (s && !s.found) line = w.set_game_none;
  else if (s && s.current) line = fill(w.backup_have, { build: s.current.build || "?", date: s.current.date, size: s.current.size_gb, path: s.current.path });
  else if (s && s.backups.length) line = fill(w.backup_other, { build: s.backups[0].build || "?", date: s.backups[0].date, now: s.build || "?" });
  else if (s) line = fill(w.backup_none, { need: s.need_gb, free: s.free_gb === null ? "?" : s.free_gb, drive: s.drive });
  text($("backup-status"), line);
  $("backup-status").className = s && s.current ? "good" : s && s.found && !s.enough ? "bad" : "muted";
  const found = Boolean(s && s.found), ready = found && !b.busy && !b.asking, current = Boolean(s && s.current);
  text($("backup-make"), current ? w.backup_make_again : w.backup_make);
  text($("backup-check"), w.backup_check);
  text($("backup-restore"), w.backup_restore);
  text($("backup-verify"), w.backup_verify);
  $("backup-verify").title = w.backup_verify_tip;
  text($("backup-deep-label"), w.backup_deep);
  $("backup-make").disabled = !ready;
  $("backup-check").disabled = !ready || !current;
  $("backup-restore").disabled = !ready || !current || state.playing;  // a Play's copy is built from the game's files
  $("backup-verify").disabled = !found || b.busy === "restore";
  $("backup-deep").disabled = Boolean(b.busy);
  const progress = { make: w.backup_making, check: w.backup_checking, restore: w.backup_restoring }[b.phase || b.busy];
  const note = $("backup-note");
  text(note, b.busy ? fill(progress, { pct: b.pct }) : b.note);
  note.className = "message" + (!b.busy && b.noteKind ? " " + b.noteKind : "");
  note.classList.toggle("hidden", !note.textContent);
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
  const yes = el("button", { type: "button", className: "small danger", textContent: yesText });
  const no = el("button", { type: "button", className: "small ghost", textContent: w.cancel });
  const close = () => { b.asking = false; $("backup-ask").replaceChildren(); renderBackup(); };
  yes.addEventListener("click", () => { close(); onYes(); });
  no.addEventListener("click", close);
  b.asking = true;
  $("backup-ask").replaceChildren(el("div", { className: "confirm" }, el("span", { textContent: question }), yes, no));
  renderBackup();
  yes.focus();
}

// Runs one backup job and follows it; resolves with its result, or null when it failed (its message is the note)
async function runBackup(kind, call) {
  const b = backupState();
  Object.assign(b, { busy: kind, phase: "", pct: "", note: "", noteKind: "" });
  renderBackup();
  let job;
  try { ({ job } = await call()); } catch (err) {
    Object.assign(b, { busy: "", note: errorText(err), noteKind: "bad" });
    renderBackup();
    return null;
  }
  return new Promise((done) => {
    let seen = 0;
    const tick = async () => {
      let j;
      try { j = await api().job(job, seen); } catch (err) {
        Object.assign(b, { busy: "", note: errorText(err), noteKind: "bad" });
        renderBackup();
        done(null);
        return;
      }
      seen = j.count;
      const last = j.lines[j.lines.length - 1];
      if (last) Object.assign(b, { phase: last.startsWith("check ") ? "check" : kind, pct: last.replace(/^check /, "") });
      if (j.state === "running") { if (state.settings) renderBackup(); setTimeout(tick, 400); return; }
      Object.assign(b, { busy: "", phase: "" });
      if (j.state !== "done") Object.assign(b, { note: j.message, noteKind: "bad" });
      render();  // Play waits for a restore: on again
      done(j.state === "done" ? j.result || {} : null);
    };
    tick();
  });
}

async function makeBackup() {
  const w = state.words, s = backupState().status;
  const go = async (replace) => {
    const res = await runBackup("make", () => api().backup_make(replace));
    if (res) Object.assign(backupState(), { found: null, note: fill(w.backup_made, { files: res.files, size: res.size_gb }), noteKind: "good" });
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
    Object.assign(b, { found: res, note: n ? fill(w.backup_differs, { n }) : w.backup_clean, noteKind: n ? "bad" : "good" });
  }
  renderBackup();
  return res;
}

// Restore: the game is checked first, and the player sees what will change before saying yes
async function restoreBackup() {
  const w = state.words, b = backupState();
  const found = await checkBackup();
  if (!found) return;
  const n = found.changed.length + found.missing.length, m = found.added.length;
  if (!n && !m) {
    Object.assign(b, { note: w.backup_nothing, noteKind: "good" });
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
      Object.assign(b, { found: null, note: said.join(" "), noteKind: res.left.length ? "bad" : "good" });
    }
    await loadBackup();
  });
}

async function verifyWithSteam() {
  const b = backupState();
  try {
    await api().steam_verify();
    Object.assign(b, { note: state.words.backup_verify_opened, noteKind: "good" });
  } catch (err) { Object.assign(b, { note: errorText(err), noteKind: "bad" }); }
  renderBackup();
}

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
  play.disabled = state.playing || Boolean(set.error) || Boolean(check && check.hard.length)
    || backupState().busy === "restore";  // a copy built now would take half-restored files
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

// --- Supported mods: the mod index (MOD_FORMAT §15). Tick the mods, then one Install downloads them one after
// another, each checked against the list. A mod tagged "cheat" is in its own group, "Cheats and test tools
// (optional)", never ticked for the player: only ticked mods are downloaded. ---
function emptyList() {
  return { mods: [], source: "", as_of: "", message: "", search: "", page: "", ticked: new Set(), installing: false,
    note: "", noteKind: "" };
}

async function openBrowse(fresh) {
  state.settings = false;
  state.editing = null;
  state.importing = null;
  state.browse = state.browse || emptyList();
  state.browse.loading = true;
  render();
  try {
    const res = await api().browse(state.browse.search, Boolean(fresh));
    Object.assign(state.browse, res, { loading: false });
  } catch (err) { state.browse.loading = false; problem(err); }
  render();
}

// what the list says about itself: the copy from before (offline), no list at all, or nothing matching
function listNote(node, view, offlineExtra) {
  const w = state.words;
  if (view.loading && !view.mods.length) text(node, w.loading_list);
  else if (view.source === "cache") text(node, fill(w.offline_note, { date: view.as_of }));
  else if (view.source === "none") {  // the launcher's message is a whole sentence already ("The mod list couldn't…")
    text(node, (/^(The|No) /.test(view.message || "") ? view.message : fill(w.list_failed, { why: view.message }))
      + (offlineExtra ? " " + offlineExtra : ""));
  }
  else if (!view.loading && !view.mods.length) text(node, w.list_empty);
  else text(node, "");
  node.classList.toggle("hidden", !node.textContent);
}

// the mods with their tick boxes: the supported ones, then the cheats and test tools under their own heading
function renderPickList(holder, view) {
  const w = state.words;
  const card = (mod) => {
    const meta = [mod.version ? fill(w.version_v, { v: mod.version }) : "", mod.author ? fill(w.by, { authors: mod.author }) : "",
      mod.size_text, mod.game_build ? fill(w.for_build, { build: mod.game_build }) : ""].filter(Boolean).join(" · ");
    const have = mod.state === "installed";
    const ticked = !have && view.ticked.has(mod.id);
    const box = el("input", { type: "checkbox", checked: have || ticked,  // one in the library: ticked, greyed out
      disabled: have || view.installing || state.playing });
    box.setAttribute("aria-label", mod.name);
    const li = el("li", { className: "mod-card browse-card tickable" + (ticked ? " ticked" : "") }, box,
      el("span", { className: "name", textContent: mod.name }),
      el("span", { className: "state", textContent: have ? w.installed
        : mod.state === "update" ? fill(w.update_to, { v: mod.version }) : "" }),
      el("span", { className: "meta", textContent: meta }));
    if (mod.description) li.append(el("span", { className: "desc", textContent: mod.description }));
    if (mod.tags && mod.tags.length) li.append(el("span", { className: "tags", textContent: mod.tags.join(" · ") }));
    if (mod.homepage) {
      const link = el("button", { type: "button", className: "link", textContent: w.more_info });
      link.addEventListener("click", (e) => { e.stopPropagation(); api().open_link(mod.homepage).catch(problem); });
      li.append(link);
    }
    const toggle = (on) => {
      if (on) view.ticked.add(mod.id); else view.ticked.delete(mod.id);
      render();
    };
    box.addEventListener("change", () => toggle(box.checked));
    li.addEventListener("click", (e) => { if (e.target === li || (e.target.tagName === "SPAN")) { if (!box.disabled) toggle(!box.checked); } });
    return li;
  };
  const main = view.mods.filter((m) => !m.cheat), cheats = view.mods.filter((m) => m.cheat);
  const parts = [el("ul", { className: "browse-list" }, ...main.map(card))];
  if (cheats.length) {
    parts.push(el("h2", { className: "browse-group", textContent: w.cheats_group }),
      el("p", { className: "muted", textContent: w.cheats_help }),
      el("ul", { className: "browse-list" }, ...cheats.map(card)));
  }
  holder.replaceChildren(...parts);
}

// the ticked mods that are still to install (one installed meanwhile is left out)
function toInstall(view) {
  return view.mods.filter((m) => view.ticked.has(m.id) && m.state !== "installed").map((m) => m.id);
}

function listMessage(node, view) {
  text(node, view.note);
  node.className = "message" + (view.noteKind ? " " + view.noteKind : "");
}

function renderBrowse() {
  const w = state.words;
  const b = state.browse;
  $("set-view").classList.add("hidden");
  $("editor").classList.add("hidden");
  $("import-view").classList.add("hidden");
  $("browse-view").classList.remove("hidden");
  if ($("browse-search").value !== b.search) $("browse-search").value = b.search;
  text($("browse-page"), w.see_list);
  listNote($("browse-note"), b);
  renderPickList($("browse-list"), b);
  const n = toInstall(b).length;
  text($("browse-install"), b.installing ? w.installing : fill(w.install_ticked, { n }));
  $("browse-install").disabled = !n || b.installing || state.playing;
  listMessage($("browse-message"), b);
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

// Install the ticked mods of a list (the Supported mods tab's, or the first run's): one job, each mod checked
async function installTicked(view, onEnd) {
  const ids = toInstall(view);
  if (!ids.length) return;
  Object.assign(view, { installing: true, note: state.words.installing, noteKind: "" });
  render();
  let job;
  try { ({ job } = await api().install_mods(ids)); }
  catch (err) { Object.assign(view, { installing: false, note: err.message, noteKind: "bad" }); render(); return; }
  followJob(job, async (j) => {
    try {
      useLists({ sets: await api().mod_sets(), library: await api().library() });  // some may be in even if one failed
      Object.assign(view, await api().browse(view.search || "", false));
    } catch (err) { problem(err); }
    for (const m of view.mods) if (m.state === "installed") view.ticked.delete(m.id);
    Object.assign(view, { installing: false, note: j.message, noteKind: j.state === "done" ? "good" : "bad" });
    if (onEnd) onEnd(j); else render();
  });
}

// --- the first run: "Choose your mods" while the library is empty and the player hasn't chosen yet. Everything in
// the list is ticked except the cheats and test tools; offline it's the copy from before, or only Skip ---
async function openWelcome() {
  let show = false;
  try { show = (await api().first_run()).show; } catch { return; }  // an older launcher: no first run
  if (!show) return;
  state.welcome = Object.assign(emptyList(), { loading: true });
  render();
  try {
    Object.assign(state.welcome, await api().browse("", false), { loading: false });
  } catch (err) { Object.assign(state.welcome, { loading: false, source: "none", message: (err && err.message) || String(err) }); }
  state.welcome.ticked = new Set(state.welcome.mods.filter((m) => !m.cheat && m.state !== "installed").map((m) => m.id));
  render();
}

async function closeWelcome(message, kind) {
  try { await api().first_run_done(); } catch { /* shown again next time: harmless */ }
  state.welcome = null;
  render();
  if (message) setMessage(message, kind);
}

function renderWelcome() {
  const w = state.words, v = state.welcome;
  for (const id of ["set-view", "editor", "import-view", "browse-view", "settings-view"]) $(id).classList.add("hidden");
  $("welcome-view").classList.remove("hidden");
  text($("welcome-title"), w.welcome_title);
  text($("welcome-help"), v.source === "none" ? "" : w.welcome_help);  // no list: only why, and Skip
  text($("welcome-page"), w.see_list);
  listNote($("welcome-note"), v, w.welcome_offline);
  renderPickList($("welcome-list"), v);
  const n = toInstall(v).length;
  text($("welcome-install"), v.installing ? w.installing : fill(w.install_ticked, { n }));
  $("welcome-install").disabled = !n || v.installing || v.loading;
  $("welcome-install").classList.toggle("hidden", v.source === "none");
  text($("welcome-skip"), w.welcome_skip);
  $("welcome-skip").disabled = Boolean(v.installing);
  listMessage($("welcome-message"), v);
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

// The library: one compact row per mod (its name, its version and sets; a mistake in red), so a long library fits;
// a row opens on a click to its description, the builds it was made for and Remove. The search box narrows it.
const libraryOpen = new Set();  // the ids of the rows opened

function renderLibrary() {
  const w = state.words, all = state.library;
  const q = ($("library-search").value || "").trim().toLowerCase();
  const shown = q ? all.filter((m) => `${m.name} ${m.description || ""} ${m.author || ""}`.toLowerCase().includes(q)) : all;
  $("library-empty").classList.toggle("hidden", all.length > 0 && shown.length > 0);
  text($("library-empty"), all.length ? fill(w.library_no_match, { q }) : w.library_empty);
  $("library-search").classList.toggle("hidden", all.length < 8);  // a short library needs no search
  $("library-search").placeholder = w.library_search;
  text($("library-count"), all.length ? fill(w.library_count, { n: all.length }) : "");
  $("drop-hint").classList.toggle("hidden", all.length > 0);  // the empty library's words say it already
  $("mod-list").replaceChildren(...shown.map((mod) => {
    const meta = [mod.version ? fill(w.version_v, { v: mod.version }) : "",
      mod.used_in ? (mod.used_in === 1 ? w.used_in_one : fill(w.used_in, { n: mod.used_in })) : ""].filter(Boolean).join(" · ");
    const open = libraryOpen.has(mod.id);
    const sum = el("button", { type: "button", className: "lib-sum", title: mod.description || mod.name },
      el("span", { className: "name", textContent: mod.name }),
      el("span", { className: "meta", textContent: meta }));
    sum.setAttribute("aria-expanded", String(open));
    const li = el("li", { className: "mod-card lib-row" + (open ? " open" : "") + (mod.error ? " bad" : "") }, sum);
    sum.addEventListener("click", () => {
      if (libraryOpen.has(mod.id)) libraryOpen.delete(mod.id); else libraryOpen.add(mod.id);
      renderLibrary();
    });
    if (mod.error && !open) li.append(el("div", { className: "lib-more" }, el("span", { className: "warn", textContent: w.has_mistake })));
    if (!open) return li;
    const more = el("div", { className: "lib-more" });
    if (mod.author) more.append(el("span", { className: "meta", textContent: fill(w.by, { authors: mod.author }) }));
    if (mod.description) more.append(el("span", { className: "meta", textContent: mod.description }));
    const note = buildNote(mod);
    if (note) more.append(el("span", { className: "meta", textContent: note }));
    if (mod.error) more.append(el("span", { className: "warn", textContent: `${w.has_mistake}: ${mod.error}` }));
    const remove = el("button", { type: "button", className: "small ghost danger", textContent: w.remove, disabled: state.playing });
    remove.addEventListener("click", () => {
      remove.disabled = true;
      confirmRow(fill(w.really_remove_mod, { name: mod.name }), w.remove, async () => {
        libraryOpen.delete(mod.id);
        useLists(await api().remove_mod(mod.id));
        setMessage(fill(w.mod_removed, { name: mod.name }), "good");
      }, more, remove);
    });
    more.append(remove);
    li.append(more);
    return li;
  }));
  $("add-mod").disabled = state.playing;
}

function added(res) {
  const w = state.words;
  useLists(res);
  if (!res.mod) return;
  const done = res.replaced ? fill(w.mod_updated, { name: res.mod.name, v: res.mod.version }) : fill(w.mod_added, { name: res.mod.name });
  const problems = res.problems || [];  // the mod check: said now rather than when Play stops
  if (problems.length) setMessage(`${done} ${fill(w.mod_check_warn, { n: problems.length })} ${problems.map((p) => p.problem).join(" · ")}`, "bad");
  else setMessage(done, "good");
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

// --- the troubleshooter (rusemod.doctor through api.troubleshoot): what can stop Play, checked in one go. Each
// finding's sentence is its "say" word filled with its data; a fix the launcher can run has a button ---
const DOC_SIGNS = { ok: "✔\uFE0E", info: "ℹ\uFE0E", warn: "⚠\uFE0E", fail: "✖\uFE0E" };  // \uFE0E: a sign, not an emoji

function openDoctor() {
  if (!$("doc").open) $("doc").showModal();
  checkDoctor();
}

// note: what the last fix did, kept on screen while everything is checked again
async function checkDoctor(note, kind) {
  const run = (state.doctorRun || 0) + 1;
  state.doctorRun = run;  // only the latest check is shown
  const d = state.doctor = { busy: true, findings: state.doctor ? state.doctor.findings : [], report: "",
    note: note || "", noteKind: kind || "" };
  $("doc-report").classList.add("hidden");
  renderDoctor();
  try {
    Object.assign(d, await api().troubleshoot());
  } catch (err) {
    Object.assign(d, { note: (err && err.message) || String(err), noteKind: "bad" });
  }
  if (run !== state.doctorRun) return;
  d.busy = false;
  renderDoctor();
}

function renderDoctor() {
  const w = state.words, d = state.doctor;
  const list = $("doc-list");
  list.classList.toggle("busy", d.busy);
  list.replaceChildren(...d.findings.map((f) => {
    const li = el("li", { className: "doc-item " + f.level },
      el("span", { className: "sign", textContent: DOC_SIGNS[f.level] || "•" }),
      el("span", { className: "say", textContent: fill(w[f.say] || f.say, f.data) }));
    if (f.fix) {  // while Play builds a copy, its folder would look like a leftover: only the game folder can change
      const fix = el("button", { type: "button", className: "small", textContent: w["doc_fix_" + f.fix] || f.fix,
        disabled: d.busy || (state.playing && f.fix !== "choose_game") });
      fix.addEventListener("click", () => fixDoctor(f.fix));
      li.append(fix);
    }
    return li;
  }));
  const note = $("doc-note");
  text(note, [d.note, d.busy ? w.doc_checking : ""].filter(Boolean).join(" "));
  note.className = "message" + (d.note && d.noteKind ? " " + d.noteKind : "");
  $("doc-again").disabled = d.busy;
  $("doc-copy").disabled = d.busy || !d.report;
}

async function fixDoctor(action) {
  const w = state.words;
  state.doctor.busy = true;
  renderDoctor();
  if (action === "choose_game") {  // the launcher's own Choose folder…, as in the header
    try {
      const status = await api().choose_game_folder();
      renderStatus(status);
      await refresh();
      return checkDoctor(status.found ? "" : status.message, "bad");
    } catch (err) { return checkDoctor((err && err.message) || String(err), "bad"); }
  }
  try {
    const res = await api().troubleshoot_fix(action);
    const said = [];
    if (res.done || !res.left.length) said.push(fill(w.doc_fixed, { done: res.done }));
    if (res.left.length) said.push(fill(w.doc_fix_left, { left: res.left.join("; ") }));
    return checkDoctor(said.join(" "), res.left.length ? "bad" : "good");
  } catch (err) { return checkDoctor((err && err.message) || String(err), "bad"); }
}

async function copyDoctorReport() {
  const d = state.doctor, area = $("doc-report");
  try {
    await navigator.clipboard.writeText(d.report);
    area.classList.add("hidden");
    Object.assign(d, { note: state.words.doc_copied, noteKind: "good" });
  } catch {  // no clipboard access here: the report is shown, selected, so Ctrl+C copies it
    area.value = d.report;
    area.classList.remove("hidden");
    area.focus();
    area.select();
    Object.assign(d, { note: "", noteKind: "" });
  }
  renderDoctor();
}

async function start() {
  state.languages = await api().languages();
  state.lang = (await loadLang()) || await api().default_language();
  if (!state.languages.some((l) => l.code === state.lang)) state.lang = "us";
  $("lang").addEventListener("change", (e) => setLanguage(e.target.value).catch(problem));
  $("settings-open").addEventListener("click", () => { state.settings = true; render(); loadBackup(); });
  $("backup-make").addEventListener("click", makeBackup);
  $("backup-check").addEventListener("click", checkBackup);
  $("backup-restore").addEventListener("click", restoreBackup);
  $("backup-verify").addEventListener("click", verifyWithSteam);
  $("settings-back").addEventListener("click", () => { state.settings = false; render(); });
  $("set-game-change").addEventListener("click", async () => {
    try { renderStatus(await api().choose_game_folder()); await refresh(); } catch (err) { problem(err); }
    if (state.settings) { renderSettings(); loadBackup(); }  // another game folder: its own backups
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
  $("browse").addEventListener("click", () => { state.welcome = null; openBrowse(true); });
  $("browse-install").addEventListener("click", () => state.browse && installTicked(state.browse));
  for (const id of ["browse-page", "welcome-page"]) $(id).addEventListener("click", () => api().open_help("mods").catch(problem));
  $("welcome-install").addEventListener("click", () => state.welcome && installTicked(state.welcome,
    (j) => closeWelcome(j.message, j.state === "done" ? "good" : "bad")));
  $("welcome-skip").addEventListener("click", () => closeWelcome());
  $("doc-open").addEventListener("click", openDoctor);
  $("doc-again").addEventListener("click", () => checkDoctor());
  $("doc-copy").addEventListener("click", copyDoctorReport);
  $("doc-close").addEventListener("click", () => $("doc").close());
  $("help").addEventListener("click", () => api().open_help("wiki").catch(problem));
  $("report").addEventListener("click", () => api().report_problem("").catch(problem));
  $("browse-refresh").addEventListener("click", () => openBrowse(true));
  $("browse-back").addEventListener("click", () => { state.browse = null; render(); });
  let searching = null;
  $("library-search").addEventListener("input", renderLibrary);
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
    if (!state.playing && !state.editing && !state.browse && !state.importing && !state.welcome) refresh();  // changed while away
    if (state.settings && !backupState().busy) loadBackup();  // a backup made or removed in the other app
  });
  watchDrops();
  $("update-now").addEventListener("click", installUpdate);
  $("update-info").addEventListener("click", () => api().update_page().catch(() => {}));
  await setLanguage(state.lang);
  await refresh();
  checkUpdate();
  await firstBackup();
  openWelcome();  // the first run: "Choose your mods"
}

// The installer's "Keep a clean copy of my game's files" (rusemod.backup.BackupCalls.backup_requested): made on this
// start, in Settings, where its help says why; the first run's "Choose your mods" opens over it as it runs
async function firstBackup() {
  let ask;
  try { ask = await api().backup_requested(); } catch { return; }  // an older back end
  if (!ask || !ask.make) return;
  state.settings = true;
  render();
  await loadBackup();
  makeBackup();
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
