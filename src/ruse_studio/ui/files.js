// The Files tab (StudioApi.files_packs / files_list / files_preview / files_export, rusemod.packfiles; LittleGroove's
// Raw / Asset Editor's Browse / Files): every file of the game's packs, and of the packs stored inside them, listed by
// path, shown as what it is (a picture, a text table, a mission script, a summary of a data file...) and saved out.
// Read only: mods change the game through the other tabs. Uses app.js's $, el, fill, problem and api.
(function () {
  "use strict";
  const F = { words: {}, packs: null, pack: null, nested: [], find: "", list: null, picked: null, ask: 0, shown: 0 };
  const W = () => F.words;
  const PACK_WORD = { gameplay: "files_pack_gameplay", gameplay_fixed: "files_pack_gameplay_fixed",
    scripts: "files_pack_scripts", maps: "files_pack_maps", texts: "files_pack_texts", common: "files_pack_common" };
  const KINDS = ["ndf", "texture", "image", "table", "script", "text", "pack", "binary", "picture", "scenario", "bytes"];
  const kindWord = (k) => W()["files_kind_" + (KINDS.includes(k) ? k : "binary")] || k;
  const size = (n) => n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : n >= 1024 ? `${Math.round(n / 1024)} KB` : `${n} B`;
  const tail = (path) => path.split("\\").pop();

  function packLabel(p) {
    return p.map ? fill(W().files_pack_map, { file: p.file }) : `${W()[PACK_WORD[p.id]] || p.id} · ${p.file}`;
  }

  function renderTexts() {
    const w = W();
    $("files-intro").textContent = w.files_intro;
    $("files-pack-label").textContent = w.files_pack_label;
    $("files-pack").title = w.tip_files_pack;
    $("files-find-label").textContent = w.files_find_label;
    $("files-find").placeholder = w.files_find_hint;
    $("files-find").title = w.tip_files_find;
    if (!F.picked) $("files-detail").replaceChildren(el("p", { className: "muted", textContent: w.files_pick }));
  }

  function renderPacks() {
    const pick = $("files-pack");
    pick.replaceChildren(...F.packs.map((p) => el("option", { value: p.id, textContent: `${packLabel(p)} (${size(p.size)})` })));
    if (F.pack) pick.value = F.pack;
  }

  async function load() {
    const ask = ++F.ask;
    $("files-count").textContent = W().files_loading;
    let res;
    try { res = await api().files_list(F.pack, F.nested, F.find); } catch (err) { problem(err); return; }
    if (ask !== F.ask) return;  // another pack or search was asked for meanwhile
    F.list = res;
    renderList();
  }

  function renderNested() {
    const box = $("files-nested"), w = W();
    box.replaceChildren();
    if (!F.nested.length) return;
    const back = el("button", { type: "button", className: "link", textContent: w.files_back_out, title: w.tip_files_back_out });
    back.addEventListener("click", backOut);
    box.append(el("div", { className: "muted", textContent: fill(w.files_in_pack, { path: F.nested.map(tail).join(" › ") }) }), back);
  }

  function renderList() {
    const w = W(), l = F.list;
    renderNested();
    if (!l) return;
    $("files-count").textContent = fill(w.files_count, { n: l.matching, total: l.total })
      + (l.matching > l.files.length ? " " + fill(w.files_more, { n: l.files.length }) : "");
    $("files-list").replaceChildren(...l.files.map((f) => {
      const b = el("button", { type: "button", title: `${f.path}\n${w.tip_files_row}` },
        el("span", { className: "name", textContent: tail(f.path) }),
        el("span", { className: "meta", textContent: `${kindWord(f.kind)} · ${size(f.size)} · ${f.path}` }));
      b.dataset.path = f.path;
      b.setAttribute("aria-current", String(f.path === F.picked));
      b.addEventListener("click", () => showFile(f.path));
      return el("li", {}, b);
    }));
  }

  async function showFile(path) {
    F.picked = path;
    for (const b of $("files-list").querySelectorAll("button")) b.setAttribute("aria-current", String(b.dataset.path === path));
    const ask = ++F.shown;
    $("files-detail").replaceChildren(el("h1", { textContent: tail(path) }), el("p", { className: "muted", textContent: W().files_loading }));
    let p;
    try { p = await api().files_preview(F.pack, F.nested, path); } catch (err) { problem(err); return; }
    if (ask === F.shown) renderDetail(p);
  }

  function rowsTable(rows) {
    return el("table", { className: "values-table" }, ...rows.map(([k, v]) => el("tr", {}, el("th", { textContent: k }), el("td", { textContent: v }))));
  }

  function renderDetail(p) {
    const w = W();
    const save = el("button", { type: "button", textContent: w.files_save, title: w.tip_files_save });
    save.addEventListener("click", async () => {
      try {
        const res = await api().files_export(F.pack, F.nested, p.path);
        if (res.saved) say(fill(w.files_saved, { path: res.saved }), "ok");
      } catch (err) { problem(err); }
    });
    const parts = [el("h1", { textContent: tail(p.path) }),
      el("div", { className: "address" }, el("code", { textContent: p.path }), save),
      el("div", { className: "meta", textContent: `${kindWord(p.kind)} · ${size(p.size)}` })];
    if (p.why) parts.push(el("p", { className: "notice", textContent: fill(w.files_not_read, { why: p.why }) }));
    const body = el("div", { className: "group" });
    if (p.kind === "ndf") {
      body.append(rowsTable([[w.files_ndf_objects, String(p.objects)], [w.files_ndf_classes, String(p.classes)],
        [w.files_ndf_props, String(p.props)], [w.files_ndf_packed, p.packed ? w.values_yes : w.values_no]]),
      el("h2", { textContent: w.files_ndf_top }), rowsTable(p.top.map(([c, n]) => [c, String(n)])));
    } else if (p.kind === "picture") {
      body.append(el("img", { className: "files-picture", src: p.picture, alt: tail(p.path) }),
        el("p", { className: "muted small", textContent: fill(w.files_picture_size,
          { w: p.width, h: p.height, fw: p.full[0], fh: p.full[1], format: p.format }) }));
    } else if (p.kind === "table") {
      body.append(el("p", { className: "muted small", textContent: fill(w.files_table_count, { n: p.count, shown: p.rows.length }) }),
        rowsTable(p.rows));
    } else if (p.kind === "scenario") {
      body.append(rowsTable([[w.files_scenario_zones, String(p.zones)], ...p.items.map(([k, n]) => [k, String(n)])]));
    } else if (p.kind === "script" || p.kind === "text") {
      body.append(el("pre", { className: "files-text", textContent: p.text }));
    } else if (p.kind === "pack") {
      const inside = el("button", { type: "button", className: "primary", textContent: w.files_open_pack, title: w.tip_files_open_pack });
      inside.addEventListener("click", () => openNested(p.path));
      body.append(el("p", { textContent: fill(w.files_inside, { n: p.files }) }), inside);
    } else {
      body.append(el("pre", { className: "files-text", textContent: (p.lines || []).join("\n") }));
      if (p.more) body.append(el("p", { className: "muted small", textContent: fill(w.files_bytes_more, { n: p.more }) }));
    }
    parts.push(body, el("p", { className: "muted small", textContent: w.files_read_only }));
    $("files-detail").replaceChildren(...parts);
  }

  function openNested(path) {
    F.nested.push(path);
    resetList();
  }

  function backOut() {
    F.nested.pop();
    resetList();
  }

  function resetList() {
    F.list = null;
    F.picked = null;
    F.find = "";
    $("files-find").value = "";
    $("files-list").replaceChildren();
    renderTexts();
    load();
  }

  async function open(words) {
    F.words = words;
    renderTexts();
    if (!F.packs) {
      try { F.packs = (await api().files_packs()).packs; } catch (err) { problem(err); return; }
      if (!F.pack && F.packs.length) F.pack = F.packs[0].id;
    }
    renderPacks();
    if (!F.list) await load(); else renderList();
  }

  function wire() {
    $("files-pack").addEventListener("change", (e) => { F.pack = e.target.value; F.nested = []; resetList(); });
    let timer = null;
    $("files-find").addEventListener("input", (e) => {
      clearTimeout(timer);
      timer = setTimeout(() => { F.find = e.target.value; load(); }, 250);
    });
  }

  window.FilesView = {
    open,
    setWords(words) { F.words = words; renderTexts(); if (F.packs) renderPacks(); if (F.list) renderList(); },
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire); else wire();
})();
