// Owned copies, layer 2 (rusemod.ownedpass): "Sign in through Steam". A small panel to sign in through Steam so the
// project can confirm the player owns R.U.S.E. for online play, RUSE Guard and content downloads. The player signs in
// on Steam's own page in their browser; the panel waits for the server to hand back a signed pass. The same file in
// both apps' ui folders. While layer 2 is switched off (owned_pass_status().on is false) nothing is shown.
(() => {
  "use strict";
  const STYLE = `
.osi-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center;
  background: rgba(4, 10, 20, 0.72); padding: 16px; }
.osi-panel { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: var(--radius);
  max-width: 560px; width: 100%; max-height: calc(100vh - 32px); overflow-y: auto; padding: 18px 20px; }
.osi-panel h2 { margin: 0 0 10px; font-size: 1.15em; }
.osi-panel p { margin: 8px 0; line-height: 1.4; }
.osi-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 12px 0 4px; }
.osi-note { color: var(--muted); }
.osi-note.good { color: var(--good, var(--ok)); }
.osi-note.bad { color: var(--bad, var(--error)); }
.osi-close { float: right; }`;

  // which status key a poll outcome's message falls back to, when the server sent none
  const ERR_KEY = { "not-owned": "err_not_owned", "private": "err_private", "steam-error": "err_steam",
                    "bad-pass": "err_bad_pass", "expired": "err_expired" };

  let session = 0;  // bumped on each open/close, so a poll loop from a panel that's gone stops itself

  function api() { return window.pywebview && window.pywebview.api; }

  function el(tag, props, kids) {
    const node = document.createElement(tag);
    Object.assign(node, props || {});
    for (const kid of kids || []) node.append(kid);
    return node;
  }

  function button(word, tip, onclick) {
    return el("button", { type: "button", className: "small", textContent: word, title: tip, onclick });
  }

  function close() {
    session++;
    const old = document.getElementById("osi-overlay");
    if (old) old.remove();
  }

  function whenDate(ts) {
    try { return new Date(ts * 1000).toLocaleDateString(); } catch { return ""; }
  }

  function panel(w, kids) {
    if (!document.getElementById("osi-style")) document.head.append(el("style", { id: "osi-style", textContent: STYLE }));
    close();
    const body = el("div", { className: "osi-panel" }, [button(w.close, w.tip_close, close),
                                                        el("h2", { id: "osi-title", textContent: w.title })].concat(kids));
    body.firstChild.classList.add("osi-close");
    body.setAttribute("role", "dialog");
    body.setAttribute("aria-modal", "true");
    body.setAttribute("aria-labelledby", "osi-title");
    document.body.append(el("div", { id: "osi-overlay", className: "osi-overlay" }, [body]));
    return body;
  }

  // Settings listens for this: the kept pass changed, or the panel opened or closed.
  function notify(status) {
    try { window.dispatchEvent(new CustomEvent("ownedsignin", { detail: status || null })); } catch { /* an old window */ }
  }

  function render(status) {
    notify(status);
    const w = status.words || {};
    if (!status.on) {
      panel(w, [el("p", { className: "osi-note", textContent: w.off || "" })]);
      return;
    }
    if (status.signed_in && status.owned) {
      panel(w, [
        el("p", { className: "osi-note good", textContent: w.signed_in }),
        el("p", { textContent: (w.until || "").replace("{date}", whenDate(status.until)) }),
        el("div", { className: "osi-row" }, [button(w.sign_out, w.tip_sign_out, signOut)]),
      ]);
      return;
    }
    panel(w, [
      el("p", { textContent: w.intro }),
      el("p", { className: "osi-note", textContent: w.not_signed_in }),
      el("div", { className: "osi-row" }, [button(w.sign_in, w.tip_sign_in, () => signIn(w))]),
    ]);
  }

  function waiting(w, note, kind) {
    panel(w, [
      el("p", { className: "osi-note " + (kind || ""), textContent: note }),
      el("p", { className: "osi-note", textContent: w.waiting_note || "" }),
      el("div", { className: "osi-row" }, [button(w.cancel, w.tip_cancel, close)]),
    ]);
  }

  async function signIn(w) {
    let info;
    try { info = await api().owned_sign_in_start(); }
    catch (err) { waiting(w, w.err_reach || String(err), "bad"); return; }
    if (!info || !info.on) { render(await loadStatus()); return; }
    waiting(w, w.waiting, "");
    // this sign-in owns the panel waiting() just drew until it's closed or reopened. Taken after drawing it: drawing a
    // panel moves `session` on (panel() closes the one before), so a number taken first stopped every check before it
    // ran (the owner's 0.4.8.10 sign-in, 2026-11-01: Steam's page done, the Launcher never asked the server)
    const mine = session;
    const every = Math.max(1, info.poll_every || 3) * 1000;
    const until = Date.now() + (info.expires_in || 600) * 1000;
    const tick = async () => {
      if (mine !== session) return;
      if (Date.now() > until) { waiting(w, w.err_expired, "bad"); return; }
      let result;
      try { result = await api().owned_sign_in_poll(info.code); }
      catch { setTimeout(tick, every); return; }
      if (mine !== session) return;
      if (!result || result.status === "pending") { setTimeout(tick, every); return; }
      if (result.status === "owned") { render(result.words ? result : await loadStatus()); return; }
      waiting(w, result.message || w[ERR_KEY[result.status] || "err_steam"] || "", "bad");
    };
    setTimeout(tick, every);
  }

  async function signOut() {
    render(await api().owned_sign_out());
  }

  async function loadStatus() {
    try { return await api().owned_pass_status(); }
    catch { return { on: false, words: {} }; }
  }

  async function open() {
    render(await loadStatus());
  }

  async function atStart() {
    const status = await loadStatus();
    if (!status || !status.on || status.signed_in) return;
    let asked = false;
    try { asked = localStorage.getItem("osi-asked") === "1"; } catch { /* no storage: ask */ }
    if (asked) return;  // asked once already; the Launcher's Settings opens it whenever they want
    try { localStorage.setItem("osi-asked", "1"); } catch { /* fine */ }
    open();
  }

  window.OwnedSignIn = { open, close };
  if (api()) atStart();
  else window.addEventListener("pywebviewready", atStart, { once: true });
})();
