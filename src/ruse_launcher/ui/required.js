// A required update (rusemod.update: a release whose notes mark it required; the owner, 2026-10-30: "a box it can't
// skip ... it should update by itself without asking"): a box over the whole window with no way to close it, while
// the app installs the update by itself (the app's installUpdate) and starts again; Play and Test in game wait for it
// (rusemod.play.Starter.required). Without the internet it says so, with Try again. The same file in both apps.
// window.requiredUpdate({u, w, app, note, updating, again}) from the app's renderUpdate: u is update_check's answer.
(() => {
  "use strict";
  const STYLE = `
.required-overlay { position: fixed; inset: 0; z-index: 1100; display: flex; align-items: center; justify-content: center;
  background: rgba(4, 10, 20, 0.86); padding: 16px; }
.required-panel { background: var(--panel); color: var(--text); border: 1px solid var(--line); border-radius: var(--radius);
  max-width: 560px; width: 100%; padding: 18px 20px; }
.required-panel h2 { margin: 0 0 10px; font-size: 1.15em; }
.required-panel p { margin: 8px 0; line-height: 1.4; }
.required-note { color: var(--muted); }`;

  function el(tag, props, kids) {
    const node = document.createElement(tag);
    Object.assign(node, props || {});
    for (const kid of kids || []) node.append(kid);
    return node;
  }

  function fill(text, values) {
    return String(text || "").replace(/\{(\w+)\}/g, (all, key) => (key in values ? String(values[key]) : all));
  }

  // nothing closes it: Escape and the keys meant for the page under it stop here (its own button still takes keys)
  function hold(event) {
    const box = document.getElementById("required-overlay");
    if (box && !box.contains(event.target)) { event.stopPropagation(); event.preventDefault(); }
    else if (box && event.key === "Escape") event.preventDefault();
  }
  document.addEventListener("keydown", hold, true);

  window.requiredUpdate = function (v) {
    const u = v && v.u, old = document.getElementById("required-overlay");
    if (!u || !u.required) { if (old) old.remove(); return; }
    if (!document.getElementById("required-style")) document.head.append(el("style", { id: "required-style", textContent: STYLE }));
    const w = v.w || {}, values = { app: v.app, version: u.version || "", why: u.error || "" };
    const text = u.offline ? fill(w.update_required_offline, values)
      : u.installed === false ? fill(w.update_required_repo, values) : fill(w.update_required_text, values);
    const kids = [el("h2", { textContent: w.update_required_title || "" }), el("p", { textContent: text })];
    if (v.note && !u.offline) kids.push(el("p", { className: "required-note", textContent: v.note }));
    if (u.offline || (!v.updating && u.installed !== false)) {
      kids.push(el("button", { type: "button", className: "small", textContent: w.update_required_again || "",
        title: w.tip_update_required_again || "", onclick: () => v.again && v.again() }));
    }
    const box = el("div", { id: "required-overlay", className: "required-overlay" },
      [el("div", { className: "required-panel", role: "alertdialog", ariaModal: "true" }, kids)]);
    if (old) old.replaceWith(box); else document.body.append(box);
  };
})();
