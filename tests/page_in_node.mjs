// The Studio's own page code (ui/app.js and ui/squad.js, as they are) run in Node with a small stand-in for the
// browser's document, its calls answered live by the Studio itself (the test that starts this: one JSON line each way
// on stdin and stdout), in each language the test gives: what the page then shows. For tests/test_recheck_notes.py
// (what a Bring back couldn't keep, shown on the page in the modder's language).
//
//   node page_in_node.mjs <the page's ui folder> <scenario.json>
//
// scenario: {"langs": [...], "words": {lang: {key: text}}, "cases": [{"name", "page", "unit": {"address", "name"},
//   "click": {"text": words key, "title": words key, "index": n}}]}; for each language and case, in turn:
//   -> {"id", "begin": case, "lang"}   the test makes the case's mod for that language (answered {"ok": true})
//   page "look": the unit page's Look and moves section (app.js lookMovesBox), its Model and Its soldiers rows' More
//     open, as the modder has them to click there;
//   page "squad": the squad page's section (squad.js SquadView.section) on the squad's squad_info, as showUnit draws it;
//   then the button whose words are click.text (with click.title's tooltip when one has it, else the click.index'th, 0
//   the first) clicked, the page left to finish, and on the squad page More options opened;
//   -> {"id", "call": name, "args": [...]}   each call the page makes, answered {"value"} or {"error": its message}
//   -> {"id", "end": case, "lang", "out": {"tree": the section, "status": the pop-up area, "body": the page's body (the
//      section isn't in it), "said": [[text, kind]] (pop-ups and alerts), "calls": [names], "error": when it threw}}
//   -> {"id", "done": true}; a tree is [tag, class, hidden, [children]] for an element, a string for text.
import fs from "node:fs";
import readline from "node:readline";
import vm from "node:vm";
import { Console } from "node:console";

const [uiFolder, scenarioFile] = process.argv.slice(2);
const scenario = JSON.parse(fs.readFileSync(scenarioFile, "utf8"));

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

// --- the document's stand-in: elements with their children, classes, attributes and listeners ---
class TextNode {
  constructor(t) { this.data = String(t); this.parentNode = null; this.nodeType = 3; }
  get textContent() { return this.data; }
  set textContent(v) { this.data = String(v ?? ""); }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
}

function simple(node, sel) {   // one compound selector: tag, #id, .class, [attr] or [attr="v"]; pseudo-classes ignored
  const s = sel.replace(/:[\w-]+(\([^)]*\))?/g, "");
  const m = /^([a-z0-9*]*)((?:[#.][\w-]+|\[[^\]]+\])*)$/i.exec(s.trim());
  if (!m || !(node instanceof Elem)) return false;
  if (m[1] && m[1] !== "*" && node.tagName !== m[1].toUpperCase()) return false;
  for (const part of m[2].match(/[#.][\w-]+|\[[^\]]+\]/g) || []) {
    if (part[0] === ".") { if (!node._cls.has(part.slice(1))) return false; }
    else if (part[0] === "#") { if (node.id !== part.slice(1)) return false; }
    else {
      const a = /^\[([\w-]+)(?:=["']?([^"'\]]*)["']?)?\]$/.exec(part);
      if (!a) return false;
      const v = a[1] in node.attrs ? node.attrs[a[1]] : node[a[1]];
      if (v === undefined || v === null || v === false) return false;
      if (a[2] !== undefined && String(v) !== a[2]) return false;
    }
  }
  return true;
}

function matches(node, selector) {   // a selector list, each a chain of compound selectors (descendant only)
  return selector.split(",").some((one) => {
    const chain = one.trim().split(/\s+/).filter((x) => x !== ">");
    if (!chain.length || !simple(node, chain[chain.length - 1])) return false;
    let at = node.parentNode, k = chain.length - 2;
    while (k >= 0 && at) {
      if (simple(at, chain[k])) k--;
      at = at.parentNode;
    }
    return k < 0;
  });
}

function under(root, selector) {
  const out = [];
  const walk = (n) => {
    for (const c of n.childNodes) {
      if (c instanceof Elem) {
        if (matches(c, selector)) out.push(c);
        walk(c);
      }
    }
  };
  walk(root);
  return out;
}

class Elem {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.nodeName = this.tagName;
    this.nodeType = 1;
    this.childNodes = [];
    this.parentNode = null;
    this.listeners = {};
    this.attrs = {};
    this.dataset = {};
    this.style = { setProperty() {}, removeProperty() {}, getPropertyValue() { return ""; } };
    this._cls = new Set();
    this._html = "";
    this.id = "";
    this.hidden = false;
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
      replace: (a, b) => { if (!n._cls.has(a)) return false; n._cls.delete(a); n._cls.add(b); return true; },
      get length() { return n._cls.size; },
      [Symbol.iterator]: () => n._cls[Symbol.iterator](),
    };
  }
  get children() { return this.childNodes.filter((c) => c instanceof Elem); }
  get firstChild() { return this.childNodes[0] || null; }
  get lastChild() { return this.childNodes[this.childNodes.length - 1] || null; }
  get firstElementChild() { return this.children[0] || null; }
  get lastElementChild() { const c = this.children; return c[c.length - 1] || null; }
  get parentElement() { return this.parentNode instanceof Elem ? this.parentNode : null; }
  get childElementCount() { return this.children.length; }
  _sibling(step, elementsOnly) {
    if (!this.parentNode) return null;
    const list = elementsOnly ? this.parentNode.children : this.parentNode.childNodes;
    return list[list.indexOf(this) + step] || null;
  }
  get nextSibling() { return this._sibling(1, false); }
  get previousSibling() { return this._sibling(-1, false); }
  get nextElementSibling() { return this._sibling(1, true); }
  get previousElementSibling() { return this._sibling(-1, true); }
  get textContent() { return this.childNodes.map((c) => c.textContent).join(""); }
  set textContent(v) { this._drop(); this._html = ""; const t = String(v ?? ""); if (t) this._add(new TextNode(t)); }
  get innerText() { return this.textContent; }
  set innerText(v) { this.textContent = v; }
  get innerHTML() { return this._html; }
  set innerHTML(v) { this._drop(); this._html = String(v ?? ""); }   // (the page's own drawings: no text in them)
  get isConnected() { return true; }
  get offsetHeight() { return 0; }
  get offsetWidth() { return 0; }
  get clientHeight() { return 0; }
  get clientWidth() { return 0; }
  get scrollHeight() { return 0; }
  get ownerDocument() { return document; }
  _drop() { for (const c of this.childNodes) c.parentNode = null; this.childNodes = []; }
  _node(c) {
    if (c instanceof Elem && c.tagName === "#FRAGMENT") { const kids = c.childNodes.slice(); c._drop(); return kids; }
    if (c instanceof Elem || c instanceof TextNode) return [c];
    return [new TextNode(c)];
  }
  _add(c, at = this.childNodes.length) {
    for (const k of this._node(c)) {
      if (k.parentNode) k.parentNode.removeChild(k);
      k.parentNode = this;
      this.childNodes.splice(at++, 0, k);
    }
  }
  append(...cs) { for (const c of cs) this._add(c); }
  prepend(...cs) { let at = 0; for (const c of cs) { const before = this.childNodes.length; this._add(c, at); at += this.childNodes.length - before; } }
  appendChild(c) { this._add(c); return c; }
  insertBefore(c, ref) { const i = ref ? this.childNodes.indexOf(ref) : -1; this._add(c, i < 0 ? this.childNodes.length : i); return c; }
  removeChild(c) { const i = this.childNodes.indexOf(c); if (i >= 0) { this.childNodes.splice(i, 1); c.parentNode = null; } return c; }
  replaceChild(n, old) { const i = this.childNodes.indexOf(old); if (i >= 0) { this.removeChild(old); this._add(n, i); } return old; }
  replaceChildren(...cs) { this._drop(); this._html = ""; this.append(...cs); }
  remove() { if (this.parentNode) this.parentNode.removeChild(this); }
  replaceWith(...cs) { const p = this.parentNode; if (!p) return; let i = p.childNodes.indexOf(this); p.removeChild(this); for (const c of cs) { const before = p.childNodes.length; p._add(c, i); i += p.childNodes.length - before; } }
  before(...cs) { const p = this.parentNode; if (!p) return; for (const c of cs) p._add(c, p.childNodes.indexOf(this)); }
  after(...cs) { const p = this.parentNode; if (!p) return; let i = p.childNodes.indexOf(this) + 1; for (const c of cs) { const before = p.childNodes.length; p._add(c, i); i += p.childNodes.length - before; } }
  insertAdjacentElement(where, n) {
    if (where === "beforebegin") this.before(n); else if (where === "afterend") this.after(n);
    else if (where === "afterbegin") this.prepend(n); else this.append(n);
    return n;
  }
  insertAdjacentText(where, t) { this.insertAdjacentElement(where, new TextNode(t)); }
  insertAdjacentHTML() {}
  cloneNode(deep) {
    const c = new Elem(this.tagName);
    Object.assign(c, this);
    c._cls = new Set(this._cls); c.attrs = { ...this.attrs }; c.listeners = {}; c.parentNode = null; c.childNodes = [];
    if (deep) for (const k of this.childNodes) c._add(k instanceof Elem ? k.cloneNode(true) : new TextNode(k.data));
    return c;
  }
  addEventListener(t, f) { (this.listeners[t] ||= []).push(f); }
  removeEventListener(t, f) { this.listeners[t] = (this.listeners[t] || []).filter((x) => x !== f); }
  dispatchEvent(e) { for (const f of this.listeners[e.type] || []) f.call(this, e); return true; }
  click() { return this.dispatchEvent({ type: "click", target: this, currentTarget: this, preventDefault() {}, stopPropagation() {} }); }
  setAttribute(k, v) { this.attrs[k] = String(v); if (k === "class") this.className = v; if (k === "id") this.id = String(v); }
  getAttribute(k) { return k === "class" ? this.className : k in this.attrs ? this.attrs[k] : null; }
  removeAttribute(k) { delete this.attrs[k]; }
  hasAttribute(k) { return k in this.attrs; }
  toggleAttribute(k, on) { const want = on === undefined ? !(k in this.attrs) : Boolean(on); if (want) this.attrs[k] = ""; else delete this.attrs[k]; return want; }
  querySelector(sel) { return under(this, sel)[0] || null; }
  querySelectorAll(sel) { return under(this, sel); }
  getElementsByTagName(tag) { return under(this, tag); }
  getElementsByClassName(c) { return under(this, "." + c); }
  matches(sel) { return matches(this, sel); }
  closest(sel) { let n = this; while (n instanceof Elem) { if (matches(n, sel)) return n; n = n.parentNode; } return null; }
  contains(o) { let n = o; while (n) { if (n === this) return true; n = n.parentNode; } return false; }
  focus() {}
  blur() {}
  select() {}
  scrollIntoView() {}
  scrollTo() {}
  showModal() { this.open = true; }
  close() { this.open = false; }
  animate() { return { finished: Promise.resolve(), cancel() {} }; }
  getBoundingClientRect() { return { top: 0, left: 0, right: 0, bottom: 0, width: 0, height: 0, x: 0, y: 0 }; }
  getContext() { return null; }
}

const said = [];   // (what the page said in pop-ups and alerts: [text, kind])
const byId = new Map();
const body = new Elem("body");
const document = {
  createElement: (tag) => new Elem(tag),
  createElementNS: (_ns, tag) => new Elem(tag),
  createTextNode: (t) => new TextNode(t),
  createDocumentFragment: () => new Elem("#fragment"),
  getElementById: (id) => { if (!byId.has(id)) { const e = new Elem("div"); e.id = id; byId.set(id, e); } return byId.get(id); },
  querySelector: (sel) => under(body, sel)[0] || null,
  querySelectorAll: (sel) => under(body, sel),
  getElementsByTagName: () => [],
  addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; },
  execCommand() { return false; },
  documentElement: new Elem("html"),
  head: new Elem("head"),
  body,
  activeElement: null,
  readyState: "complete",
  hidden: false,
  visibilityState: "visible",
  fonts: { ready: Promise.resolve() },
};
class Observer { observe() {} disconnect() {} unobserve() {} takeRecords() { return []; } }
class HTMLElement {}
const kinds = {};
for (const name of ["HTMLInputElement", "HTMLSelectElement", "HTMLTextAreaElement", "HTMLButtonElement"]) {
  // (app.js reads an input's own value property at load)
  kinds[name] = class extends HTMLElement {};
  Object.defineProperty(kinds[name].prototype, "value", { configurable: true, enumerable: true,
    get() { return this._value ?? ""; }, set(v) { this._value = String(v); } });
}
const later = (f, ms, ...a) => { const t = setTimeout(f, ms, ...a); if (t && t.unref) t.unref(); return t; };
const ctx = {
  HTMLElement, ...kinds, Element: Elem, Node: Elem, Text: TextNode,
  document, console: new Console({ stdout: process.stderr, stderr: process.stderr }),
  URL, URLSearchParams, Promise, JSON, Math, Date, Map, Set, WeakMap, WeakSet, Intl, structuredClone,
  TextEncoder, TextDecoder, AbortController, queueMicrotask, atob, btoa, Blob,
  setTimeout: later, clearTimeout, setInterval: () => 0, clearInterval: () => {},
  requestAnimationFrame: (f) => { later(() => f(0), 0); return 0; }, cancelAnimationFrame() {},
  requestIdleCallback: (f) => { later(() => f({ timeRemaining: () => 0, didTimeout: true }), 0); return 0; },
  ResizeObserver: Observer, MutationObserver: Observer, IntersectionObserver: Observer,
  localStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
  location: { search: "", href: "http://studio/", hash: "", pathname: "/" },
  history: { replaceState() {}, pushState() {} },
  navigator: { language: "en", languages: ["en"], platform: "Win32", userAgent: "node", clipboard: { writeText: async () => {} } },
  matchMedia: () => ({ matches: false, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {} }),
  getComputedStyle: () => ({ getPropertyValue: () => "" }),
  getSelection: () => ({ removeAllRanges() {}, addRange() {}, toString: () => "" }),
  performance: { now: () => Date.now() },
  addEventListener() {}, removeEventListener() {}, dispatchEvent() { return true; },
  confirm: () => true, alert: (text) => { said.push([String(text ?? ""), "alert"]); }, prompt: () => null,
  open() { return null; }, scrollTo() {},
  devicePixelRatio: 1, innerWidth: 1600, innerHeight: 1000,
  CustomEvent: class { constructor(t, o) { this.type = t; this.detail = o && o.detail; } },
  Event: class { constructor(t) { this.type = t; } },
  Image: class { constructor() { this.onload = null; this.onerror = null; } },
};
ctx.window = ctx;
ctx.globalThis = ctx;
ctx.self = ctx;
vm.createContext(ctx);
for (const f of ["app.js", "squad.js"]) vm.runInContext(fs.readFileSync(`${uiFolder}/${f}`, "utf8"), ctx, { filename: f });
// what the page says in its pop-ups (say: app.js's cards), kept as said; the cards' area and the page's body read too
// (a card or a box put there otherwise)
ctx.say = (text, kind) => { said.push([String(text ?? ""), kind || ""]); return null; };
const state = vm.runInContext("state", ctx);
// the page left to finish: no call waiting for its answer, and nothing more done, a few times over
const settle = async () => {
  for (let quiet = 0; quiet < 6;) {
    await new Promise((r) => setTimeout(r, 4));
    quiet = pending.size ? 0 : quiet + 1;
  }
};

function tree(n) {
  if (n instanceof TextNode) return n.data;
  const hidden = n._cls.has("hidden") || n.hidden === true || n.attrs.hidden !== undefined;
  return [n.tagName, n.className, hidden, n.childNodes.map(tree)];
}

function buttonFor(root, click) {
  const w = state.words;
  const all = under(root, "button").filter((b) => b.textContent === w[click.text]);
  return all.find((b) => click.title && b.title === w[click.title]) || all[click.index || 0] || null;
}

for (const lang of scenario.langs) {
  for (const c of scenario.cases) {
    await ask({ begin: c.name, lang });
    state.words = scenario.words[lang];
    state.lang = lang;
    state.mod = "My mod";
    state.lmOpen = { model: true, soldiers: true };   // (the rows the modder opened to click there)
    state.squadMore = false;
    state.focusModel = null;
    said.length = 0;
    byId.delete("status");
    body.replaceChildren();
    const calls = [];
    ctx.window.pywebview = { api: new Proxy({}, {
      get: (_t, name) => {
        if (name === "then" || typeof name !== "string") return undefined;
        return async (...args) => {
          calls.push(name);
          const r = await ask({ call: name, args });
          if ("error" in r) throw new Error(r.error);
          return r.value;
        };
      },
    }) };
    let root = null, error;
    try {
      const unit = { address: c.unit.address, name: c.unit.name, editable: true, can_copy: true };
      if (c.page === "look") root = vm.runInContext("lookMovesBox", ctx)(unit, null, null, false);
      else if (c.page === "squad") {
        const first = await ctx.window.SquadView.infoOf(unit.address);
        if (!first || first.error) throw new Error(`no squad card: ${first && first.error}`);
        root = ctx.window.SquadView.section(unit, first, { view: null, looks: null, startNew: null, fresh: false });
      } else throw new Error(`no page called ${c.page}`);
      await settle();
      const b = buttonFor(root, c.click);
      if (!b) throw new Error(`no button "${state.words[c.click.text]}" on the page`);
      if (b.disabled) throw new Error(`the button "${state.words[c.click.text]}" can't be clicked (disabled)`);
      b.click();
      await settle();
      const toggle = root.querySelector(".squad-more-toggle");
      if (toggle && toggle.getAttribute("aria-expanded") !== "true") { toggle.click(); await settle(); }   // More options
    } catch (err) {
      error = String((err && err.stack) || err);
    }
    await ask({ end: c.name, lang, out: { tree: root ? tree(root) : null, status: tree(document.getElementById("status")),
      body: tree(body), said: said.slice(), calls, ...(error ? { error } : {}) } });
  }
}
await ask({ done: true });
process.exit(0);
