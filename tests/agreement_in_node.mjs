// The shared agreement screen's own code (src/rusemod/sharedui/agreement.js, as it is) run in Node with a small
// stand-in for the browser's document, every call it makes answered live by the test (one JSON line each way on stdin
// and stdout), as an app's window answers them (pywebview: a call's answer, or its error thrown on the page). For
// tests/test_title_opt_in.py: R.U.S.E. 2.0's title box on the screen.
//
//   node agreement_in_node.mjs <agreement.js> <scenario.json>
//
// scenario: {"cases": [{"name", "words": {key: text}, "tick": bool, "accept": n, "username": text}]}; each case on a
// fresh page (the screen's code loaded again, its markup made from the HTML it writes):
//   -> {"id", "begin": name}                 the test gets the case's app ready (answered {"ok": true})
//   Agreement.open({api, words, fairOn: true}); the page left to finish; what the screen shows read ("shown"); the box
//   ticked when the case says so; Accept clicked ("accept" times, 1 if not said; the page left to finish after each);
//   when the username is asked, it typed and Save clicked
//   -> {"id", "call": name, "args": [...]}   each call the screen makes, answered {"value"} or {"error": its message}
//   -> {"id", "end": name, "out": {"shown", "calls": [names], "finished": open() returned, "agree_shown",
//      "username_shown", "box_after": the box's tick at the end, "error"?}}
//   -> {"id", "done": true}
import fs from "node:fs";
import readline from "node:readline";
import vm from "node:vm";
import { Console } from "node:console";

const [screenFile, scenarioFile] = process.argv.slice(2);
const scenario = JSON.parse(fs.readFileSync(scenarioFile, "utf8"));
const code = fs.readFileSync(screenFile, "utf8");

// --- talking to the test: stdout carries only these lines (the page's own console writes to stderr) ---
const pending = new Map();
let nextId = 1;
readline.createInterface({ input: process.stdin }).on("line", (line) => {
  const m = JSON.parse(line);
  const done = pending.get(m.id);
  if (done) { pending.delete(m.id); done(m); }
});
const ask = (msg) => new Promise((done) => {
  const id = nextId++;
  pending.set(id, done);
  process.stdout.write(JSON.stringify({ id, ...msg }) + "\n");
});
// the page left to finish: no call waiting for its answer, and nothing more done, a few times over
const settle = async () => {
  for (let quiet = 0; quiet < 6;) {
    await new Promise((r) => setTimeout(r, 4));
    quiet = pending.size ? 0 : quiet + 1;
  }
};

// --- the document's stand-in: the elements the screen's HTML names by id, with their attributes, classes, the
// properties the screen sets and their listeners; an id the HTML doesn't have isn't there (null), as in a browser ---
class Elem {
  constructor(tag, attrs) {
    this.tagName = tag.toUpperCase();
    this.attrs = attrs;
    this.id = attrs.id || "";
    this._cls = new Set((attrs.class || "").split(/\s+/).filter(Boolean));
    this.type = attrs.type || "";
    this.checked = "checked" in attrs;   // (as the markup has it: ticked only when it says checked)
    this.disabled = "disabled" in attrs;
    this.title = attrs.title || "";
    this.value = attrs.value || "";
    this.placeholder = attrs.placeholder || "";
    this.textContent = "";
    this.listeners = {};
    this.childNodes = [];
  }
  get className() { return [...this._cls].join(" "); }
  set className(v) { this._cls = new Set(String(v ?? "").split(/\s+/).filter(Boolean)); }
  get classList() {
    const n = this;
    return {
      add: (...c) => c.forEach((x) => n._cls.add(x)),
      remove: (...c) => c.forEach((x) => n._cls.delete(x)),
      toggle: (c, on) => { const want = on === undefined ? !n._cls.has(c) : Boolean(on); if (want) n._cls.add(c); else n._cls.delete(c); return want; },
      contains: (c) => n._cls.has(c),
    };
  }
  set innerHTML(html) {   // the markup the screen writes: each tag with an id becomes its element
    this.childNodes = [];
    for (const [, tag, rest] of String(html).matchAll(/<([a-z][a-z0-9]*)\b([^>]*)>/gi)) {
      const attrs = {};
      for (const [, name, value] of rest.matchAll(/([a-z][\w-]*)(?:\s*=\s*"([^"]*)")?/gi)) attrs[name.toLowerCase()] = value ?? "";
      if (!attrs.id) continue;
      const e = new Elem(tag, attrs);
      byId.set(e.id, e);
      this.childNodes.push(e);
    }
  }
  append(...cs) { this.childNodes.push(...cs); }
  appendChild(c) { this.childNodes.push(c); return c; }
  addEventListener(t, f) { (this.listeners[t] ||= []).push(f); }
  removeEventListener(t, f) { this.listeners[t] = (this.listeners[t] || []).filter((x) => x !== f); }
  click() {
    if (this.disabled) return;
    for (const f of [...(this.listeners.click || [])]) f({ type: "click", target: this, preventDefault() {} });
  }
  focus() {}
}

let byId = new Map();
const shown = (id) => { const e = byId.get(id); return e ? !e._cls.has("agree-hidden") : null; };

for (const c of scenario.cases) {
  await ask({ begin: c.name });
  byId = new Map();
  const document = {
    createElement: (tag) => new Elem(tag, {}),
    getElementById: (id) => byId.get(id) || null,
    head: new Elem("head", {}),
    body: new Elem("body", {}),
  };
  const ctx = { document, console: new Console({ stdout: process.stderr, stderr: process.stderr }), Promise, JSON,
    setTimeout, clearTimeout, String, Boolean, Object, Array, Error };
  ctx.window = ctx;
  vm.createContext(ctx);
  const calls = [];
  const api = new Proxy({}, {
    get: (_t, name) => {
      if (name === "then" || typeof name !== "string") return undefined;
      return async (...args) => {
        calls.push(name);
        const r = await ask({ call: name, args });
        if ("error" in r) throw new Error(r.error);
        return r.value;
      };
    },
  });
  const out = { calls };
  try {
    vm.runInContext(code, ctx, { filename: "agreement.js" });
    let finished = false;
    const opened = ctx.window.Agreement.open({ api, words: c.words, fairOn: true });
    opened.then(() => { finished = true; }, (err) => { out.error = String((err && err.stack) || err); });
    await settle();
    const box = byId.get("agree-ruse20"), row = byId.get("agree-ruse20-row"), label = byId.get("agree-ruse20-label");
    out.shown = {
      agree: shown("agree"),
      box: box ? { type: box.type, checked: box.checked, disabled: box.disabled, title: box.title } : null,
      row_title: row ? row.title : null,
      row_shown: row ? !row._cls.has("agree-hidden") : null,
      label: label ? label.textContent : null,
      accept: byId.get("agree-accept") ? byId.get("agree-accept").textContent : null,
    };
    if (c.tick && box) box.checked = true;
    for (let k = 0; k < (c.accept || 1); k++) {
      byId.get("agree-accept").click();
      await settle();
    }
    if (shown("username")) {
      byId.get("username-name").value = c.username || "Tester";
      byId.get("username-save").click();
      await settle();
    }
    Object.assign(out, { finished, agree_shown: shown("agree"), username_shown: shown("username"),
      box_after: box ? box.checked : null });
  } catch (err) {
    out.error = String((err && err.stack) || err);
  }
  await ask({ end: c.name, out });
}
await ask({ done: true });
process.exit(0);
