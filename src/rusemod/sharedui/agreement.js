// The first-start agreement + username screen (plan §3a), ONE implementation shared by the Launcher and the Studio.
// It's served to both apps at shared/agreement.js (rusemod.webui.serve mounts rusemod/sharedui at "shared"), injects
// its own markup and styles (so neither app's index.html or style.css carries a copy), and the app calls
// window.Agreement.open({api, words, fairOn}) at startup, after the language pick and before "how would you like to
// build a mod?" / "Choose your mods".
//
// RUSE Guard, with its program check, is required (Accept -> guard_accept_terms); Bug Watch (bugwatch_on) is opt-in.
// Then "Choose your username" -- always, since RUSE Guard is required -> set_username (guard-only) or bugwatch_on. Gated
// off until RUSE Guard is live (fairOn); the words come from the app (words.toml agree_*/username_*, English fallback).
(function () {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const text = (el, s) => { if (el) el.textContent = s || ""; };
  let ready = false;

  function inject() {
    if (ready) return;
    ready = true;
    const style = document.createElement("style");
    style.textContent = [
      ".agree-overlay{position:fixed;inset:0;z-index:60;display:grid;place-items:center;padding:16px;background:rgba(5,12,24,.72)}",
      ".agree-box{position:relative;width:min(680px,100%);max-height:100%;overflow:auto;padding:24px 28px 20px;",
      "background:var(--panel,#132033);border:1px solid var(--line,#2c3a4f);border-radius:10px;color:var(--text,#e6edf6)}",
      ".agree-box h1{margin:0 0 6px;font-size:22px}.agree-box h2{margin:16px 0 4px;font-size:15px}",
      ".agree-row{display:flex;gap:8px;align-items:flex-start;margin:14px 0 2px}.agree-row input{margin-top:3px}",
      ".agree-full{white-space:pre-wrap;max-height:40vh;overflow-y:auto;margin:6px 0 2px;padding:10px 12px;",
      "border:1px solid var(--line,#2c3a4f);border-radius:6px;line-height:1.5;font-size:12px}",
      ".agree-box .muted{color:var(--muted,#9fb0c6)}.agree-box .small{font-size:12px}",
      ".agree-box input[type=text]{width:100%;max-width:280px;padding:7px 9px;margin:8px 0;",
      "border:1px solid var(--line,#2c3a4f);border-radius:6px;background:var(--bg,#0a1628);color:inherit}",
      ".agree-box .actions{margin-top:16px}.agree-box summary{cursor:pointer;margin-top:12px}",
      ".agree-box .bad{color:var(--bad,#ff8a8a)}.agree-hidden{display:none}",
    ].join("");
    document.head.appendChild(style);
    const holder = document.createElement("div");
    holder.innerHTML =
      '<div id="agree" class="agree-overlay agree-hidden" role="dialog" aria-modal="true" aria-labelledby="agree-title"><div class="agree-box">' +
      '<h1 id="agree-title"></h1><p id="agree-intro" class="muted small"></p>' +
      '<h2 id="agree-guard-title"></h2><p id="agree-guard" class="small"></p>' +
      '<label class="agree-row agree-hidden" id="agree-bugwatch-row"><input id="agree-bugwatch" type="checkbox"> <span id="agree-bugwatch-label"></span></label>' +
      '<p id="agree-bugwatch-note" class="muted small agree-hidden"></p>' +
      '<details><summary id="agree-full-toggle" class="small"></summary><pre id="agree-full" class="agree-full"></pre></details>' +
      '<p id="agree-accept-note" class="muted small"></p>' +
      '<div class="actions"><button id="agree-accept" type="button" class="primary"></button></div>' +
      '</div></div>' +
      '<div id="username" class="agree-overlay agree-hidden" role="dialog" aria-modal="true" aria-labelledby="username-title"><div class="agree-box">' +
      '<h1 id="username-title"></h1><p id="username-help" class="muted small"></p>' +
      '<div><input id="username-name" type="text" maxlength="34" autocomplete="off"></div>' +
      '<div class="actions"><button id="username-save" type="button" class="primary"></button></div>' +
      '<p id="username-note" class="small" role="status"></p>' +
      '</div></div>';
    document.body.append(...holder.childNodes);
  }

  function renderAgreement(words, bugwatch) {
    const w = words;
    $("agree").classList.remove("agree-hidden");
    text($("agree-title"), w.agree_title);
    text($("agree-intro"), w.agree_intro);
    text($("agree-guard-title"), w.agree_guard_title);
    text($("agree-guard"), w.agree_guard);
    $("agree-bugwatch-row").classList.toggle("agree-hidden", !bugwatch);
    $("agree-bugwatch-note").classList.toggle("agree-hidden", !bugwatch);
    text($("agree-bugwatch-label"), w.bugwatch_on_label);
    text($("agree-bugwatch-note"), w.set_bugwatch_help);
    text($("agree-full-toggle"), w.agree_full_toggle);
    text($("agree-full"), w.agree_full);
    text($("agree-accept-note"), w.agree_accept_note);
    text($("agree-accept"), w.agree_accept);
  }

  // `status`: bugwatch_status() as the app had it ({available, on, name}). A player shown a new version of the
  // agreement (rusemod.guard.TERMS_VERSION raised) has a username already: it stays (asked again, a new #number would
  // have replaced it, and with it whose crashes and matches are whose), and the Bug Watch tick starts as it is now,
  // so the box says what accepting leaves on; untick it and Bug Watch goes off, tick it and it comes on.
  function accept(api, words, status) {
    return new Promise((done) => {
      renderAgreement(words, status.available);
      $("agree-bugwatch").checked = Boolean(status.available && status.on);
      const btn = $("agree-accept");
      const handler = async () => {
        const bw = status.available && $("agree-bugwatch").checked;
        btn.disabled = true;
        try {
          await api.guard_accept_terms();   // RUSE Guard, with its program check, is on for everyone who accepts
        } catch (e) { btn.disabled = false; return; }  // a failure keeps the screen up; the player can try again
        btn.removeEventListener("click", handler);
        $("agree").classList.add("agree-hidden");
        if (status.name) {   // agreed to an earlier version: the username stays, Bug Watch as the tick says
          try {
            if (bw && !status.on) await api.bugwatch_on(status.name);
            else if (!bw && status.on) await api.bugwatch_off();
          } catch (e) { /* Settings keeps the switch */ }
        } else {
          await askUsername(api, words, bw);   // RUSE Guard is required, so a username is always needed
        }
        done();
      };
      btn.addEventListener("click", handler);
    });
  }

  function askUsername(api, words, bugwatchOn) {
    return new Promise((done) => {
      const w = words, note = $("username-note"), nameInput = $("username-name"), btn = $("username-save");
      $("username").classList.remove("agree-hidden");
      text($("username-title"), w.username_title);
      text($("username-help"), w.username_help);
      nameInput.placeholder = w.bugwatch_name_hint;
      nameInput.value = "";
      text($("username-save"), w.username_save);
      note.textContent = ""; note.className = "small";
      nameInput.focus();
      const save = async () => {
        const name = nameInput.value.trim();
        if (!name) { note.textContent = w.username_need; note.className = "small bad"; return; }
        btn.disabled = true;
        try {
          if (bugwatchOn) await api.bugwatch_on(name);   // the shared id + name, and Bug Watch on
          else await api.set_username(name);              // the shared id + name only (for RUSE Guard)
        } catch (e) { btn.disabled = false; note.textContent = (e && e.message) || String(e); note.className = "small bad"; return; }
        btn.removeEventListener("click", save);
        nameInput.removeEventListener("keydown", onKey);
        $("username").classList.add("agree-hidden");
        done();
      };
      const onKey = (e) => { if (e.key === "Enter") { e.preventDefault(); save(); } };
      btn.addEventListener("click", save);
      nameInput.addEventListener("keydown", onKey);
    });
  }

  async function open(opts) {
    const api = opts.api, words = opts.words;
    if (!opts.fairOn) return;                                   // RUSE Guard not live yet: no gate
    let st;
    try { st = await api.guard_status(); } catch (e) { return; }  // an older back end: no guard
    if ((st.terms || 0) >= (st.terms_version || 1)) return;     // already accepted
    inject();
    let status = { available: false, on: false, name: "" };
    try {
      const got = await api.bugwatch_status();
      status = { available: Boolean(got.available), on: Boolean(got.on), name: String(got.name || "") };
    } catch (e) { /* an older back end: no Bug Watch box, the username asked */ }
    await accept(api, words, status);
  }

  window.Agreement = { open };
})();
