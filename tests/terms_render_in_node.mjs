// Runs the Settings "Terms, credits and licences" section's own drawing code (ui/app.js, as it is) in Node with a small
// stand-in for the page: the Launcher's renderTerms (the page's state.terms, answered or not yet) and the Studio's terms
// section render (its terms_info call answered by the scenario). For tests/test_terms_settings.py.
//
//   node terms_render_in_node.mjs <app.js> <launcher|studio> <scenario.json>
//
// scenario: {"words": {key: text}, "info": {terms_info's answer} | null (the Launcher: not answered yet)}
// prints one JSON line: {element id: its text}
import fs from "node:fs";
import vm from "node:vm";

const [file, kind, scenarioFile] = process.argv.slice(2);
const src = fs.readFileSync(file, "utf8");
const scenario = JSON.parse(fs.readFileSync(scenarioFile, "utf8"));

const els = {};
const $ = (id) => (els[id] ||= { id, textContent: "", title: "" });
const fill = (s, v) => String(s).replace(/\{(\w+)\}/g, (m, k) => (k in v ? v[k] : m));
const text = (el, s) => { el.textContent = s; };
const errorText = (e) => String(e && e.message || e);
const state = { words: scenario.words, settings: true };
const ctx = { state, $, fill, fillText: fill, text, errorText, api: () => ({ terms_info: async () => scenario.info }) };
vm.createContext(ctx);

if (kind === "launcher") {
  const start = src.indexOf("function renderTerms() {");
  const end = src.indexOf("\n}\n", start);
  if (start < 0 || end < 0) throw new Error("renderTerms not found");
  vm.runInContext(src.slice(start, end + 2), ctx);
  if (scenario.info) ctx.state.terms = scenario.info;
  vm.runInContext("renderTerms()", ctx);
} else {
  const start = src.indexOf('{ id: "terms", async render() {');
  const end = src.indexOf("\n  } },", start);
  if (start < 0 || end < 0) throw new Error("terms section not found");
  const section = vm.runInContext("(" + src.slice(start, end + 6) + ")", ctx);
  await section.render();
}
const out = {};
for (const [id, el] of Object.entries(els)) out[id] = el.textContent;
process.stdout.write(JSON.stringify(out) + "\n");
