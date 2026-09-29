// The home screen (PLAN.md L5, screen 6). It talks to LauncherApi (launcher/api.py) through
// window.pywebview.api; in a normal browser, open index.html?fake to use the made-up API in fake-api.js.
"use strict";

const $ = (id) => document.getElementById(id);
const state = { sets: [], active: "vanilla", playing: false };

function api() {
  return window.pywebview.api;
}

function text(el, value) {
  el.textContent = value || "";
}

function renderStatus(status) {
  const el = $("status");
  text(el, status.message);
  el.className = "status " + (status.found ? "good" : "bad");
  $("choose").classList.toggle("hidden", status.found);
}

function renderSets() {
  const list = $("set-list");
  list.replaceChildren();
  for (const set of state.sets) {
    const li = document.createElement("li");
    const card = document.createElement("button");
    card.type = "button";
    card.className = "set-card";
    card.setAttribute("aria-pressed", String(set.id === state.active));
    const name = document.createElement("span");
    name.className = "name";
    text(name, set.name);
    const meta = document.createElement("span");
    meta.className = set.error ? "warn" : "meta";
    text(meta, set.error ? "Has a mistake" : set.id === "vanilla" ? "No mods" :
      `${set.mods.length} mod${set.mods.length === 1 ? "" : "s"}`);
    card.append(name, meta);
    card.addEventListener("click", () => {
      if (state.playing) return;
      state.active = set.id;
      renderSets();
      renderActive();
    });
    li.append(card);
    list.append(li);
  }
}

function renderActive() {
  const set = state.sets.find((s) => s.id === state.active) || state.sets[0];
  if (!set) return;
  text($("active-name"), set.name);
  text($("active-description"), set.description);
  const mods = $("active-mods");
  mods.replaceChildren(...set.mod_names.map((n) => {
    const li = document.createElement("li");
    text(li, n);
    return li;
  }));
  const err = $("active-error");
  text(err, set.error ? `This mod set has a mistake: ${set.error}` : "");
  err.classList.toggle("hidden", !set.error);
  const play = $("play");
  text(play, set.id === "vanilla" ? "Play" : `Play ${set.name}`);
  play.disabled = state.playing || Boolean(set.error);
}

function setMessage(message, kind) {
  const el = $("play-message");
  text(el, message);
  el.className = "message" + (kind ? " " + kind : "");
}

async function refresh() {
  renderStatus(await api().status());
  state.sets = await api().mod_sets();
  if (!state.sets.some((s) => s.id === state.active)) state.active = "vanilla";
  renderSets();
  renderActive();
}

async function play() {
  state.playing = true;
  renderActive();
  renderSets();
  const log = $("log");
  log.textContent = "";
  $("progress").classList.remove("hidden");
  setMessage("Getting everything ready…");
  const { job } = await api().play(state.active);
  let seen = 0;
  const tick = async () => {
    const j = await api().job(job, seen);
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
    renderActive();
    renderSets();
  };
  tick();
}

function start() {
  $("play").addEventListener("click", play);
  $("open-sets").addEventListener("click", async () => {
    await api().open_sets_folder();
  });
  $("choose").addEventListener("click", async () => {
    renderStatus(await api().choose_game_folder());
    await refresh();
  });
  window.addEventListener("focus", () => {
    if (!state.playing) refresh();  // mod sets edited while the launcher was in the background show up
  });
  refresh();
}

let started = false;
function startOnce() {
  if (started) return;
  started = true;
  start();
}
window.addEventListener("pywebviewready", startOnce);
if (window.pywebview && window.pywebview.api && window.pywebview.api.status) startOnce();
