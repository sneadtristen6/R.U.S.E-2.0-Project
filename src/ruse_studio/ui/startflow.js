// The start screen and a new mod's steps (StudioApi.start_mods, prefs "start_skip"; the owner, 2026-10-18: "the whole
// studio screen is hidden behind a series of menus when you start the studio ... You can either load an existing mod
// and it takes you to the studio as is right now ... or start a new mod ... And then an option to just bypass both";
// on skipping: "are you an experienced modder? Select here and you can always have this menu skip", kept in Settings).
//
// The start screen: Carry on with a mod (only when there's one: never on a fresh install), Start a new mod, Skip, and
// the tick that always skips it. A new mod's steps: its name; what each nation keeps (the Nations tab itself, with
// Keep its units / Start it empty on each nation); research (keep the game's, none, or custom: the game's, changed on
// the board); the board of each nation's buildings (board.js); "What will your mod change?", whose ticked tabs come
// next, each the tab itself with the steps' bar above it (never a second copy of an editor); then done. Maps keep
// their own start in the Maps tab. Uses app.js's $, el, fill, say, problem, api, state, showView, useMods, modChanged,
// pickMod and window.NationsView.
(function () {
  "use strict";
  const CHANGES = [  // "What will your mod change?": each tick's tab (the economy is in AI and player settings, 10-22)
    ["units", "flow_change_units", "tip_flow_change_units"], ["ai", "flow_change_ai", "tip_flow_change_ai"],
    ["decoy", "flow_change_music", "tip_flow_change_music"], ["values", "flow_change_values", "tip_flow_change_values"]];
  const TAB_WORD = { units: "units_tab", ai: "ai_tab", decoy: "decoy_tab", values: "values_files_tab" };
  const RESEARCH = [["keep", "flow_research_keep", "flow_research_keep_help"],
    ["none", "flow_research_none", "flow_research_none_help"],
    ["custom", "flow_research_custom", "flow_research_custom_help"]];
  const F = { on: false, step: 0, steps: [], name: "", made: null, research: "keep", applied: "game", ticks: new Set(),
    nation: 0, board: null };
  const W = () => state.words || {};

  // --- the start screen ---
  async function atStart(ready) {
    if (!ready) return;  // the game index is built first (its own screen): the Studio opens as it always did
    let prefs = {};
    try { prefs = (await api().prefs()) || {}; } catch { /* an older back end */ }
    if (prefs.start_skip) return;
    await openStart();
  }

  async function openStart(list = false) {
    const w = W();
    let mods = [];
    try { mods = (await api().start_mods()).mods || []; } catch (err) { problem(err); }
    $("ss-title").textContent = w.ss_title;
    const body = $("ss-body");
    const big = (word, tip, act, cls = "") => {
      const b = el("button", { type: "button", className: "ss-choice " + cls, title: w[tip] || "" },
        el("strong", { textContent: w[word] }), el("span", { className: "muted small", textContent: w[tip] || "" }));
      b.addEventListener("click", act);
      return b;
    };
    const always = el("input", { type: "checkbox", title: w.tip_ss_always });
    try { always.checked = Boolean(((await api().prefs()) || {}).start_skip); } catch { /* an older back end */ }
    always.addEventListener("change", () => api().set_pref("start_skip", always.checked ? true : null).catch(problem));
    const tick = el("label", { className: "ss-always small", title: w.tip_ss_always }, always, " " + w.ss_always);
    if (list && mods.length) {
      const back = el("button", { type: "button", className: "small ghost", textContent: w.ss_back, title: w.tip_ss_back });
      back.addEventListener("click", () => openStart(false));
      body.replaceChildren(el("h2", { textContent: w.ss_carry_head }),
        el("ul", { className: "ss-mods" }, ...mods.map((m) => {
          const open = el("button", { type: "button", className: "small primary", textContent: w.ss_open,
            title: fill(w.tip_ss_open, { name: m.name }) });
          open.addEventListener("click", async () => {
            closeStart();
            await pickMod({ target: { value: m.path } }, "mod");
          });
          const when = new Date(m.changed * 1000).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
          return el("li", {}, el("div", {}, el("strong", { textContent: m.name }),
            el("div", { className: "muted small", textContent: fill(w.ss_changed, { when }) })), open);
        })), el("div", { className: "actions" }, back), tick);
    } else {
      const choices = [];
      if (mods.length) choices.push(big("ss_carry", "tip_ss_carry", () => openStart(true), "primary"));  // never on a fresh install
      choices.push(big("ss_new", "tip_ss_new", () => { closeStart(); startFlow(); }, mods.length ? "" : "primary"));
      choices.push(big("ss_skip", "tip_ss_skip", closeStart, "ghost"));
      body.replaceChildren(el("div", { className: "ss-choices" }, ...choices), tick);
    }
    $("start-screen").classList.remove("hidden");
    const first = body.querySelector("button");
    if (first) first.focus();
  }

  function closeStart() { $("start-screen").classList.add("hidden"); }

  // Settings > Start screen: shown when the Studio opens, or always skipped; and open it now
  async function renderSetting() {
    const w = W(), show = $("set-start-show");
    let prefs = {};
    try { prefs = (await api().prefs()) || {}; } catch { /* an older back end */ }
    show.checked = !prefs.start_skip;
    show.title = w.tip_set_start_show;
    $("set-start-show-label").textContent = w.set_start_show;
    $("set-start-show-label").title = w.tip_set_start_show;
    show.onchange = () => api().set_pref("start_skip", show.checked ? null : true).catch(problem);
    const open = $("set-start-open");
    open.textContent = w.set_start_open;
    open.title = w.tip_set_start_open;
    open.onclick = () => openStart(false);
  }

  // --- a new mod's steps ---
  function startFlow() {
    Object.assign(F, { on: true, step: 0, name: "", made: null, research: "keep", applied: "game", ticks: new Set(),
      nation: 0, board: null });
    F.steps = ["name", "nations", "research", "board", "change", "done"];
    go(0);
  }

  function stepWord(s) {
    const w = W();
    return TAB_WORD[s] ? w[TAB_WORD[s]] || s : w["flow_step_" + s] || s;
  }

  function bar() {
    const w = W(), b = $("flow-bar");
    if (!F.on) { b.classList.add("hidden"); b.replaceChildren(); return; }
    const chips = F.steps.map((s, i) => el("span", { className: "flow-chip" + (i === F.step ? " now" : i < F.step ? " done" : ""),
      textContent: `${i + 1}. ${stepWord(s)}` }));
    const back = el("button", { type: "button", className: "small ghost", textContent: w.flow_back, title: w.tip_flow_back,
      disabled: F.step === 0 });
    back.addEventListener("click", () => go(F.step - 1));
    const last = F.steps[F.step] === "done";
    const next = el("button", { type: "button", className: "small primary", textContent: last ? w.flow_finish : w.flow_next,
      title: last ? w.tip_flow_finish : w.tip_flow_next });
    next.addEventListener("click", () => leave(F.step + 1));
    const out = el("button", { type: "button", className: "small ghost", textContent: w.flow_studio, title: w.tip_flow_studio });
    out.addEventListener("click", finish);
    const help = w["flow_help_" + F.steps[F.step]];  // a tab's step: what to do there, in one line
    b.replaceChildren(el("span", { className: "small flow-title", textContent: fill(w.flow_bar, { n: F.step + 1, all: F.steps.length,
      step: stepWord(F.steps[F.step]) }) }), el("span", { className: "flow-chips" }, ...chips), back, next, out,
      ...(help ? [el("div", { className: "muted small flow-help", textContent: help })] : []));
    b.classList.remove("hidden");
  }

  // leaving a step: what it set is saved first (the name makes the mod; research is applied), then the next one
  async function leave(to) {
    const w = W(), s = F.steps[F.step];
    try {
      if (s === "name") {
        const typed = ($("flow-name").value || "").trim();
        if (!typed) { $("flow-name").focus(); say(w.flow_name_needed, "warn"); return; }
        F.name = typed;
        if (!F.made) {
          useMods(await api().new_mod(typed, "mod"));
          F.made = state.mod;
          await modChanged();
          say(fill(w.flow_made, { name: typed }), "ok");
        }
      }
      // "No research": every unit buildable from the start; Keep and Custom both start from the game's research,
      // given back when No research was applied before (Back, then another choice)
      const want = F.research === "none" ? "none" : "game";
      if (s === "research" && want !== F.applied) {
        const res = want === "none" ? await api().research_clear_all() : await api().research_reset_all();
        F.applied = want;
        say(want === "none" ? fill(w.flow_research_none_done, { n: res.cleared }) : w.flow_research_reset_done, "ok");
      }
      if (s === "nations" && window.NationsView && window.NationsView.setFlow) window.NationsView.setFlow(false);
      if (s === "change") {
        const keep = F.steps.slice(0, F.steps.indexOf("change") + 1);
        F.steps = [...keep, ...CHANGES.map(([tab]) => tab).filter((t) => F.ticks.has(t)), "done"];
      }
      if (s === "done" && to >= F.steps.length) { finish(); return; }
    } catch (err) { problem(err); return; }
    go(to);
  }

  function go(i) {
    F.step = Math.max(0, Math.min(i, F.steps.length - 1));
    const s = F.steps[F.step];
    bar();
    const page = $("flow-page");
    const own = ["name", "research", "board", "change", "done"].includes(s);  // a page of the steps' own
    document.body.classList.toggle("flow-page-on", own);  // (the tabs wait behind it)
    if (own) {
      page.classList.remove("hidden");
      page.replaceChildren(el("div", { className: "settings flow-inner" }, ...stepPage(s)));
      const input = page.querySelector("input");
      if (input) input.focus();
      return;
    }
    page.classList.add("hidden");
    page.replaceChildren();
    if (s === "nations") {
      showView("nations");
      if (window.NationsView && window.NationsView.setFlow) window.NationsView.setFlow(true);
      return;
    }
    showView(s);  // a ticked tab: the tab itself, the steps' bar above it
  }

  function stepPage(s) {
    const w = W();
    if (s === "name") {
      const input = el("input", { id: "flow-name", className: "wide", maxLength: 60, autocomplete: "off", value: F.name,
        placeholder: w.flow_name_placeholder, title: w.tip_flow_name, disabled: Boolean(F.made) });
      input.addEventListener("keydown", (e) => { if (e.key === "Enter") leave(F.step + 1); });
      return [el("h1", { textContent: w.flow_name_head }), el("p", { className: "muted small",
        textContent: F.made ? fill(w.flow_name_made, { name: F.name }) : w.flow_name_help }), input];
    }
    if (s === "research") {
      const rows = RESEARCH.map(([key, word, help]) => {
        const r = el("input", { type: "radio", name: "flow-research", value: key, checked: F.research === key,
          title: w[help] });
        r.addEventListener("change", () => { F.research = key; });
        return el("label", { className: "flow-option", title: w[help] }, r,
          el("span", {}, el("strong", { textContent: " " + w[word] }), el("div", { className: "muted small", textContent: w[help] })));
      });
      return [el("h1", { textContent: w.flow_research_head }), el("p", { className: "muted small", textContent: w.flow_research_help }),
        ...rows];
    }
    if (s === "board") {
      const flags = el("div", { className: "flow-nations", role: "group" });
      const holder = el("div", { className: "board" });
      const names = (state.nationNames && state.nationNames.length ? state.nationNames : []);
      const pick = (n) => {
        F.nation = n;
        for (const b of flags.querySelectorAll("button")) b.setAttribute("aria-pressed", String(Number(b.dataset.n) === n));
        F.board = window.BoardView.mount(holder, n, names[n] || String(n));
      };
      for (let n = 0; n < 7; n++) {
        const b = el("button", { type: "button", className: "chip", textContent: names[n] || String(n),
          title: fill(w.tip_flow_board_nation, { nation: names[n] || String(n) }) });
        b.dataset.n = String(n);
        b.addEventListener("click", () => pick(n));
        flags.append(b);
      }
      setTimeout(() => pick(F.nation), 0);
      return [el("h1", { textContent: w.flow_board_head }),
        el("p", { className: "muted small", textContent: F.research === "custom" ? w.flow_board_help_custom : w.flow_board_help }),
        flags, holder];
    }
    if (s === "change") {
      const rows = CHANGES.map(([tab, word, tip]) => {
        const c = el("input", { type: "checkbox", checked: F.ticks.has(tab), title: w[tip] });
        c.addEventListener("change", () => { if (c.checked) F.ticks.add(tab); else F.ticks.delete(tab); });
        return el("label", { className: "flow-option", title: w[tip] }, c,
          el("span", {}, el("strong", { textContent: " " + w[word] }), el("div", { className: "muted small", textContent: w[tip] })));
      });
      return [el("h1", { textContent: w.flow_change_head }), el("p", { className: "muted small", textContent: w.flow_change_help }),
        ...rows];
    }
    // done
    const test = el("button", { type: "button", className: "primary", textContent: w.flow_done_test, title: w.tip_flow_done_test });
    test.addEventListener("click", () => { finish(); $("test").click(); });
    const studio = el("button", { type: "button", className: "ghost", textContent: w.flow_studio, title: w.tip_flow_studio });
    studio.addEventListener("click", finish);
    return [el("h1", { textContent: fill(w.flow_done_head, { name: F.name || state.mod || "" }) }),
      el("p", { className: "muted small", textContent: w.flow_done_help }), el("div", { className: "actions" }, test, studio)];
  }

  function finish() {
    if (window.NationsView && window.NationsView.setFlow) window.NationsView.setFlow(false);
    F.on = false;
    bar();
    document.body.classList.remove("flow-page-on");
    $("flow-page").classList.add("hidden");
    $("flow-page").replaceChildren();
    if (["name", "research", "board", "change", "done"].includes(F.steps[F.step])) showView("units");
  }

  // the language changed while the screen or the steps are up: their words again
  function setWords() {
    if (!$("start-screen").classList.contains("hidden")) openStart(Boolean($("ss-body").querySelector(".ss-mods")));
    if (F.on) go(F.step);
  }

  window.StartFlow = { atStart, openStart, renderSetting, startFlow, setWords, active: () => F.on };
})();
