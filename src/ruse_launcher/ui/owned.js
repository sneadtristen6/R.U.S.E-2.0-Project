// Owned copies only (rusemod.owned): when the game folder in use isn't a copy its player owns, as far as the apps
// can tell, a box says why and how to fix it: Steam's own check of the game's files, or a ticket (Discord or GitHub)
// with the player's folder code, answered with an unlock code pasted here. The same file in both apps' ui folders.
(() => {
  "use strict";
  const STYLE = `
.owned-overlay { position: fixed; inset: 0; z-index: 1000; display: flex; align-items: center; justify-content: center;
  background: rgba(4, 10, 20, 0.72); padding: 16px; }
.owned-panel { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: var(--radius);
  max-width: 620px; width: 100%; max-height: calc(100vh - 32px); overflow-y: auto; padding: 18px 20px; }
.owned-panel h2 { margin: 0 0 10px; font-size: 1.15em; }
.owned-panel p { margin: 8px 0; line-height: 1.4; }
.owned-panel ul { margin: 6px 0 10px 18px; padding: 0; color: var(--bad, var(--error)); }
.owned-row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0; }
.owned-row code { background: var(--panel-hi); border: 1px solid var(--line); border-radius: 4px; padding: 3px 8px;
  font-size: 1.05em; letter-spacing: 0.06em; user-select: all; }
.owned-row input { flex: 1 1 260px; min-width: 0; }
.owned-note { color: var(--muted); }
.owned-note.good { color: var(--good, var(--ok)); }
.owned-note.bad { color: var(--bad, var(--error)); }
.owned-close { float: right; }`;

  let view = null;

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

  async function copy(code, btn, w) {
    try { await navigator.clipboard.writeText(code); }
    catch {  // a window without the clipboard API: the old way
      const box = el("textarea", { value: code });
      document.body.append(box);
      box.select();
      document.execCommand("copy");
      box.remove();
    }
    btn.textContent = w.copied;
    setTimeout(() => { btn.textContent = w.copy; }, 1500);
  }

  function close() {
    const old = document.getElementById("owned-overlay");
    if (old) old.remove();
  }

  function show(v, note, kind) {
    view = v;
    close();
    if (!document.getElementById("owned-style")) document.head.append(el("style", { id: "owned-style", textContent: STYLE }));
    const w = v.words;
    const why = {
      no_steam_record: w.why_no_steam_record,
      steam_file: w.why_steam_file,
      fake_steam: (w.why_fake_steam || "").replace("{names}", (v.fake || []).join(", ")),
    };
    const unlockBox = el("input", { type: "text", title: w.tip_unlock_box, placeholder: w.unlock_label,
                                    spellcheck: false, autocomplete: "off" });
    unlockBox.setAttribute("aria-label", w.unlock_label);
    const copyBtn = button(w.copy, w.tip_copy, () => copy(v.code, copyBtn, w));
    const panel = el("div", { className: "owned-panel" }, [
      button(w.close, w.tip_close, close),
      el("h2", { id: "owned-title", textContent: w.title }),
      el("ul", {}, (v.reasons || []).map((r) => el("li", { textContent: why[r] || r }))),
      el("p", { textContent: w.body }),
      el("p", { textContent: w.if_steam }),
      el("div", { className: "owned-row" }, [
        button(w.steam_check, w.tip_steam_check, () => api().owned_open("steam")),
        button(w.check_again, w.tip_check_again, recheck),
      ]),
      el("p", { textContent: w.if_other }),
      el("div", { className: "owned-row" }, [
        el("span", { textContent: w.your_code }), el("code", { textContent: v.code }), copyBtn,
      ]),
      el("div", { className: "owned-row" }, [
        button(w.discord, w.tip_discord, () => api().owned_open("discord")),
        button(w.github, w.tip_github, () => api().owned_open("ticket")),
      ]),
      el("div", { className: "owned-row" }, [
        unlockBox,
        button(w.unlock, w.tip_unlock, () => unlock(unlockBox.value)),
      ]),
      el("p", { className: "owned-note " + (kind || ""), textContent: note || "" }),
    ]);
    panel.firstChild.classList.add("owned-close");
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "true");
    panel.setAttribute("aria-labelledby", "owned-title");
    document.body.append(el("div", { id: "owned-overlay", className: "owned-overlay" }, [panel]));
  }

  function done(v) {  // just unlocked: say so, with the one button that closes the box
    view = v;
    close();
    const w = v.words;
    const panel = el("div", { className: "owned-panel" }, [
      el("h2", { id: "owned-title", textContent: w.unlocked }),
      el("div", { className: "owned-row" }, [button(w.close, w.tip_close, close)]),
    ]);
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-labelledby", "owned-title");
    document.body.append(el("div", { id: "owned-overlay", className: "owned-overlay" }, [panel]));
  }

  async function recheck() {
    const v = await api().owned_check();
    if (v.ok) { view = v; close(); } else show(v);
  }

  async function unlock(code) {
    const v = await api().owned_unlock(code || "");
    if (v.ok) done(v); else show(v, v.bad_code ? v.words.bad_code : "", "bad");
  }

  async function atStart() {
    try {
      const v = await api().owned_check();
      view = null;
      if (!v.ok) show(v);
    } catch { /* an older back end or the preview: no check */ }
  }

  window.Owned = { check: atStart, show, close };
  if (api()) atStart();
  else window.addEventListener("pywebviewready", atStart, { once: true });
})();
