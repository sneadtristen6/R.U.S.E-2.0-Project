// The Nations tab (StudioApi.nations_view / nation_flag_set / nation_reset, rusemod.nations): one of the game's seven
// nations given a new name and flag in the current mod, China in Italy's place say (the owner, 2026-10-08: "build the
// replace-a-nation feature for this patch"). Its name in the lobby and its army's name are changed in every language
// with All values' words box (app.js wordsPanel); its flag is a picture of the modder's (any picture the window can
// read: PNG, JPG, WebP...) fitted here to the flag's size, shone like the game's flags, its round shape kept the game's.
// Its units: the Units tab with that nation picked (New unit puts a unit in its build menus); what they say: each
// unit's page (Voice). Seen in the game (2026-10-08, Italy made China). Uses app.js's $, el, fill, say, problem, api,
// state, wordsPanel,
// showView, renderChips and refreshList.
(function () {
  "use strict";
  const N = { words: {}, lang: "base", data: null, open: null };
  const W = () => N.words;

  // the words for nation x in the Studio's language (the game's code names: English), the mod's when it has its own
  function inLang(list) {
    const lang = N.lang === "base" ? "us" : N.lang;
    const x = (list || []).find((y) => y.lang === lang) || (list || []).find((y) => y.lang === "us") || {};
    return { now: x.mine ?? x.game ?? "", game: x.game ?? "", mine: x.mine !== null && x.mine !== undefined && x.mine !== x.game };
  }

  async function render() {
    const w = W();
    $("nations-title").textContent = w.nations_title;
    $("nations-help").textContent = w.nations_help;
    $("nations-lobby").textContent = w.nations_lobby_note;
    let data;
    try { data = await api().nations_view(); } catch (err) { problem(err); return; }
    if (!$("nations-view") || $("nations-view").classList.contains("hidden")) return;  // another tab meanwhile
    N.data = data;
    $("nations-nomod").textContent = data.mod ? "" : w.no_mod;
    $("nations-nomod").classList.toggle("hidden", data.mod);
    $("nations-list").replaceChildren(...data.nations.map(card));
  }

  function flagImage(url, label, big) {
    const img = el("img", { src: url, alt: label, title: label, className: big ? "nation-flag big" : "nation-flag" });
    img.width = img.height = big ? 84 : 42;
    return img;
  }

  function card(x) {
    const w = W(), name = inLang(x.name), army = x.army ? inLang(x.army) : null;
    const changed = name.mine || (army && army.mine) || (x.flag && x.flag.own);
    const head = el("div", { className: "nation-head" },
      x.flag ? flagImage(x.flag.url, fill(w.nations_flag_of, { nation: name.now }), false) : el("span", { className: "nation-flag" }),
      el("div", { className: "nation-names" },
        el("strong", { textContent: name.now }),
        ...(name.mine ? [el("span", { className: "muted small", textContent: " " + fill(w.nations_was, { nation: name.game }) })] : []),
        ...(army ? [el("div", { className: "muted small", textContent: army.now })] : []),
        el("div", { className: "muted small", textContent: fill(w.nations_units_count, { n: x.units }) })));
    const toggle = el("button", { type: "button", className: "small", textContent: N.open === x.nation ? w.nations_close : w.nations_change,
      title: fill(w.tip_nations_change, { nation: name.now }) });
    toggle.addEventListener("click", () => { N.open = N.open === x.nation ? null : x.nation; render(); });
    head.append(toggle);
    const box = el("div", { className: "nation" + (changed ? " changed" : "") }, head);
    if (N.open === x.nation) box.append(details(x, name));
    return box;
  }

  function details(x, name) {
    const w = W(), has = Boolean(N.data && N.data.mod);
    const parts = [];
    parts.push(el("h3", { textContent: w.nations_name_head, title: w.tip_nations_name_head }),
      el("p", { className: "muted small", textContent: w.nations_name_help }), wordsPanel(x.name_key, render));
    if (x.army_key) {
      parts.push(el("h3", { textContent: w.nations_army_head, title: w.tip_nations_army_head }),
        el("p", { className: "muted small", textContent: w.nations_army_help }), wordsPanel(x.army_key, render));
    }
    // the flag: the game's and the mod's side by side, a picture chosen and fitted here, or the game's back
    parts.push(el("h3", { textContent: w.nations_flag_head, title: w.tip_nations_flag_head }),
      el("p", { className: "muted small", textContent: w.nations_flag_help }));
    if (x.flag) {
      const pics = el("div", { className: "nation-flags" },
        el("figure", {}, flagImage(x.flag.game_url, w.nations_flag_game, true), el("figcaption", { className: "small muted", textContent: w.nations_flag_game })),
        ...(x.flag.own ? [el("figure", {}, flagImage(x.flag.url, w.nations_flag_mine, true), el("figcaption", { className: "small muted", textContent: w.nations_flag_mine }))] : []));
      const input = el("input", { type: "file", accept: "image/*" });
      input.hidden = true;
      const shine = el("input", { type: "checkbox", checked: true, title: w.tip_nations_shine });
      const pick = el("button", { type: "button", className: "small primary", textContent: w.nations_flag_pick,
        title: w.tip_nations_flag_pick, disabled: !has });
      pick.addEventListener("click", () => input.click());
      input.addEventListener("change", () => { const f = input.files[0]; input.value = ""; if (f) useFlag(x, f, shine.checked); });
      const back = el("button", { type: "button", className: "small ghost", textContent: w.nations_flag_back,
        title: w.tip_nations_flag_back, disabled: !has || !x.flag.own });
      back.addEventListener("click", async () => {
        try { await api().nation_reset(x.nation, "flag"); } catch (err) { problem(err); return; }
        say(fill(w.nations_flag_backed, { nation: name.now }), "ok");
        render();
      });
      // a picture dropped on the flags works as the button does
      pics.addEventListener("dragover", (e) => { if (has) e.preventDefault(); });
      pics.addEventListener("drop", (e) => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (has && f) useFlag(x, f, shine.checked); });
      parts.push(pics, el("div", { className: "actions" }, pick, back,
        el("label", { className: "small", title: w.tip_nations_shine }, shine, " " + w.nations_shine)), input);
    } else {
      parts.push(el("p", { className: "muted small", textContent: w.nations_flag_none }));
    }
    // its units and what they say: where they're always changed
    const units = el("button", { type: "button", className: "small", textContent: fill(w.nations_units, { nation: name.now }),
      title: w.tip_nations_units });
    units.addEventListener("click", () => {
      state.nation = x.nation;
      showView("units");
      renderChips();
      refreshList();
    });
    parts.push(el("h3", { textContent: w.nations_units_head, title: w.tip_nations_units }),
      el("p", { className: "muted small", textContent: w.nations_units_help }), el("div", { className: "actions" }, units));
    const all = el("button", { type: "button", className: "small ghost", textContent: w.nations_reset,
      title: w.tip_nations_reset, disabled: !has });
    all.addEventListener("click", async () => {
      try { await api().nation_reset(x.nation, "all"); } catch (err) { problem(err); return; }
      say(fill(w.nations_reset_done, { nation: name.game }), "ok");
      render();
    });
    parts.push(el("div", { className: "actions nation-reset" }, all));
    return el("div", { className: "nation-details" }, ...parts);
  }

  // a picture of the modder's as the nation's flag: fitted to the flag's size (filling it, centred), shone like the
  // game's flags (their top half lighter, their bottom half darker); the round shape is the game's (the build keeps
  // the flag's own alpha), so nothing outside the circle shows
  async function useFlag(x, file, shine) {
    const w = W(), fw = x.flag.width, fh = x.flag.height;
    let bitmap;
    try { bitmap = await createImageBitmap(file); } catch (err) { problem(new Error(w.nations_flag_unreadable)); return; }
    const canvas = document.createElement("canvas");
    canvas.width = fw; canvas.height = fh;
    const g = canvas.getContext("2d");
    const scale = Math.max(fw / bitmap.width, fh / bitmap.height);
    const dw = bitmap.width * scale, dh = bitmap.height * scale;
    g.imageSmoothingQuality = "high";
    g.drawImage(bitmap, (fw - dw) / 2, (fh - dh) / 2, dw, dh);
    // the game flag's own shape (its alpha), so the picture shown here is the one the game will show (the build keeps
    // the game's alpha whatever this picture's is)
    let shape = null;
    try {
      const game = await new Promise((ok, bad) => { const i = new Image(); i.onload = () => ok(i); i.onerror = bad; i.src = x.flag.game_url; });
      const s = document.createElement("canvas");
      s.width = fw; s.height = fh;
      const sg = s.getContext("2d");
      sg.drawImage(game, 0, 0, fw, fh);
      shape = sg.getImageData(0, 0, fw, fh).data;
    } catch { /* the game's flag couldn't be drawn here: the picture is saved square, the build still cuts it */ }
    const img = g.getImageData(0, 0, fw, fh), d = img.data;
    for (let y = 0; y < fh; y++) {
      const top = y < fh / 2, t = top ? 0.22 * (1 - y / (fh / 2)) : 0;
      for (let xx = 0; xx < fw; xx++) {
        const i = (y * fw + xx) * 4;
        if (shine) for (let c = 0; c < 3; c++) d[i + c] = top ? d[i + c] + (255 - d[i + c]) * t : d[i + c] * 0.78;
        d[i + 3] = shape ? shape[i + 3] : 255;
      }
    }
    g.putImageData(img, 0, 0);
    try { await api().nation_flag_set(x.nation, canvas.toDataURL("image/png")); } catch (err) { problem(err); return; }
    say(fill(w.nations_flag_saved, { nation: inLang(x.name).now }), "ok");
    render();
  }

  window.NationsView = {
    open(words, lang) { N.words = words; N.lang = lang; render(); },
    setWords(words, lang) { N.words = words; N.lang = lang; render(); },
    modChanged() { render(); },
  };
})();
