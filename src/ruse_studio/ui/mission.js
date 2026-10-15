// The Scenario side's Mission, Goals, Events and Camera moves trays (StudioApi.mission / mission_save /
// mission_delete / mission_unit, rusemod.mission): a new Operation's or campaign chapter's own mission, kept in the
// map project's maps/<map>/mission.toml (the owner's design, 2026-10-09: "the actual unit commands, spawning the
// units, choosing the sides, the camera angles"; events When -> Do; all on the same map screen). The page holds the
// mission as the file's own table and saves it whole after each change; the Studio checks it with the build's own
// checks, so what it lists is what Test in game will say. maps.js opens it (window.MissionView), draws the camera
// moves on the map and hands it the map's clicks while Camera moves is open. Uses app.js's el and fill.
(function () {
  "use strict";
  const MS = { api: null, words: {}, lang: "base", pack: null, data: null, draft: null, tool: null, busy: false,
    error: "", box: null, units: [], nationNames: [], open: new Set(), onChange: null, cam: 0, height: 120,
    looking: false };
  const W = () => MS.words;
  const NATIONS = ["US", "Germany", "UK", "France", "Italy", "USSR", "Japan"];  // the game's nation numbers 0..6
  const OTHER_LANGS = ["fr", "ger", "ita", "spa", "pol", "ru", "cz", "jpn", "sc"];
  const LANG_NAMES = { fr: "Français", ger: "Deutsch", ita: "Italiano", spa: "Español", pol: "Polski", ru: "Русский",
    cz: "Čeština", jpn: "日本語", sc: "中文" };
  const WHEN = ["start", "time", "zone", "destroyed", "goal"];
  const DONE = ["zone", "destroyed", "time", "event"];
  const ACTIONS = ["message", "spawn", "move", "attack", "hold", "artillery", "bombing", "paradrop", "camera", "money",
    "goal", "complete", "victory", "defeat", "wait", "ai"];
  const METRE = 260;

  const copy = (x) => JSON.parse(JSON.stringify(x));
  const list = (k) => (MS.draft[k] = MS.draft[k] || []);

  // --- small controls, each with its tooltip ---
  function select(options, current, onChange, tip, label) {
    const s = el("select", { className: "small", title: tip || "" });
    if (label) s.setAttribute("aria-label", label);
    for (const [value, text] of options) s.append(el("option", { value: String(value), textContent: text }));
    s.value = current === undefined || current === null ? "" : String(current);
    s.addEventListener("change", () => onChange(s.value));
    return s;
  }

  function number(value, least, most, step, onChange, tip, label) {
    const n = el("input", { type: "number", className: "small ms-number", min: String(least), max: String(most),
      step: String(step), value: value === undefined || value === null ? "" : String(value), title: tip || "" });
    if (label) n.setAttribute("aria-label", label);
    n.addEventListener("change", () => {
      const v = n.value === "" ? null : Number(n.value);
      if (v !== null && (!Number.isFinite(v) || v < least || v > most)) { n.value = value ?? ""; return; }
      onChange(v);
    });
    return n;
  }

  function text(value, placeholder, onChange, tip, label) {
    const t = el("input", { type: "text", className: "small ms-text", value: value || "", placeholder: placeholder || "",
      title: tip || "", maxLength: 2000 });
    if (label) t.setAttribute("aria-label", label);
    t.addEventListener("change", () => onChange(t.value.trim()));
    t.addEventListener("keydown", (e) => e.stopPropagation());  // typing never moves the map
    return t;
  }

  function chips(options, current, onChange, tip) {
    return el("div", { className: "chips" }, ...options.map(([value, label]) => {
      const c = el("button", { type: "button", className: "chip", textContent: label, title: tip || "" });
      c.setAttribute("aria-pressed", String(value === current));
      c.addEventListener("click", () => { if (value !== current) onChange(value); });
      return c;
    }));
  }

  function row(label, ...controls) {
    return el("label", { className: "ms-row small" }, el("span", { className: "ms-label", textContent: label }), ...controls);
  }

  function linkButton(textContent, title, onClick, danger) {
    const b = el("button", { type: "button", className: "link" + (danger ? " danger" : ""), textContent, title });
    b.addEventListener("click", onClick);
    return b;
  }

  // A text in English and, behind "Other languages", the game's nine others (left empty: the English shows)
  function words(value, placeholder, onChange, tip, key) {
    const v = typeof value === "string" ? { us: value } : { ...(value || {}) };
    const put = () => {
      const more = Object.fromEntries(Object.entries(v).filter(([k, t]) => k !== "us" && t));
      onChange(Object.keys(more).length ? { us: v.us || "", ...more } : (v.us || ""));
    };
    const main = text(v.us, placeholder, (t) => { v.us = t; put(); }, tip, W().ms_lang_us);
    const toggle = linkButton(W().ms_more_langs, W().tip_ms_more_langs, () => {
      if (MS.open.has(key)) MS.open.delete(key); else MS.open.add(key);
      render();
    });
    const box = el("div", { className: "ms-words" }, main, toggle);
    if (MS.open.has(key)) {
      box.append(el("div", { className: "ms-langs" }, ...OTHER_LANGS.map((lang) => row(LANG_NAMES[lang],
        text(v[lang], v.us, (t) => { v[lang] = t; put(); }, W().tip_ms_lang, LANG_NAMES[lang])))));
    }
    return box;
  }

  // --- the map's names the mission can use ---
  const points = () => (MS.data.points || []).map((p) => [p, p]);
  const zones = () => (MS.data.zones || []).map((z) => [z, z]);
  const pick = (opts) => [["", W().ms_pick], ...opts];

  function groupInput(value, onChange, tip) {
    const id = "ms-groups";
    let dl = document.getElementById(id);
    if (!dl) { dl = el("datalist", { id }); document.body.append(dl); }
    dl.replaceChildren(...(MS.data.groups || []).map((g) => el("option", { value: g })));
    const t = text(value, W().ms_group_hint, (v) => onChange(v.replace(/[^A-Za-z0-9_]/g, "_").replace(/^([^A-Za-z])/, "g$1")), tip,
      W().ms_group);
    t.setAttribute("list", id);
    return t;
  }

  function sideName(s) {
    const w = W(), nation = s.nation ? MS.nationNames[NATIONS.indexOf(s.nation)] || s.nation : "";
    return `${fill(w.ms_side_n, { n: s.number })} · ${s.player ? w.ms_side_you : w.ms_side_cpu}${nation ? " · " + nation : ""}`
      + (s.team ? ` · ${fill(w.ms_team_n, { n: s.team })}` : "");
  }

  function sideSelect(value, onChange, tip, withNone) {
    const opts = (MS.data.sides || []).map((s) => [s.number, sideName(s)]);
    return select(withNone ? [["", W().ms_side_player], ...opts] : opts, value, (v) => onChange(v === "" ? null : Number(v)),
      tip, W().ms_side);
  }

  function unitName(cls) {
    const address = (MS.data.units || {})[cls];
    const u = address && MS.units.find((x) => x.address === address);
    return u ? u.name : cls;
  }

  function freeId(prefix, used) {
    let n = 1;
    while (used.has(prefix + n)) n += 1;
    return prefix + n;
  }

  // --- saving ---
  async function save() {
    MS.busy = true;
    MS.error = "";
    render();
    try {
      MS.data = await MS.api.mission_save(MS.pack, MS.draft);
      MS.draft = copy(MS.data.mission);
    } catch (err) {
      MS.error = (err && err.message) || String(err);
    }
    MS.busy = false;
    render();
    if (MS.onChange) MS.onChange();
  }

  function change(fn) {
    return (...args) => { fn(...args); save(); };
  }

  // --- the trays ---
  function head() {
    const w = W(), d = MS.data, out = [];
    if (!d) return [el("div", { className: "muted small", textContent: w.ms_loading })];
    if (!d.allowed) return [el("div", { className: "small", textContent: w[d.why] || d.why })];
    if (!d.exists) {
      const b = el("button", { type: "button", className: "ghost small", textContent: w.ms_start, title: w.tip_ms_start });
      b.addEventListener("click", () => save());
      out.push(el("div", { className: "small ms-note" }, el("span", { textContent: w.ms_none + " " }), b));
    }
    return out;
  }

  function problems() {
    const w = W(), d = MS.data;
    const rows = (d.problems || []).map(([level, msg]) => el("div", { className: level === "error" ? "error-text" : "muted",
      textContent: msg }));
    const box = el("div", { className: "ms-problems small" }, el("div", { className: "ms-head", textContent: w.ms_problems }));
    if (MS.error) box.append(el("div", { className: "error-text", textContent: MS.error }));
    box.append(...(rows.length ? rows : [el("div", { className: "muted", textContent: w.ms_ok })]));
    if (MS.busy) box.append(el("div", { className: "muted", textContent: w.ms_saving }));
    return box;
  }

  function renderMission() {
    const w = W(), m = MS.draft.mission = MS.draft.mission || {};
    const out = [];
    const t = m.time_limit || 0;
    out.push(row(t ? fill(w.ms_time, { n: t }) : w.ms_time_none,
      number(t, 0, 600, 1, change((v) => { m.time_limit = v || 0; }), w.tip_ms_time, w.ms_time_label)));
    if (t) {
      out.push(row(w.ms_time_up, chips([["defeat", w.ms_up_defeat], ["victory", w.ms_up_victory], ["nothing", w.ms_up_nothing]],
        m.time_up || "defeat", change((v) => { m.time_up = v; }), w.tip_ms_time_up)));
    }
    out.push(row(w.ms_win, chips([["main_goals", w.ms_win_main], ["events", w.ms_win_events]], m.win || "main_goals",
      change((v) => { m.win = v; }), w.tip_ms_win)));
    const cams = [["", w.ms_opening_none], ...(MS.data.cameras || []).map((c) => [c, fill(w.ms_opening_map, { name: c })]),
      ...list("camera").map((c) => [c.name, c.name])];
    out.push(row(w.ms_opening, select(cams, m.opening || "", change((v) => { if (v) m.opening = v; else delete m.opening; }),
      w.tip_ms_opening, w.ms_opening)));
    out.push(el("div", { className: "ms-head small", textContent: w.ms_sides, title: w.tip_ms_sides }));
    const sides = list("side");
    for (const info of MS.data.sides || []) {
      let s = sides.find((x) => x.number === info.number);
      if (!s) { s = { number: info.number }; sides.push(s); }
      const set = (k, v) => change(() => { if (v === null || v === "") delete s[k]; else s[k] = v; })();
      const controls = [
        select([["", w.ms_nation_same], ...NATIONS.map((n, i) => [n, MS.nationNames[i] || n])], s.nation || "",
          (v) => set("nation", v), w.tip_ms_nation, w.ms_nation),
        select([["", w.ms_diff_same], ["easy", w.ms_diff_easy], ["normal", w.ms_diff_normal], ["hard", w.ms_diff_hard]],
          s.difficulty || "", (v) => set("difficulty", v), w.tip_ms_difficulty, w.ms_difficulty),
      ];
      if (!info.player) {
        controls.push(select([["script", w.ms_plays_script], ["ai", w.ms_plays_ai]], s.plays || "script",
          (v) => set("plays", v === "script" ? null : v), w.tip_ms_plays, w.ms_plays));
      }
      const money = number(s.money ?? null, 0, 1e9, 50, (v) => set("money", v), w.tip_ms_money, w.ms_money);
      money.placeholder = w.ms_amount;
      controls.push(money);
      out.push(el("div", { className: "ms-side small" }, el("span", { className: "ms-label", textContent: sideName(info) }),
        ...controls));
    }
    if (MS.data.exists) {
      out.push(el("div", { className: "small" }, linkButton(w.ms_remove, w.tip_ms_remove, async () => {
        MS.data = await MS.api.mission_delete(MS.pack);
        MS.draft = copy(MS.data.mission);
        render();
        if (MS.onChange) MS.onChange();
      }, true)));
    }
    return out;
  }

  function goalCard(g, i) {
    const w = W(), goals = list("goal");
    const done = g.done || "zone";
    const card = el("div", { className: "ms-card" });
    card.append(el("div", { className: "ms-card-head" },
      chips([[true, w.ms_goal_main], [false, w.ms_goal_bonus]], g.main !== false, change((v) => { g.main = v; }), w.tip_ms_goal_main),
      words(g.text, w.ms_goal_text, change((v) => { g.text = v; }), w.tip_ms_goal_text, "goal:" + g.id),
      linkButton(w.ms_delete, w.tip_ms_delete_goal, change(() => { goals.splice(i, 1); }), true)));
    card.append(row(w.ms_goal_done, select(DONE.map((k) => [k, w["ms_done_" + k]]), done, change((v) => {
      g.done = v;
      for (const k of ["zone", "group", "seconds"]) delete g[k];
      if (v === "time") g.seconds = 120;
      if (v === "zone") g.zone = (MS.data.zones || [])[0] || "";
      if (v === "destroyed") g.group = (MS.data.groups || [])[0] || "enemy";
    }), w.tip_ms_goal_done, w.ms_goal_done)));
    if (done === "zone") card.append(row(w.ms_zone, select(pick(zones()), g.zone, change((v) => { g.zone = v; }), w.tip_ms_zone, w.ms_zone)));
    if (done === "destroyed") card.append(row(w.ms_group, groupInput(g.group, change((v) => { g.group = v; }), w.tip_ms_goal_group)));
    if (done === "time") card.append(row(w.ms_seconds, number(g.seconds, 1, 36000, 5, change((v) => { g.seconds = v || 60; }), w.tip_ms_goal_seconds, w.ms_seconds)));
    card.append(row(w.ms_marker, select([["", w.ms_marker_none], ...points()], g.marker || "",
      change((v) => { if (v) g.marker = v; else delete g.marker; }), w.tip_ms_marker, w.ms_marker)));
    card.append(row(w.ms_goal_shows, chips([["start", w.ms_shows_start], ["event", w.ms_shows_event]], g.start || "start",
      change((v) => { if (v === "start") delete g.start; else g.start = v; }), w.tip_ms_goal_shows)));
    return card;
  }

  function renderGoals() {
    const w = W(), goals = list("goal");
    const add = el("button", { type: "button", className: "ghost small", textContent: w.ms_goal_add, title: w.tip_ms_goal_add });
    add.addEventListener("click", change(() => {
      const id = freeId("goal", new Set([...goals.map((g) => g.id), ...list("event").map((e) => e.id)]));
      goals.push({ id, text: w.ms_goal_new, main: true, done: "zone", zone: (MS.data.zones || [])[0] || "" });
    }));
    return [...(goals.length ? goals.map(goalCard) : [el("div", { className: "muted small", textContent: w.ms_goals_none })]), add];
  }

  function actionRow(a, k, acts) {
    const w = W(), parts = [];
    const set = (key) => change((v) => { if (v === null || v === "" || (Array.isArray(v) && !v.length)) delete a[key]; else a[key] = v; });
    const goals = list("goal");
    if (a.do === "message") parts.push(words(a.text, w.ms_message_hint, set("text"), w.tip_ms_message, `act:${k}:${acts.id}`));
    if (a.do === "spawn") {
      const unit = select([["", w.ms_unit_pick], ...MS.units.filter((u) => u.address !== "DalleBatimentDepot")
        .map((u) => [u.address, `${u.name}${u.nation_name ? " · " + u.nation_name : ""}`])],
      (Object.entries(MS.data.units || {}).find(([c]) => c === a.unit) || [])[1] || "", async (address) => {
        if (!address) return;
        try {
          const got = await MS.api.mission_unit(address);
          a.unit = got.class;
          MS.data.units = { ...(MS.data.units || {}), [got.class]: got.unit };
          save();
        } catch (err) { MS.error = (err && err.message) || String(err); render(); }
      }, w.tip_ms_unit, w.ms_unit);
      if (a.unit && !(MS.data.units || {})[a.unit]) unit.append(el("option", { value: "", textContent: a.unit, selected: true }));
      parts.push(unit, number(a.count || 1, 1, 50, 1, set("count"), w.tip_ms_count, w.ms_count),
        sideSelect(a.side, set("side"), w.tip_ms_spawn_side), select(pick(points()), a.at, set("at"), w.tip_ms_at, w.ms_at_point),
        groupInput(a.group, set("group"), w.tip_ms_spawn_group));
    }
    if (["move", "attack", "hold", "artillery", "bombing", "paradrop"].includes(a.do)) {
      parts.push(groupInput(a.group, set("group"), w["tip_ms_group_" + a.do]));
    }
    if (a.do === "move") {
      const to = a.to || [];
      to.forEach((t, j) => parts.push(select(pick(points()), t, change((v) => { if (v) to[j] = v; else to.splice(j, 1); a.to = to; }),
        w.tip_ms_to, w.ms_to)));
      parts.push(select([["", w.ms_to_add], ...points()], "", change((v) => { if (v) { to.push(v); a.to = to; } }), w.tip_ms_to, w.ms_to_add));
    }
    if (a.do === "attack") parts.push(groupInput(a.target, set("target"), w.tip_ms_target));
    if (a.do === "hold") parts.push(select(pick(zones()), a.zone, set("zone"), w.tip_ms_hold_zone, w.ms_zone));
    if (["artillery", "bombing", "paradrop"].includes(a.do)) parts.push(select(pick(points()), a.at, set("at"), w.tip_ms_at, w.ms_at_point));
    if (a.do === "camera") {
      const cams = [...(MS.data.cameras || []).map((c) => [c, fill(w.ms_opening_map, { name: c })]), ...list("camera").map((c) => [c.name, c.name])];
      parts.push(select(pick(cams), a.camera, set("camera"), w.tip_ms_camera, w.ms_camera),
        number(a.seconds ?? 15, 1, 600, 1, set("seconds"), w.tip_ms_cam_seconds, w.ms_seconds));
    }
    if (a.do === "money") parts.push(sideSelect(a.side ?? 0, set("side"), w.tip_ms_money_side),
      number(a.amount ?? 0, 0, 1e9, 50, set("amount"), w.tip_ms_amount, w.ms_amount));
    if (a.do === "goal") parts.push(select(pick(goals.filter((g) => g.start === "event").map((g) => [g.id, textOf(g.text)])), a.goal,
      set("goal"), w.tip_ms_do_goal, w.ms_goal));
    if (a.do === "complete") parts.push(select(pick(goals.filter((g) => g.done === "event").map((g) => [g.id, textOf(g.text)])), a.goal,
      set("goal"), w.tip_ms_do_complete, w.ms_goal));
    if (a.do === "wait") parts.push(number(a.seconds ?? 5, 0, 3600, 1, set("seconds"), w.tip_ms_wait_s, w.ms_seconds));
    if (a.do === "ai") parts.push(sideSelect(a.side, set("side"), w.tip_ms_ai_side));
    const list_ = acts.do;
    const tools = el("span", { className: "ms-tools" },
      linkButton("↑", w.tip_ms_up, change(() => { if (k > 0) [list_[k - 1], list_[k]] = [list_[k], list_[k - 1]]; })),
      linkButton("↓", w.tip_ms_down, change(() => { if (k < list_.length - 1) [list_[k + 1], list_[k]] = [list_[k], list_[k + 1]]; })),
      linkButton("✕", w.tip_ms_delete_action, change(() => { list_.splice(k, 1); }), true));
    return el("div", { className: "ms-action small", title: w["tip_ms_do_" + a.do] || "" },
      el("span", { className: "ms-label", textContent: `${k + 1}. ${w["ms_do_" + a.do] || a.do}` }), ...parts, tools);
  }

  const textOf = (t) => (typeof t === "string" ? t : (t && t.us) || "");

  function eventCard(e, i) {
    const w = W(), events = list("event"), when = e.when || "start";
    const card = el("div", { className: "ms-card" });
    card.append(el("div", { className: "ms-card-head" },
      el("span", { className: "ms-label", textContent: e.id }),
      select(WHEN.map((k) => [k, w["ms_when_" + k]]), when, change((v) => {
        e.when = v;
        for (const k of ["at", "zone", "side", "count", "group", "goal", "repeat"]) delete e[k];
        if (v === "time") e.at = 30;
        if (v === "zone") e.zone = (MS.data.zones || [])[0] || "";
        if (v === "destroyed") e.group = (MS.data.groups || [])[0] || "enemy";
        if (v === "goal") e.goal = (list("goal")[0] || {}).id || "";
      }), w.tip_ms_when, w.ms_when),
      linkButton(w.ms_delete, w.tip_ms_delete_event, change(() => { events.splice(i, 1); }), true)));
    const set = (key) => change((v) => { if (v === null || v === "") delete e[key]; else e[key] = v; });
    if (when === "time") {
      card.append(row(w.ms_at, number(e.at ?? 0, 0, 36000, 5, set("at"), w.tip_ms_at_s, w.ms_at)));
      card.append(row(w.ms_repeat, number(e.repeat ?? 0, 0, 36000, 5, change((v) => { if (v) e.repeat = Math.max(5, v); else delete e.repeat; }),
        w.tip_ms_repeat, w.ms_repeat)));
    }
    if (when === "zone") {
      card.append(row(w.ms_zone, select(pick(zones()), e.zone, set("zone"), w.tip_ms_when_zone, w.ms_zone),
        sideSelect(e.side ?? "", set("side"), w.tip_ms_when_side, true),
        number(e.count ?? 1, 1, 500, 1, set("count"), w.tip_ms_when_count, w.ms_count)));
    }
    if (when === "destroyed") card.append(row(w.ms_group, groupInput(e.group, set("group"), w.tip_ms_when_group)));
    if (when === "goal") card.append(row(w.ms_goal, select(pick(list("goal").map((g) => [g.id, textOf(g.text)])), e.goal, set("goal"),
      w.tip_ms_when_goal, w.ms_goal)));
    card.append(row(w.ms_wait, number(e.wait ?? 0, 0, 36000, 1, set("wait"), w.tip_ms_wait, w.ms_wait)));
    e.do = e.do || [];
    card.append(el("div", { className: "ms-head small", textContent: w.ms_then }));
    e.do.forEach((a, k) => card.append(actionRow(a, k, e)));
    card.append(select([["", w.ms_action_add], ...ACTIONS.map((k) => [k, w["ms_do_" + k]])], "", change((v) => {
      if (!v) return;
      // a new step starts filled in with the map's first point, zone and so on, so it saves at once (each can be
      // changed after); a spawn's unit is the one thing left to pick
      const a = { do: v }, first = (xs) => (xs || [])[0], sides = MS.data.sides || [];
      const group = first(MS.data.groups) || "units", point = first(MS.data.points), zone = first(MS.data.zones);
      if (v === "message") a.text = w.ms_message_new;
      if (v === "spawn") {
        a.count = 1;
        a.side = (sides.find((s) => s.player) || sides[0] || {}).number ?? 0;
        if (point) a.at = point;
        a.group = group;
        a.unit = "Unit_M4_Sherman";  // (the Sherman until another is picked)
      }
      if (["move", "attack", "hold", "artillery", "bombing", "paradrop"].includes(v)) a.group = group;
      if (v === "move" && point) a.to = [point];
      if (v === "attack") a.target = group;
      if (v === "hold" && zone) a.zone = zone;
      if (["artillery", "bombing", "paradrop"].includes(v) && point) a.at = point;
      if (v === "wait") a.seconds = 5;
      if (v === "camera") { a.seconds = 15; a.camera = first(MS.data.cameras) || (first(list("camera")) || {}).name || ""; }
      if (v === "money") { a.side = (sides.find((s) => s.player) || sides[0] || {}).number ?? 0; a.amount = 1000; }
      if (v === "ai") a.side = (sides.find((s) => !s.player) || sides[0] || {}).number ?? 0;
      if (v === "goal") a.goal = (list("goal").find((g) => g.start === "event") || {}).id || "";
      if (v === "complete") a.goal = (list("goal").find((g) => g.done === "event") || {}).id || "";
      e.do.push(a);
    }), w.tip_ms_action_add, w.ms_action_add));
    return card;
  }

  function renderEvents() {
    const w = W(), events = list("event");
    const add = el("button", { type: "button", className: "ghost small", textContent: w.ms_event_add, title: w.tip_ms_event_add });
    add.addEventListener("click", change(() => {
      const id = freeId("event", new Set([...events.map((e) => e.id), ...list("goal").map((g) => g.id)]));
      events.push({ id, when: "time", at: 30, do: [{ do: "message", text: w.ms_message_new }] });
    }));
    return [...(events.length ? events.map(eventCard) : [el("div", { className: "muted small", textContent: w.ms_events_none })]), add];
  }

  function renderCameras() {
    const w = W(), cams = list("camera");
    const out = [el("div", { className: "muted small", textContent: w.ms_cam_untried })];
    if (cams.length) {
      MS.cam = Math.min(MS.cam, cams.length - 1);
      out.push(chips(cams.map((c, i) => [i, c.name]), MS.cam, (i) => { MS.cam = i; MS.looking = false; render(); if (MS.onChange) MS.onChange(); },
        w.tip_ms_cam_pick));
      const c = cams[MS.cam];
      out.push(row(w.ms_cam_name, text(c.name, "", change((v) => {
        const clean = v.replace(/[^A-Za-z0-9_]/g, "_").replace(/^([^A-Za-z])/, "C$1").slice(0, 60);
        if (clean && !cams.some((x, j) => j !== MS.cam && x.name === clean)) {
          if (MS.draft.mission && MS.draft.mission.opening === c.name) MS.draft.mission.opening = clean;
          c.name = clean;
        }
      }), w.tip_ms_cam_name, w.ms_cam_name)));
      out.push(row(w.ms_seconds, number(c.seconds ?? 15, 1, 600, 1, change((v) => { c.seconds = v || 15; }), w.tip_ms_cam_seconds, w.ms_seconds)));
      out.push(row(fill(w.ms_cam_height, { m: MS.height }), number(MS.height, 5, 2000, 5, (v) => { MS.height = v || 120; render(); },
        w.tip_ms_cam_height, w.ms_cam_height_label)));
      out.push(el("div", { className: "small" }, el("span", { textContent: fill(w.ms_cam_points, { n: (c.points || []).length }) + " · " }),
        el("span", { className: "muted", textContent: MS.looking ? w.ms_cam_look_help : w.ms_cam_help })));
      const look = el("button", { type: "button", className: "chip", textContent: w.ms_cam_look, title: w.tip_ms_cam_look });
      look.setAttribute("aria-pressed", String(MS.looking));
      look.addEventListener("click", () => { MS.looking = !MS.looking; render(); });
      out.push(el("div", { className: "small ms-tools" }, look,
        linkButton(w.ms_cam_undo, w.tip_ms_cam_undo, change(() => { if ((c.points || []).length > 2) c.points.pop(); })),
        linkButton(w.ms_cam_play, w.tip_ms_cam_play, () => window.MissionView.onPlay && window.MissionView.onPlay(c)),
        linkButton(w.ms_delete, w.tip_ms_delete_cam, change(() => {
          if (MS.draft.mission && MS.draft.mission.opening === c.name) delete MS.draft.mission.opening;
          cams.splice(MS.cam, 1);
          MS.cam = 0;
        }), true)));
    } else {
      out.push(el("div", { className: "muted small", textContent: w.ms_cams_none }));
    }
    const add = el("button", { type: "button", className: "ghost small", textContent: w.ms_cam_add, title: w.tip_ms_cam_add });
    add.addEventListener("click", () => window.MissionView.onAddCamera && window.MissionView.onAddCamera());
    out.push(add);
    return out;
  }

  function render() {
    const box = MS.box;
    if (!box) return;
    const parts = head();
    if (MS.data && MS.data.allowed && MS.draft) {
      if (MS.tool === "mission") parts.push(...renderMission());
      if (MS.tool === "goals") parts.push(...renderGoals());
      if (MS.tool === "events") parts.push(...renderEvents());
      if (MS.tool === "cameras") parts.push(...renderCameras());
      parts.push(problems());
    }
    box.replaceChildren(...parts);
  }

  window.MissionView = {
    onPlay: null,        // maps.js: play a camera move on the map view
    onAddCamera: null,   // maps.js: start a new camera move round the view's middle
    // open a tray: ctx {api, words, lang, pack, units (the Add unit list), nationNames, box, onChange}
    async open(ctx, tool) {
      Object.assign(MS, { api: ctx.api, words: ctx.words, lang: ctx.lang, units: ctx.units || [],
        nationNames: ctx.nationNames || [], box: ctx.box, onChange: ctx.onChange, tool });
      if (MS.pack !== ctx.pack || !MS.data) {
        MS.pack = ctx.pack;
        MS.data = null;
        MS.error = "";
        render();
        try {
          MS.data = await MS.api.mission(ctx.pack);
          MS.draft = copy(MS.data.mission || {});
        } catch (err) {
          MS.data = { allowed: false, why: (err && err.message) || String(err) };
        }
      }
      render();
    },
    forget() { MS.pack = null; MS.data = null; MS.draft = null; },
    render,
    data: () => MS.data,
    draft: () => MS.draft,
    camera: () => (MS.draft && (MS.draft.camera || [])[MS.cam]) || null,
    looking: () => MS.looking,
    heightUnits: () => MS.height * METRE,
    // a click on the map while Camera moves is open: the next point (at the height set over the ground), or the
    // spot the move looks at
    cameraClick(x, y, ground) {
      const c = window.MissionView.camera();
      if (!c) return;
      if (MS.looking) { c.look = [Math.round(x), Math.round(y), Math.round(ground)]; MS.looking = false; }
      else c.points = [...(c.points || []), [Math.round(x), Math.round(y), Math.round(ground + MS.height * METRE)]];
      save();
    },
    addCamera(cam) {
      const cams = list("camera");
      let n = cams.length + 1;
      while (cams.some((c) => c.name === "Camera_" + n)) n += 1;
      cams.push({ name: "Camera_" + n, seconds: 15, ...cam });
      MS.cam = cams.length - 1;
      save();
    },
  };
})();
