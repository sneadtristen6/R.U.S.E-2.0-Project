// The Settings title switch's own code in both apps' pages, cut out of each page as it is and run in Node with a
// small stand-in for the few elements it uses: the Launcher's loadTitle, renderTitle and changeTitle
// (src/ruse_launcher/ui/app.js), the Studio's SETTINGS entry "title" (src/ruse_studio/ui/app.js). For
// tests/test_title_opt_in.py: the switch is drawn ticked only when the app's answer says on, and a tick is kept.
//
//   node title_switch_in_node.mjs <launcher app.js> <studio app.js> <cases.json>
//
// cases: [{"app": "launcher" or "studio", "words": {key: text}, "answer": game_title()'s answer, or null for an
// error, "change": the player ticks it (true) or unticks it (false) after it's drawn, "set_answer": set_game_title()'s
// answer (else {"ruse20": what was asked})}]. Prints one JSON line, a result per case in order: {"checked",
// "disabled", "note", "note_class", "calls": [[name, args]], "after": the same once changed, "problems": [...]} or
// {"error"}. A piece of code that can't be found or cut (its start moved, a template literal in it) is an error.
import fs from "node:fs";
import vm from "node:vm";

const [launcherFile, studioFile, casesFile] = process.argv.slice(2);
const pages = { launcher: fs.readFileSync(launcherFile, "utf8"), studio: fs.readFileSync(studioFile, "utf8") };
const cases = JSON.parse(fs.readFileSync(casesFile, "utf8"));

// the code from `start` to the brace that closes the first "{" at or after it: strings and comments skipped
function cut(src, start) {
  const at = src.indexOf(start);
  if (at < 0 || src.indexOf(start, at + 1) >= 0) throw new Error(`not found once: ${start}`);
  let i = src.indexOf("{", at), depth = 0;
  for (; i < src.length; i++) {
    const ch = src[i];
    if (ch === "`") throw new Error(`a template literal in ${start}: not cut`);
    if (ch === '"' || ch === "'") {
      for (i++; i < src.length && src[i] !== ch; i++) if (src[i] === "\\") i++;
    } else if (ch === "/" && src[i + 1] === "/") {
      i = src.indexOf("\n", i);
    } else if (ch === "/" && src[i + 1] === "*") {
      i = src.indexOf("*/", i) + 1;
    } else if (ch === "{") {
      depth++;
    } else if (ch === "}" && --depth === 0) {
      return src.slice(at, i + 1);
    }
  }
  throw new Error(`no end: ${start}`);
}

function element() {
  return { checked: false, disabled: false, title: "", textContent: "", className: "", onchange: null };
}

async function run(c) {
  const els = new Map(), calls = [], problems = [];
  const $ = (id) => { if (!els.has(id)) els.set(id, element()); return els.get(id); };
  const api = () => ({
    game_title: async () => {
      calls.push(["game_title", []]);
      if (c.answer === null) throw new Error("game_title failed (the test's)");
      return c.answer;
    },
    set_game_title: async (on) => {
      calls.push(["set_game_title", [on]]);
      return c.set_answer || { ruse20: Boolean(on) };
    },
  });
  const ctx = { $, api, Promise, JSON, String, Boolean, Object, Error,
    text: (node, value) => { node.textContent = value || ""; },
    errorText: (err) => (err && err.message) || String(err),
    problem: (err) => { problems.push((err && err.message) || String(err)); } };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  const box = $("title-gold"), note = $("set-title-note");
  const seen = () => ({ checked: box.checked, disabled: box.disabled, note: note.textContent,
    note_class: note.className });
  let out;
  if (c.app === "launcher") {
    ctx.state = { words: c.words, settings: true };
    for (const start of ["async function loadTitle() {", "function renderTitle() {", "async function changeTitle() {"]) {
      vm.runInContext(cut(pages.launcher, start), ctx, { filename: "launcher app.js" });
    }
    await ctx.loadTitle();
    out = seen();
    if (c.change !== undefined) {
      box.checked = c.change;
      await ctx.changeTitle();
      out.after = seen();
    }
  } else {
    ctx.state = { words: c.words };
    vm.runInContext(`globalThis.entry = (${cut(pages.studio, '{ id: "title", async render() {')});`, ctx,
      { filename: "studio app.js" });
    try { await ctx.entry.render(); } catch (err) { problems.push(`render: ${(err && err.message) || err}`); }
    out = seen();
    if (c.change !== undefined && box.onchange) {
      box.checked = c.change;
      await box.onchange();
      out.after = seen();
    }
  }
  return { ...out, calls, problems };
}

const results = [];
for (const c of cases) {
  try { results.push(await run(c)); } catch (err) { results.push({ error: String((err && err.stack) || err) }); }
}
process.stdout.write(JSON.stringify(results) + "\n");
