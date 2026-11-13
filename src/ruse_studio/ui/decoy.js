// RUSE Decoy, the sound and animation designer (StudioApi.decoy / decoy_list / decoy_volume / decoy_volume_all /
// decoy_volumes, rusemod.soundlist, rusemod.sound): every sound the game has, by kind (weapons near and far, impacts,
// engines, surroundings, map backgrounds, the interface, the ruse cards, unit voices, the HQ's lines, radio, mission
// dialogue, music); each heard, made louder or quieter from 0 to 200% of the game's (saved in the mod's
// files/sound/volume.toml; the build makes the sound again at it), and replaced in sound.js's editor. A mission's
// lines show what they say, in the Studio's language. "Music and jingles" is the game's songs by where they play
// (sound.js musicInto: where the Music tab was), each with its volume too. A unit's page opens it on that unit's own
// sounds (showUnitSounds), and its animations: each change to one is for "Only this unit" (its own copy of the clip,
// files/anim/units.toml) or "Every unit that plays it" (the clip itself); and, for a new unit of the mod, Change its
// animations in Blender and Bring my changes back (blenderBox: every animation the unit plays out to Blender, the
// changed ones back as this unit's own; ruse_studio.decoyblender). Copy this animation… (copyBox) makes a copy of an
// animation in the mod that only the units and soldiers ticked under its Who plays it play (whoBox; Your copies down
// the left, copiesList; StudioApi.decoy_copy_*, ruse_studio.decoycopies; the owner, 2026-11-13: "a way to copy an
// animation so that way you can change an animation and implement it into like certain models and soldiers").
// Uses app.js's $, el, fill, say, problem and api.
(function () {
  "use strict";
  const D = { words: {}, lang: "base", data: null, kind: null, words_q: "", mission: "", in_lang: "", rows: [],
              total: 0, start: 0, timer: null, unit: null, mode: "sound", akind: null, adata: null, anim: null,
              scope: "all", blender: null, said: null, busy: false, copy: null, cdata: null, who: null, whoQ: "" };
  // the animation's changes the editor shows and makes: one of the mod's copies of it (D.copy, its id: opened from Your
  // copies, or picked under Change it for on a unit's page), the unit's own copy ("unit": opened from a unit's page;
  // until it has one, the clip as it plays now) or the clip every unit plays ("all"), and the unit the calls are for
  const copyOf = (a) => D.copy ? (a.copy === D.copy ? a : (a.copies || []).find((c) => c.copy === D.copy) || null) : null;
  const cur = (a) => copyOf(a) || ((D.scope === "unit" && a.own) ? a.own : a);
  const scopeUnit = () => (!D.copy && D.scope === "unit" && D.unit) ? D.unit.address : null;
  // a figure of a unit as the page names it (ruse_studio.modelfit.figure_kind's kinds; app.js fitWho's words)
  const FIGURE_WORDS = { rifle: "fit_fig_rifle", heavy: "fit_fig_heavy", far: "fit_fig_far", fallen: "fit_fig_fallen",
                         wreck: "fit_fig_wreck", unit: "fit_fig_unit", other: "fit_fig_other" };
  const W = () => D.words;
  const clock = (s) => `${Math.floor(Math.round(s) / 60)}:${String(Math.round(s) % 60).padStart(2, "0")}`;
  const shortClock = (s) => s < 10 ? `${s.toFixed(1)} s` : clock(s);
  // the dialogue's language folders as the Studio names its languages
  const LANGS = { us: "decoy_lang_us", fr: "decoy_lang_fr", ger: "decoy_lang_ger", ita: "decoy_lang_ita",
                  spa: "decoy_lang_spa", pol: "decoy_lang_pol", ru: "decoy_lang_ru", jpn: "decoy_lang_jpn" };
  const shown = () => !$("decoy-view").classList.contains("hidden");

  async function open(words, lang) {
    D.words = words;
    D.lang = lang;
    const w = W();
    $("decoy-title").textContent = w.decoy_title;
    $("decoy-title").title = w.decoy_subtitle;
    $("decoy-sub").textContent = w.decoy_subtitle;
    $("decoy-help").textContent = w.decoy_help;
    $("decoy-search").placeholder = w.decoy_search;
    $("decoy-search").title = w.tip_decoy_search;
    $("decoy-mission").title = w.tip_decoy_mission;
    $("decoy-lang").title = w.tip_decoy_lang;
    $("decoy-all-label").textContent = w.decoy_all;
    $("decoy-all").title = w.tip_decoy_all;
    $("decoy-all-set").textContent = w.decoy_all_set;
    $("decoy-all-set").title = w.tip_decoy_all;
    $("decoy-more").textContent = w.decoy_more;
    let data;
    try { data = await api().decoy(lang); } catch (err) { problem(err); return; }
    try { D.adata = await api().decoy_anims(); } catch (err) { D.adata = { kinds: [] }; problem(err); }
    try { D.cdata = await api().decoy_copies(); } catch (err) { D.cdata = { copies: [], mod: false }; problem(err); }
    if (!shown()) return;   // another tab meanwhile
    D.data = data;
    $("decoy-nomod").textContent = data.mod ? "" : w.decoy_nomod;
    $("decoy-nomod").classList.toggle("hidden", data.mod);
    if (!D.unit && (!D.kind || !data.kinds.some((k) => k.id === D.kind))) D.kind = data.kinds.length ? data.kinds[0].id : null;
    kinds();
    missions();
    await list(true);
  }

  // --- the kinds, down the left (and a unit's own sounds, when its page sent us here) ---
  function kinds() {
    const w = W();
    const button = (k, mode) => {
      const on = !D.unit && D.mode === mode && (mode === "sound" ? D.kind : D.akind) === k.id;
      const word = mode === "sound" ? `decoy_kind_${k.id}` : `decoy_akind_${k.id}`;
      const b = el("button", { type: "button", className: "decoy-kind" + (on ? " on" : ""), title: w["tip_" + word] || "" },
        el("span", { textContent: w[word] || k.id }),
        el("span", { className: "muted small", textContent: k.count.toLocaleString() }),
        ...(k.changed ? [el("span", { className: "music-mine small", textContent: fill(w.decoy_changed, { n: k.changed }) })] : []));
      b.addEventListener("click", () => {
        if (on) return;
        D.unit = null;
        D.mode = mode;
        if (mode === "sound") { D.kind = k.id; D.mission = ""; } else { D.akind = k.id; }
        kinds(); missions(); list(true);
      });
      return b;
    };
    const buttons = [el("p", { className: "decoy-head", textContent: w.decoy_sounds_head }),
      ...D.data.kinds.map((k) => button(k, "sound")),
      el("p", { className: "decoy-head", textContent: w.decoy_anims_head, title: w.tip_decoy_anims_head }),
      ...((D.adata && D.adata.kinds) || []).map((k) => button(k, "anim"))];
    if (D.cdata && D.cdata.mod) {   // Your copies: the mod's copies of animations (copiesList)
      const on = !D.unit && D.mode === "copies";
      const b = el("button", { type: "button", className: "decoy-kind" + (on ? " on" : ""), title: w.tip_decoy_copies_kind },
        el("span", { textContent: w.decoy_copies_kind }),
        el("span", { className: "muted small", textContent: D.cdata.copies.length.toLocaleString() }));
      b.addEventListener("click", () => {
        if (on) return;
        D.unit = null;
        D.mode = "copies";
        kinds(); missions(); list(true);
      });
      buttons.push(b);
    }
    if (D.unit) {
      const u = el("button", { type: "button", className: "decoy-kind on", title: w.tip_decoy_unit },
        el("span", { textContent: fill(w.decoy_unit_kind, { name: D.unit.name }) }),
        el("span", { className: "muted small", textContent: String(D.unit.count) }));
      buttons.unshift(u);
    }
    $("decoy-kinds").replaceChildren(...buttons);
  }

  // the mission and language pickers, for a mission's dialogue and the HQ's lines (one file per language)
  function missions() {
    const w = W();
    const sounds = !D.unit && D.mode === "sound";
    const dialogue = sounds && D.kind === "dialogue", perLang = dialogue || (sounds && D.kind === "hq_voices");
    $("decoy-mission").classList.toggle("hidden", !dialogue);
    $("decoy-lang").classList.toggle("hidden", !perLang);
    if (dialogue) {
      $("decoy-mission").replaceChildren(el("option", { value: "", textContent: w.decoy_all_missions }),
        ...D.data.missions.map((m) => el("option", { value: m.id, textContent: `${m.name} (${m.count.toLocaleString()})` })));
      $("decoy-mission").value = D.mission;
    }
    if (perLang) {
      const mine = { base: "us", us: "us", fr: "fr", ger: "ger", ita: "ita", spa: "spa", pol: "pol", ru: "ru", jpn: "jpn" }[D.lang] || "us";
      if (!D.in_lang) D.in_lang = D.data.langs.includes(mine) ? mine : (D.data.langs[0] || "");
      $("decoy-lang").replaceChildren(el("option", { value: "", textContent: w.decoy_all_langs }),
        ...D.data.langs.map((l) => el("option", { value: l, textContent: w[LANGS[l]] || l })));
      $("decoy-lang").value = D.in_lang;
    }
  }

  // --- the sounds of the kind picked, a page at a time ---
  async function list(fresh) {
    const w = W();
    const anims = !D.unit && D.mode === "anim";
    const copies = !D.unit && D.mode === "copies";
    const music = !D.unit && !anims && !copies && D.kind === "music";
    for (const id of ["decoy-search", "decoy-count", "decoy-more"]) $(id).classList.toggle("hidden", music || copies || (id === "decoy-search" && Boolean(D.unit)));
    for (const id of ["decoy-all-set"]) $(id).classList.toggle("hidden", anims || copies);
    $("decoy-all").closest("label").classList.toggle("hidden", anims || copies);
    $("decoy-kind-help").textContent = D.unit ? fill(w.decoy_unit_help_all, { name: D.unit.name })
      : copies ? w.tip_decoy_copies_kind
      : anims ? (w[`tip_decoy_akind_${D.akind}`] || "") : (w[`tip_decoy_kind_${D.kind}`] || "");
    $("decoy-all").value = "100";
    $("decoy-all-value").textContent = "100%";
    if (music) { await songs(); return; }
    if (copies) { await copiesList(); return; }
    if (anims) { await animList(fresh); return; }
    if (!D.kind && !D.unit) { $("decoy-rows").replaceChildren(el("p", { className: "muted", textContent: w.decoy_none })); return; }
    if (fresh) { D.start = 0; D.rows = []; }
    const perLang = !D.unit && (D.kind === "dialogue" || D.kind === "hq_voices");
    let got;
    try {
      got = D.unit ? await api().decoy_unit_list(D.unit.address, D.lang)
        : await api().decoy_list(D.kind, D.words_q, D.kind === "dialogue" ? (D.mission || null) : null,
                                 perLang ? (D.in_lang || null) : null, D.lang, D.start, 100);
    } catch (err) { problem(err); return; }
    D.rows = fresh ? got.rows : D.rows.concat(got.rows);
    D.total = got.total;
    D.start = D.rows.length;
    $("decoy-count").textContent = fill(w.decoy_count, { n: D.rows.length.toLocaleString(), total: got.total.toLocaleString() });
    const rows = D.rows.map(row);
    $("decoy-rows").replaceChildren(...(rows.length ? rows : [el("p", { className: "muted", textContent: D.unit ? w.decoy_unit_none : w.decoy_none })]));
    $("decoy-more").classList.toggle("hidden", D.rows.length >= D.total);
    if (D.unit) {   // and the unit's own animations, below its sounds
      let got;
      try { got = await api().decoy_unit_anims(D.unit.address); } catch (err) { problem(err); return; }
      if (got.rows.length) {
        $("decoy-rows").append(el("h2", { textContent: fill(w.decoy_unit_anims, { n: got.rows.length }) }),
          await blenderBox(), ...got.rows.map(animRow));
      }
    }
  }

  // --- the unit's animations in Blender, both ways (StudioApi.decoy_blender_state, decoy_blender, decoy_blender_back;
  // ruse_studio.decoyblender; the owner, 2026-11-10: "The only way you should change animation is in Ruse Decoy, you
  // go and change the animation for your new unit."): Change its animations in Blender opens every one the unit plays,
  // Bring my changes back makes the changed ones this unit's own; a game unit is told why not ---
  async function blenderBox() {
    const box = el("div", { className: "decoy-blender" });
    try { D.blender = await api().decoy_blender_state(D.unit.address, D.lang); }
    catch (err) { problem(err); return box; }
    drawBlender(box);
    return box;
  }

  function drawBlender(box) {
    const w = W(), st = D.blender || {};
    if (!st.can) {
      box.replaceChildren(el("p", { className: "muted small", textContent: st.why_not || "" }));
      return;
    }
    const go = el("button", { type: "button", className: "primary", textContent: w.decoy_blender,
      title: w.tip_decoy_blender, disabled: D.busy || Boolean(st.open) });
    go.addEventListener("click", () => blenderOpen(box));
    // Choose Blender… (StudioApi.choose_blender, as the unit's page has it): where blender.exe is, which a Blender
    // that couldn't be opened is told to use (decoyblender's decoy_blender_open_choose)
    const choose = el("button", { type: "button", className: "ghost", textContent: w.look_choose_blender,
      title: w.tip_look_choose_blender, disabled: D.busy });
    choose.addEventListener("click", async () => {
      try {
        const r = await api().choose_blender();
        if (r && r.message) say(r.message, "error");
      } catch (err) { problem(err); }
    });
    const buttons = [go];
    if (st.open || st.waiting) {   // (its Blender open, or a sending not brought back yet)
      const back = el("button", { type: "button", textContent: w.decoy_blender_back, title: w.tip_decoy_blender_back,
        disabled: D.busy });
      back.addEventListener("click", () => blenderBack(box));
      buttons.push(back);
    }
    buttons.push(choose);
    // every sending kept aside when its animations were opened again, never brought back (newest first): each can be
    // brought back, or put in the Recycle Bin, so none is out of reach behind another
    const asides = (st.asides || []).map((a) => {
      const back = el("button", { type: "button", textContent: w.decoy_blender_aside, title: w.tip_decoy_blender_aside,
        disabled: D.busy });
      back.addEventListener("click", () => blenderBack(box, a.name));
      const bin = el("button", { type: "button", textContent: w.decoy_blender_aside_recycle,
        title: w.tip_decoy_blender_aside_recycle, disabled: D.busy });
      bin.addEventListener("click", () => blenderRecycle(box, a.name));
      return el("div", { className: "decoy-aside" },
        el("p", { className: "muted small", textContent: fill(w.decoy_blender_aside_when, { when: a.when }) }),
        el("div", { className: "squad-go" }, back, bin));
    });
    box.replaceChildren(el("div", { className: "squad-go" }, ...buttons), ...asides,
      el("p", { className: "muted small", textContent: w.decoy_blender_how }), ...(D.said ? [D.said] : []));
  }

  // a sending kept aside, to the Recycle Bin (StudioApi.decoy_blender_recycle): nothing of it taken in
  async function blenderRecycle(box, aside) {
    D.busy = true;
    drawBlender(box);
    let r = null;
    try { r = await api().decoy_blender_recycle(D.unit.address, aside, D.lang); } catch (err) { problem(err); }
    D.busy = false;
    if (r) {
      D.blender = r;
      D.said = el("p", { className: "squad-result", role: "status", textContent: r.message });
      say(r.message, "");
    }
    drawBlender(box);
  }

  async function blenderOpen(box) {
    D.busy = true;
    D.said = null;
    drawBlender(box);
    try {
      const r = await api().decoy_blender(D.unit.address, D.lang);
      D.blender = r;
      say(r.message, "ok");
    } catch (err) { problem(err); }
    D.busy = false;
    drawBlender(box);
  }

  // what came back said on the page and in a pop-up, then its animations read again (the changed ones its own now);
  // `aside`: the sending kept aside to bring back instead (decoy_blender_state's "aside")
  async function blenderBack(box, aside) {
    D.busy = true;
    drawBlender(box);
    let r = null;
    try { r = await api().decoy_blender_back(D.unit.address, D.lang, aside || null); } catch (err) { problem(err); }
    D.busy = false;
    if (!r) { drawBlender(box); return; }
    D.blender = r;
    D.said = el("p", { className: "squad-result", role: "status", textContent: r.message });
    say(r.message, (r.changed && r.changed.length) || (r.undone && r.undone.length) ? "ok" : "");
    await list(true);
  }

  // --- animations (StudioApi.decoy_anim_list, rusemod.animlist): one kind's clips ---
  async function animList(fresh) {
    const w = W();
    if (fresh) { D.start = 0; D.rows = []; }
    let got;
    try { got = await api().decoy_anim_list(D.akind, D.words_q, D.start, 100); } catch (err) { problem(err); return; }
    D.rows = fresh ? got.rows : D.rows.concat(got.rows);
    D.total = got.total;
    D.start = D.rows.length;
    $("decoy-count").textContent = fill(w.decoy_count, { n: D.rows.length.toLocaleString(), total: got.total.toLocaleString() });
    const rows = D.rows.map(animRow);
    $("decoy-rows").replaceChildren(...(rows.length ? rows : [el("p", { className: "muted", textContent: w.decoy_none })]));
    $("decoy-more").classList.toggle("hidden", D.rows.length >= D.total);
  }

  // --- Your copies: the mod's copies of animations (StudioApi.decoy_copies), each opened in the editor as itself ---
  async function copiesList() {
    const w = W();
    let got;
    try { got = await api().decoy_copies(); } catch (err) { problem(err); return; }
    if (!(shown() && !D.unit && D.mode === "copies")) return;   // (another kind picked meanwhile)
    D.cdata = got;
    kinds();   // (the count beside Your copies, as the list has it now)
    const rows = got.copies.map(copyRow);
    $("decoy-rows").replaceChildren(...(rows.length ? rows : [el("p", { className: "muted", textContent: w.decoy_copies_none })]));
  }

  function copyRow(c) {
    const w = W();
    const head = el("div", { className: "music-head" },
      el("span", { className: "music-name", textContent: c.name }),
      el("span", { className: "muted small", textContent: `${c.seconds.toFixed(1)} s` }));
    for (const m of changeMarks(c)) head.append(el("span", { className: "music-mine small", textContent: m }));
    const bits = [fill(w.decoy_copy_of, { clip: c.clip_name }),
      c.units ? fill(w.decoy_copy_units, { n: c.units }) : w.decoy_copy_units_none];
    const edit = el("button", { type: "button", className: "small primary", textContent: "▶ " + w.decoy_anim_open,
                                title: w.tip_decoy_copy_open });
    edit.addEventListener("click", () => openAnim(c, c.copy));
    const del = el("button", { type: "button", className: "link small", textContent: w.decoy_copy_delete,
                               title: w.tip_decoy_copy_delete });
    del.addEventListener("click", async () => {
      if (!window.confirm(fill(w.decoy_copy_delete_confirm, { name: c.name, n: c.units }))) return;
      try {
        await api().decoy_copy_delete(c.copy);
        say(fill(w.decoy_copy_deleted, { name: c.name }), "ok");
        open(D.words, D.lang);
      } catch (err) { problem(err); }
    });
    return el("div", { className: "music-row" + (c.changed ? " edited" : "") }, head,
      el("div", { className: "muted small music-where", textContent: bits.join(" · ") }),
      el("div", { className: "music-actions" }, edit, del));
  }

  // what the mod changes in an animation (or a copy), as marks beside its name
  function changeMarks(a) {
    const w = W(), marks = [];
    if (a.speed !== 100) marks.push(fill(w.decoy_anim_speed_mark, { pct: Math.round(a.speed) }));
    if (a.from) marks.push(w.decoy_anim_from_mark);
    if (Object.keys(a.tweaks || {}).length) marks.push(fill(w.decoy_anim_bones_mark, { n: Object.keys(a.tweaks).length }));
    if (a.mine) marks.push(w.music_yours);
    return marks;
  }

  function animRow(a) {
    const w = W();
    const head = el("div", { className: "music-head" },
      el("span", { className: "music-name", textContent: a.name }),
      el("span", { className: "muted small", textContent: `${a.seconds.toFixed(1)} s` }));
    const marks = changeMarks(a);
    if (a.own) marks.push(w.decoy_anim_own_mark);   // (a unit's list: it has its own copy)
    for (const c of a.copies || []) marks.push(fill(w.decoy_copy_mark, { name: c.name }));   // (it plays a copy of yours)
    for (const m of marks) head.append(el("span", { className: "music-mine small", textContent: m }));
    const bits = [];
    if (a.role) bits.push(a.role);
    if (a.names.length) bits.push(fill(w.decoy_anim_names, { names: a.names.slice(0, 4).join(", ") + (a.names.length > 4 ? " …" : "") }));
    bits.push(a.units ? fill(w.decoy_anim_units, { n: a.units }) : w.decoy_anim_no_units);
    const edit = el("button", { type: "button", className: "small primary", textContent: "▶ " + w.decoy_anim_open,
                                title: w.tip_decoy_anim_open });
    edit.addEventListener("click", () => openAnim(a));
    const actions = el("div", { className: "music-actions" }, edit);
    if (a.changed) {
      const back = el("button", { type: "button", className: "link small", textContent: w.decoy_anim_reset, title: w.tip_decoy_anim_reset });
      back.addEventListener("click", async () => {
        try { await api().decoy_anim_reset(a.member); say(fill(w.decoy_anim_reset_done, { name: a.name }), "ok"); open(D.words, D.lang); }
        catch (err) { problem(err); }
      });
      actions.append(back);
    }
    if (a.own && D.unit) {   // the unit's own copy taken out: it plays the clip as every unit does again
      const unit = D.unit;
      const back = el("button", { type: "button", className: "link small", textContent: w.decoy_anim_reset_own,
                                  title: w.tip_decoy_anim_reset_own });
      back.addEventListener("click", async () => {
        try {
          await api().decoy_anim_reset(a.member, unit.address);
          say(fill(w.decoy_anim_reset_own_done, { name: a.name, unit: unit.name }), "ok");
          open(D.words, D.lang);
        } catch (err) { problem(err); }
      });
      actions.append(back);
    }
    return el("div", { className: "music-row" + (a.changed || a.own || (a.copies || []).length ? " edited" : "") }, head,
      el("div", { className: "muted small music-where", textContent: bits.join(" · ") }), actions);
  }

  // --- the animation editor: the clip in 3D on a unit that plays it, as the mod makes it, and its changes ---
  const V = { gl: null, mixer: null, clock: null, root: null };

  async function viewer() {
    if (V.gl) return V.gl;
    const THREE = await import("three");
    const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
    const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(window.devicePixelRatio || 1);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
    scene.add(new THREE.HemisphereLight(0xeef3f8, 0x4a4234, 2.2));
    const sun = new THREE.DirectionalLight(0xfff4e0, 2.4);
    sun.position.set(3, 5, 4);
    scene.add(sun, camera);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    const grid = new THREE.GridHelper(10, 20, 0x5a6470, 0x39414a);
    scene.add(grid);
    V.clock = new THREE.Clock();
    V.gl = { THREE, renderer, scene, camera, controls, loader: new GLTFLoader() };
    const loop = () => {
      requestAnimationFrame(loop);
      const host = renderer.domElement.parentElement;
      if (!host || !host.isConnected || host.offsetParent === null) return;
      const wd = host.clientWidth, ht = host.clientHeight, size = renderer.getSize(new THREE.Vector2());
      if (wd && ht && (size.x !== wd || size.y !== ht)) {
        renderer.setSize(wd, ht);
        camera.aspect = wd / ht;
        camera.updateProjectionMatrix();
      }
      const dt = V.clock.getDelta();
      if (V.mixer) V.mixer.update(dt);
      controls.update();
      renderer.render(scene, camera);
    };
    loop();
    return V.gl;
  }

  async function showClip(a) {
    const w = W();
    $("da-note").textContent = w.decoy_anim_loading;
    let got;
    try { got = await api().decoy_anim_preview(a.member, scopeUnit(), D.copy); } catch (err) { $("da-note").textContent = (err && err.message) || String(err); return; }
    playClip(got, w.decoy_anim_on);
  }

  // a clip's .glb in the 3D view, playing; `note` says what's shown ({model}, {sec})
  async function playClip(got, note) {
    const w = W();
    if (!got.url) { $("da-note").textContent = w.decoy_anim_no_model; return; }
    let gl;
    try { gl = await viewer(); } catch (err) { $("da-note").textContent = w.decoy_anim_no_3d; return; }
    $("da-view").replaceChildren(gl.renderer.domElement);
    gl.loader.load(got.url + "?v=" + Date.now(), (g) => {
      if (V.root) gl.scene.remove(V.root);
      V.root = g.scene;
      gl.scene.add(g.scene);
      V.mixer = new gl.THREE.AnimationMixer(g.scene);
      if (g.animations.length) V.mixer.clipAction(g.animations[0]).play();
      const box = new gl.THREE.Box3().setFromObject(g.scene);
      const c = box.getCenter(new gl.THREE.Vector3()), r = Math.max(0.5, box.getSize(new gl.THREE.Vector3()).length());
      gl.controls.target.copy(c);
      gl.camera.position.set(c.x + r * 1.1, c.y + r * 0.5, c.z + r * 1.1);
      gl.camera.near = r / 100;
      gl.camera.far = r * 100;
      gl.camera.updateProjectionMatrix();
      $("da-note").textContent = fill(note, { model: got.model, sec: got.seconds.toFixed(2) });
    }, undefined, () => { $("da-note").textContent = w.decoy_anim_no_3d; });
  }

  // --- motion capture: a .bvh picked here, a stretch of it made into this clip (watched first, then kept) ---
  function mocapWords() {
    const w = W();
    for (const [id, word] of [["da-mc-label", "decoy_mc"], ["da-mc-help", "decoy_mc_help"], ["da-mc-pick", "decoy_mc_pick"],
      ["da-mc-from-label", "decoy_mc_from"], ["da-mc-len-label", "decoy_mc_len"], ["da-mc-place-label", "decoy_mc_place"],
      ["da-mc-loop-label", "decoy_mc_loop"], ["da-mc-credit-label", "decoy_mc_credit"], ["da-mc-tip", "decoy_mc_tip"],
      ["da-mc-watch", "decoy_mc_watch"], ["da-mc-use", "decoy_mc_use"]]) $(id).textContent = w[word];
    for (const [id, tip] of [["da-mc-pick", "tip_decoy_mc_pick"], ["da-mc-from", "tip_decoy_mc_from"],
      ["da-mc-len", "tip_decoy_mc_len"], ["da-mc-place", "tip_decoy_mc_place"], ["da-mc-loop", "tip_decoy_mc_loop"],
      ["da-mc-credit", "tip_decoy_mc_credit"], ["da-mc-watch", "tip_decoy_mc_watch"], ["da-mc-use", "tip_decoy_mc_use"]]) $(id).title = w[tip];
    mocapAbout();
    libWords();
    libLoad(true);
  }

  function mocapAbout() {
    const w = W(), m = D.mc;
    $("da-mc-controls").classList.toggle("hidden", !m || m.missing.length > 0);
    if (!m) { $("da-mc-about").textContent = ""; return; }
    $("da-mc-about").textContent = m.missing.length
      ? fill(w.decoy_mc_missing, { name: m.name, parts: m.missing.map((p) => w["decoy_mc_part_" + p] || p).join(", ") })
      : fill(w.decoy_mc_about, { name: m.name, sec: m.seconds.toFixed(1), fps: Math.round(m.fps) });
  }

  function mocapLabels() {
    $("da-mc-from-value").textContent = `${Number($("da-mc-from").value).toFixed(1)} s`;
    $("da-mc-len-value").textContent = `${Number($("da-mc-len").value).toFixed(1)} s`;
  }

  async function mocapPicked() {
    const w = W(), f = $("da-mc-file").files[0];
    $("da-mc-file").value = "";
    if (!f) return;
    $("da-mc-about").textContent = w.decoy_anim_loading;
    try {
      mocapSet(await api().decoy_mocap_open(f.name, await f.text()), 0, D.anim ? D.anim.seconds : 1);
    } catch (err) { $("da-mc-about").textContent = ""; problem(err); }
  }

  // an opened file (picked, or a library move) as the panel's motion: its stretch from `from` for `len` seconds
  function mocapSet(got, from, len) {
    D.mc = got;
    $("da-mc-from").max = String(Math.max(0.1, got.seconds - 0.2));
    $("da-mc-from").value = String(Math.min(from, got.seconds).toFixed(1));
    $("da-mc-len").max = String(Math.max(0.2, Math.min(20, got.seconds)));
    $("da-mc-len").value = String(Math.max(0.2, Math.min(len, got.seconds - from, 20)).toFixed(1));
    $("da-mc-loop").checked = !!(D.anim && D.anim.loops);
    $("da-mc-credit").value = got.credit || "";
    mocapLabels();
    mocapAbout();
  }

  // --- the motion library: the free sets' moves by kind, each fetched the first time it's picked ---
  const LIB = { kind: "", words: "", start: 0, rows: [], total: 0, timer: null, poll: null, sets: {} };

  function libWords() {
    const w = W();
    $("da-lib-title").textContent = w.decoy_lib;
    $("da-lib-search").placeholder = w.decoy_lib_search;
    $("da-lib-search").title = w.tip_decoy_lib_search;
    $("da-lib-kind").title = w.tip_decoy_lib_kind;
    $("da-lib-get").textContent = w.decoy_lib_style_get;
    $("da-lib-get").title = w.tip_decoy_lib_style_get;
    $("da-lib-more").textContent = w.decoy_lib_more;
    $("da-lib-or").textContent = w.decoy_lib_or;
  }

  async function libLoad(fresh) {
    const w = W();
    if (fresh) { LIB.start = 0; LIB.rows = []; }
    let got;
    try { got = await api().decoy_motions(LIB.kind, LIB.words, "", LIB.start, 60); } catch (err) { problem(err); return; }
    if (fresh) {
      const pick = $("da-lib-kind"), was = LIB.kind;
      pick.replaceChildren(el("option", { value: "", textContent: w.decoy_lib_all_kinds }),
        ...got.kinds.map((k) => el("option", { value: k.id, textContent: `${w["decoy_lib_kind_" + k.id] || k.id} (${k.count.toLocaleString()})` })));
      pick.value = was;
      $("da-lib-rows").replaceChildren();
    }
    LIB.total = got.total;
    LIB.start += got.rows.length;
    LIB.rows.push(...got.rows);
    $("da-lib-rows").append(...got.rows.map(libRow));
    $("da-lib-more").classList.toggle("hidden", LIB.start >= LIB.total);
    libSets(got.sets);
  }

  function libSets(sets) {
    const w = W(), cmu = sets.cmu, st = sets["100style"];
    LIB.sets = sets;
    const bits = [];
    if (cmu) bits.push(fill(w.decoy_lib_cmu_state, { have: cmu.have.toLocaleString(), total: cmu.total.toLocaleString() }));
    const job = (st && st.job) || {};
    if (st) {
      if (job.state === "fetching") bits.push(fill(w.decoy_lib_style_fetching, { done: Math.round(job.done / 1048576).toLocaleString(), total: Math.round(job.total / 1048576).toLocaleString() }));
      else if (job.state === "failed") bits.push(fill(w.decoy_lib_style_failed, { why: job.message }));
      else if (st.have) bits.push(fill(w.decoy_lib_style_have, { have: st.have.toLocaleString(), total: st.total.toLocaleString() }));
      else bits.push(w.decoy_lib_style_none);
    }
    $("da-lib-sets").textContent = bits.join(" ");
    $("da-lib-get").classList.toggle("hidden", !st || st.have >= st.total || job.state === "fetching");
    clearTimeout(LIB.poll);
    if (job.state === "fetching" && $("decoy-anim").open) {   // its progress, until it's done
      LIB.poll = setTimeout(async () => {
        try { libSets(await api().decoy_motion_sets()); } catch (err) { /* asked again on the next look */ }
        if (((LIB.sets["100style"] || {}).job || {}).state !== "fetching") libLoad(true);
      }, 2000);
    }
  }

  function libRow(m) {
    const w = W();
    const name = m.set === "100style" ? `${m.name}: ${w["decoy_lib_way_" + m.way] || m.way}` : m.name;
    const row = el("button", { type: "button", className: "da-lib-row", title: w.tip_decoy_lib_row });
    row.append(el("span", { textContent: name }),
      el("span", { className: "small muted", textContent: [m.group.toLowerCase() === m.name.toLowerCase() ? "" : m.group,
        `${m.seconds.toFixed(1)} s`,
        m.set === "100style" ? "100STYLE" : "CMU",
        m.have ? w.decoy_lib_have : m.alone ? `${w.decoy_lib_fetch_mark} (${(m.size / 1048576).toFixed(1)} MB)` : w.decoy_lib_in_set]
        .filter(Boolean).join(" · ") }));
    row.addEventListener("click", () => libPick(m, row));
    return row;
  }

  async function libPick(m, row) {
    const w = W();
    for (const r of $("da-lib-rows").children) r.classList.remove("picked");
    row.classList.add("picked");
    $("da-mc-about").textContent = fill(w.decoy_lib_opening, { name: m.name });
    let got;
    try { got = await api().decoy_motion_open(m.id); } catch (err) { $("da-mc-about").textContent = ""; problem(err); return; }
    if (got.fetch_set) { $("da-mc-about").textContent = w.decoy_lib_needs_set; return; }
    if (!m.have) {   // now kept here: its row says so
      m.have = true;
      const kept = libRow(m);
      kept.classList.add("picked");
      row.replaceWith(kept);
    }
    mocapSet(got, got.from, got.length);
    if (!got.missing.length) mocapWatch();
  }

  async function libGetSet() {
    const w = W();
    $("da-lib-get").classList.add("hidden");
    try { await api().decoy_motion_set_fetch("100style"); say(w.decoy_lib_style_started, "ok"); }
    catch (err) { problem(err); }
    libLoad(true);
  }

  function mocapArgs() {
    return [D.anim.member, D.mc.id, Number($("da-mc-from").value), Number($("da-mc-len").value),
            $("da-mc-place").checked, $("da-mc-loop").checked];
  }

  async function mocapWatch() {
    const w = W();
    if (!D.anim || !D.mc) return;
    $("da-note").textContent = w.decoy_anim_loading;
    try { playClip(await api().decoy_mocap_preview(...mocapArgs()), w.decoy_mc_on); }
    catch (err) { $("da-note").textContent = (err && err.message) || String(err); }
  }

  async function mocapUse() {
    const w = W(), a = D.anim;
    if (!a || !D.mc) return;
    if (!$("da-mc-credit").value.trim()) { say(w.decoy_mc_credit_needed, "warn"); $("da-mc-credit").focus(); return; }
    const unit = scopeUnit(), copy = copyOf(a);
    try {
      const got = await api().decoy_mocap_use(...mocapArgs(), $("da-mc-credit").value.trim(), unit, D.copy);
      Object.assign(copy || a, got);
      say(copy ? fill(w.decoy_mc_used_copy, { name: copy.name })
        : unit ? fill(w.decoy_mc_used_own, { name: a.name, unit: D.unit.name }) : fill(w.decoy_mc_used, { name: a.name }), "ok");
      animControls(a);
      showClip(a);
    } catch (err) { problem(err); }
  }

  // `copyId`: one of the mod's copies opened as itself (Your copies), `a` being that copy
  async function openAnim(a, copyId) {
    const w = W();
    D.anim = a;
    D.who = null;
    // from a unit's page: its own copy when it has one, else a copy of yours it plays, or the clip as it plays now when
    // no change is made for every unit yet
    D.copy = copyId || (D.unit && !a.own && (a.copies || []).length ? a.copies[0].copy : null);
    D.scope = D.copy ? "copy" : D.unit && (a.own || !a.changed) ? "unit" : "all";
    window.SoundView.stop();
    $("da-title").textContent = a.name;
    leadLine(a);
    for (const [id, word] of [["da-speed-label", "decoy_anim_speed"], ["da-use-label", "decoy_anim_use"],
      ["da-bones-label", "decoy_anim_bones"], ["da-size-label", "decoy_anim_size"], ["da-axis-label", "decoy_anim_axis"],
      ["da-turn-label", "decoy_anim_turn"], ["da-close", "decoy_anim_done"]]) $(id).textContent = w[word];
    for (const [id, tip] of [["da-speed", "tip_decoy_anim_speed"], ["da-use", "tip_decoy_anim_use"], ["da-bone", "tip_decoy_anim_bone"],
      ["da-size", "tip_decoy_anim_size"], ["da-axis", "tip_decoy_anim_axis"], ["da-turn", "tip_decoy_anim_turn"]]) $(id).title = w[tip];
    $("da-use").replaceChildren(el("option", { value: "", textContent: w.decoy_anim_use_own }));
    $("da-bone").replaceChildren();
    scopeChoice(a);
    copyBox(a);
    animControls(a);
    mocapWords();
    if (!$("decoy-anim").open) $("decoy-anim").showModal();   // (already open: a copy just made opens in it)
    showClip(a);
    let info;
    try { info = await api().decoy_anim_info(a.member); } catch (err) { problem(err); return; }
    $("da-use").append(...info.same.map((s) => el("option", { value: s.member,
      textContent: s.name + (s.names.length ? ` (${s.names.slice(0, 2).join(", ")})` : "") })));
    $("da-use").value = cur(a).from || "";
    a.loops = info.loops;
    $("da-mc-loop").checked = info.loops;
    $("da-mc-label").closest("fieldset").classList.toggle("hidden", !info.mocap);
    $("da-bone").append(...info.bones.map((b) => el("option", { value: b, textContent: b })));
    const head = info.bones.find((b) => b.endsWith(" head"));
    $("da-bone").value = head || info.bones[0] || "";
    boneControls();
  }

  // the line under the editor's title: what the animation (or the copy) is, the names the game gives it, who plays it
  function leadLine(a) {
    const w = W();
    $("da-lead").textContent = [a.copy ? fill(w.decoy_copy_of, { clip: a.clip_name }) : "",
      a.names.length ? fill(w.decoy_anim_names, { names: a.names.join(", ") }) : "",
      a.copy ? (a.units ? fill(w.decoy_copy_units, { n: a.units }) : w.decoy_copy_units_none)
        : a.units ? fill(w.decoy_anim_units, { n: a.units }) : w.decoy_anim_no_units].filter(Boolean).join(" · ");
  }

  // "Change it for": Only this unit (its own copy of the clip), each copy of yours it plays (Copy this animation…) or
  // Every unit that plays it, when a unit's page sent us; none for a copy opened as itself
  function scopeChoice(a) {
    const w = W(), box = $("da-for");
    const show = Boolean(D.unit) && !a.copy;
    box.classList.toggle("hidden", !show);
    if (!show) { box.replaceChildren(); return; }
    const choice = el("div", { className: "choice", role: "radiogroup" }, el("span", { textContent: w.decoy_anim_for }));
    const now = D.copy ? "copy:" + D.copy : D.scope;
    for (const [scope, text, tip] of [["unit", w.decoy_anim_for_unit, w.tip_decoy_anim_for_unit],
      ...(a.copies || []).map((c) => ["copy:" + c.copy, fill(w.decoy_anim_for_copy, { name: c.name, n: c.units }),
                                       w.tip_decoy_anim_for_copy]),
      ["all", fill(w.decoy_anim_for_all, { n: a.units }), w.tip_decoy_anim_for_all]]) {
      const input = el("input", { type: "radio", name: "da-for", value: scope, checked: now === scope, title: tip });
      input.addEventListener("change", () => {
        D.copy = scope.startsWith("copy:") ? scope.slice(5) : null;
        D.scope = D.copy ? "copy" : scope;
        copyBox(a); animControls(a); showClip(a);
      });
      choice.append(el("label", { title: tip }, input, " " + text));
    }
    box.replaceChildren(choice);
  }

  // --- a copy of this animation (StudioApi.decoy_copy_make / _rename / _players / _tick; ruse_studio.decoycopies):
  // Copy this animation… (its name, then Make the copy: it opens here), and for a copy its name and Who plays it ---
  function copyBox(a) {
    const w = W(), c = copyOf(a), parts = [];
    if (c) {   // the copy's name, saved when changed
      const name = el("input", { type: "text", value: c.name, maxLength: 80, autocomplete: "off", title: w.tip_decoy_copy_name });
      name.setAttribute("aria-label", w.decoy_copy_name);
      name.addEventListener("change", async () => {
        try {
          Object.assign(c, await api().decoy_copy_rename(c.copy, name.value));
          if (a === c) $("da-title").textContent = c.name;
          say(fill(w.decoy_copy_renamed, { name: c.name }), "ok");
        } catch (err) { name.value = c.name; problem(err); }
      });
      parts.push(el("label", { className: "da-row", title: w.tip_decoy_copy_name },
        el("span", { className: "small", textContent: w.decoy_copy_name }), name));
    }
    if (D.data && D.data.mod) parts.push(copyForm(a));
    if (c) parts.push(whoBox());
    $("da-copy").replaceChildren(...parts);
    if (c) whoLoad(c);
  }

  // Copy this animation…: a name (the animation's, or the copy's, then "copy"), then Make the copy; the copy starts as
  // what the editor shows (the chosen copy, this unit's own, or every unit's) and opens in the editor
  function copyForm(a) {
    const w = W();
    const start = el("button", { type: "button", className: "small", textContent: w.decoy_copy_make, title: w.tip_decoy_copy_make });
    const form = el("form", { className: "da-copy-form hidden" });
    const name = el("input", { type: "text", autocomplete: "off", maxLength: 80, required: true,
                               placeholder: w.decoy_copy_name, title: w.tip_decoy_copy_name });
    name.setAttribute("aria-label", w.decoy_copy_name);
    const make = el("button", { type: "submit", className: "small primary", textContent: w.decoy_copy_create,
                                title: w.tip_decoy_copy_create });
    const cancel = el("button", { type: "button", className: "small ghost", textContent: w.cancel, title: w.tip_decoy_copy_cancel });
    cancel.addEventListener("click", () => { form.classList.add("hidden"); start.classList.remove("hidden"); });
    form.append(name, el("p", { className: "muted small", textContent: w.decoy_copy_help }),
      el("div", { className: "music-actions" }, make, cancel));
    start.addEventListener("click", () => {
      start.classList.add("hidden");
      form.classList.remove("hidden");
      name.value = fill(w.decoy_copy_default, { name: (copyOf(a) || a).name }).slice(0, 80);
      name.select();
      name.focus();
    });
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!name.value.trim()) return;
      make.disabled = true;
      const unit = scopeUnit();
      try {
        const got = await api().decoy_copy_make(a.member, name.value.trim(), unit, D.copy);
        say(fill(unit ? w.decoy_copy_made_unit : w.decoy_copy_made, { name: got.name, clip: got.clip_name,
                                                                     unit: unit ? D.unit.name : "" }), "ok");
        openAnim(got, got.copy);
      } catch (err) { make.disabled = false; problem(err); }
    });
    return el("div", { className: "da-copy-make" }, start, form);
  }

  // Who plays it: the units that play the animation (the mod's own first), each with a tick, and under one with more
  // than one soldier or part playing it a tick for each (StudioApi.decoy_copy_players, decoy_copy_tick)
  function whoBox() {
    const w = W();
    const search = el("input", { type: "search", value: D.whoQ, placeholder: w.decoy_copy_who_search,
                                 title: w.tip_decoy_copy_who_search });
    search.addEventListener("input", () => { D.whoQ = search.value.trim().toLowerCase(); whoDraw(); });
    return el("fieldset", { className: "da-bones da-who" },
      el("legend", { className: "small", textContent: w.decoy_copy_who }),
      el("p", { className: "small muted", textContent: w.decoy_copy_who_help }), search,
      el("div", { id: "da-who-rows", className: "da-who-rows" }, el("p", { className: "small muted", textContent: w.decoy_anim_loading })));
  }

  async function whoLoad(c) {
    let got;
    try { got = await api().decoy_copy_players(c.copy, D.lang); } catch (err) { problem(err); return; }
    if (!D.anim || D.copy !== c.copy) return;   // (another copy, or another choice, meanwhile)
    D.who = got;
    Object.assign(c, got.copy);
    if (D.anim === c) leadLine(c);   // (a copy opened as itself: how many units play it now)
    whoDraw();
  }

  function whoDraw() {
    const w = W(), got = D.who, rows = $("da-who-rows");
    if (!got || !rows) return;
    const want = D.whoQ.split(/\s+/).filter(Boolean);   // (every word typed, in its name or its country)
    const shownUnits = got.units.filter((u) => want.every((q) => `${u.name} ${u.nation}`.toLowerCase().includes(q)));
    const mine = shownUnits.filter((u) => u.new), theirs = shownUnits.filter((u) => !u.new);
    const out = [];
    if (mine.length) out.push(el("p", { className: "da-who-head", textContent: w.decoy_copy_mine_head }), ...mine.map(whoUnit));
    if (theirs.length) out.push(el("p", { className: "da-who-head", textContent: w.decoy_copy_game_head }), ...theirs.map(whoUnit));
    if (!got.units.length) out.push(el("p", { className: "small muted", textContent: w.decoy_copy_none_play }));
    if (got.unreached.length) {
      out.push(el("p", { className: "small muted", textContent: fill(w.decoy_copy_unreached, { names: got.unreached.join(", ") }) }));
    }
    rows.replaceChildren(...out);
  }

  // one unit's tick, its notes (what it plays instead), and a tick for each of its soldiers or parts that play it
  function whoUnit(u) {
    const w = W();
    const box = el("input", { type: "checkbox", checked: u.ticked === "all", title: w.tip_decoy_copy_unit });
    box.indeterminate = u.ticked === "some";
    box.addEventListener("change", () => whoTick(u, box.checked ? [] : null));
    const figNotes = (f) => [f.own_rows ? w.decoy_copy_own_rows : "",
      f.other ? fill(w.decoy_copy_other, { name: f.other }) : ""].filter(Boolean);
    const notes = [u.own_copy ? w.decoy_copy_own_copy : "", u.own_model ? w.decoy_copy_own_model : "",
      ...(u.figures.length === 1 ? figNotes(u.figures[0]) : [])].filter(Boolean);
    const parts = [el("label", { className: "da-check", title: w.tip_decoy_copy_unit }, box,
      el("span", { textContent: u.nation ? `${u.name} (${u.nation})` : u.name }))];
    if (notes.length) parts.push(el("p", { className: "small muted da-who-note", textContent: notes.join(" · ") }));
    if (u.figures.length > 1) {
      parts.push(el("div", { className: "da-who-figs" }, ...u.figures.map((f) => {
        const tick = el("input", { type: "checkbox", checked: f.ticked, title: w.tip_decoy_copy_figure });
        tick.addEventListener("change", () => {
          const on = u.figures.filter((g) => (g === f ? tick.checked : g.ticked)).map((g) => g.path);
          whoTick(u, on.length ? on : null);
        });
        const said = figNotes(f);
        return el("label", { className: "da-check", title: w.tip_decoy_copy_figure }, tick,
          el("span", { textContent: (w[FIGURE_WORDS[f.kind]] || f.kind) + (f.number ? ` ${f.number}` : "") }),
          ...(said.length ? [el("span", { className: "small muted", textContent: said.join(" · ") })] : []));
      })));
    }
    return el("div", { className: "da-who-unit" }, ...parts);
  }

  // `figures`: [] every soldier and part of the unit that plays it, a list those (their paths), null none
  async function whoTick(u, figures) {
    const w = W(), c = copyOf(D.anim);
    if (!c) return;
    let got;
    try { got = await api().decoy_copy_tick(c.copy, u.address, figures); } catch (err) { problem(err); whoDraw(); return; }
    Object.assign(c, got.copy);
    if (D.anim !== c) scopeChoice(D.anim);   // (a unit's page: Change it for's count of the copy's units)
    say((figures === null ? fill(w.decoy_copy_unticked, { unit: u.name }) : fill(w.decoy_copy_ticked, { unit: u.name, name: c.name }))
      + (got.moved.length ? " " + fill(w.decoy_copy_moved, { names: got.moved.join(", ") }) : ""), "ok");
    whoLoad(c);
  }

  // the speed, stand-in, bones and the way back, as the chosen one (cur) has them
  function animControls(a) {
    const w = W(), c = cur(a), own = Boolean(scopeUnit()), copy = Boolean(copyOf(a));
    $("da-speed").value = String(Math.round(c.speed));
    $("da-speed-value").textContent = `${Math.round(c.speed)}%`;
    if ([...$("da-use").options].some((o) => o.value === (c.from || ""))) $("da-use").value = c.from || "";
    $("da-reset").textContent = copy ? w.decoy_copy_reset : own ? w.decoy_anim_reset_own : w.decoy_anim_reset;
    $("da-reset").title = copy ? w.tip_decoy_copy_reset : own ? w.tip_decoy_anim_reset_own : w.tip_decoy_anim_reset;
    tweaksLine();
    if ($("da-bone").value) boneControls();
  }

  function tweaksLine() {
    const w = W(), t = (D.anim && cur(D.anim).tweaks) || {};
    const bits = Object.entries(t).map(([b, v]) => `${b}: ${Math.round((v.size || 1) * 100)}%` +
      (v.turn ? `, ${v.turn[0].toUpperCase()} ${v.turn[1]}°` : ""));
    $("da-tweaks").textContent = bits.length ? fill(w.decoy_anim_tweaked, { bones: bits.join(" · ") }) : "";
  }

  function boneControls() {
    const t = ((D.anim && cur(D.anim).tweaks) || {})[$("da-bone").value] || {};
    $("da-size").value = String(Math.round((t.size || 1) * 100));
    $("da-size-value").textContent = `${$("da-size").value}%`;
    $("da-axis").value = t.turn ? t.turn[0] : "z";
    $("da-turn").value = String(t.turn ? t.turn[1] : 0);
    $("da-turn-value").textContent = `${$("da-turn").value}°`;
  }

  async function saveAnim(change) {
    const w = W(), a = D.anim;
    if (!a) return;
    const unit = scopeUnit(), copy = copyOf(a);
    try {
      const got = await api().decoy_anim_set(a.member, change.speed ?? null, change.use ?? null, change.bone ?? null,
                                             change.size ?? null, change.turn ?? null, unit, D.copy);
      Object.assign(copy || a, got);
      tweaksLine();
      say(copy ? fill(w.decoy_copy_saved, { name: copy.name })
        : unit ? fill(w.decoy_anim_saved_own, { name: a.name, unit: D.unit.name }) : fill(w.decoy_anim_saved, { name: a.name }), "ok");
      showClip(a);
    } catch (err) { problem(err); }
  }

  // "Music and jingles": the game's songs by where they play, as the Music tab showed them, each with its volume
  async function songs() {
    let vols = {};
    try { vols = await api().decoy_volumes(); } catch (err) { problem(err); }
    window.SoundView.musicInto($("decoy-rows"), D.words, D.lang,
      (s) => { s.volume = vols[s.member] ?? 100; return volumeBits(s); },
      () => shown() && !D.unit && D.kind === "music",
      async (data) => {   // the music files no song of the game names (jingles), each with its own row
        const named = new Set(data.groups.flatMap((g) => g.songs.map((s) => s.member)));
        let got;
        try { got = await api().decoy_list("music", "", null, null, D.lang, 0, 500); } catch (err) { problem(err); return; }
        const rest = got.rows.filter((s) => !named.has(s.member));
        if (!rest.length || !(shown() && !D.unit && D.kind === "music")) return;
        $("decoy-rows").append(el("div", { className: "group" }, el("h2", { textContent: W().decoy_music_other }),
          el("p", { className: "muted small", textContent: W().tip_decoy_music_other }),
          el("div", { className: "music-list" }, ...rest.map(row))));
      });
  }

  function row(s) {
    const w = W();
    const head = el("div", { className: "music-head" });
    const said = s.said ? `“${s.said}”` : "";
    head.append(el("span", { className: "music-name", textContent: said || s.name }),
                el("span", { className: "muted small", textContent: shortClock(s.seconds) }));
    if (s.mine) head.append(el("span", { className: "music-mine small", textContent: w.music_yours }));
    const info = [];
    const spoken = ["dialogue", "unit_voices", "hq_voices", "radio"].includes(s.kind || D.kind);
    if (s.moment) info.push(w[`voice_moment_${s.moment.toLowerCase()}`] || s.moment);   // a unit's line: Move, Attack…
    if (said || spoken) {   // a spoken line: its file and language, and the mission it's in
      const m = s.mission && D.data ? D.data.missions.find((x) => x.id === s.mission) : null;
      info.push([said ? s.name : "", s.lang ? (w[LANGS[s.lang]] || s.lang) : "", m ? m.name : ""].filter(Boolean).join(" · "));
    } else if (s.grouped) {   // an effect: how loud the game plays it, and how many share that
      info.push(fill(s.shared === 1 ? w.decoy_group_shared_one : s.shared ? w.decoy_group_shared : w.decoy_group,
                     { pct: s.group_volume, n: s.shared }));
    }
    if (s.role) info.unshift(w[`decoy_role_${s.role}`] || s.role);   // a unit's: engine, idle, voice line…
    const sub = el("div", { className: "muted small music-where", textContent: info.filter(Boolean).join(" · ") });

    const vol = volumeBits(s);
    const playBtn = el("button", { type: "button", className: "small", textContent: "▶ " + w.music_play, title: w.tip_decoy_play });
    playBtn.addEventListener("click", () => play(playBtn, s, s.volume, false));
    // replace in sound.js's editor, play the mod's own, take it out
    const edit = el("button", { type: "button", className: "small primary", textContent: s.mine ? w.music_change : w.decoy_replace,
                                title: w.tip_decoy_replace });
    edit.addEventListener("click", () => window.SoundView.openEditor({ ...s, decoy: true, also: [], maps: [] },
      () => open(D.words, D.lang), D.words, D.lang));
    const actions = el("div", { className: "music-actions" }, playBtn, ...vol, edit);
    if (s.mine) {
      const mine = el("button", { type: "button", className: "small", textContent: "▶ " + w.music_play_yours });
      mine.addEventListener("click", () => play(mine, s, s.volume, true));
      const reset = el("button", { type: "button", className: "link small", textContent: w.music_reset, title: w.tip_music_reset });
      reset.addEventListener("click", async () => {
        window.SoundView.stop();
        try { await api().music_reset(s.member); say(fill(w.decoy_back_done, { name: s.name }), "ok"); open(D.words, D.lang); }
        catch (err) { problem(err); }
      });
      actions.append(mine, reset);
    }
    const r = el("div", { className: "music-row" + (s.mine || s.volume !== 100 ? " edited" : "") }, head, sub, actions);
    s.rowEl = r;
    return r;
  }

  // a sound's volume: the slider between − and +, its % beside it, Back to 100% when changed; saved when let go
  function volumeBits(s) {
    const w = W();
    if (s.volume === undefined) s.volume = 100;
    const slider = el("input", { type: "range", min: "0", max: "200", step: "5", value: String(s.volume),
                                 className: "decoy-volume", title: w.tip_decoy_volume });
    slider.dataset.stepper = "beside";   // the slider itself between − and + (app.js stepperOf)
    const value = el("span", { className: "decoy-pct", textContent: `${s.volume}%` });
    const back = el("button", { type: "button", className: "link small", textContent: w.decoy_back_100, title: w.tip_decoy_back_100 });
    back.classList.toggle("hidden", s.volume === 100);
    slider.addEventListener("input", () => { value.textContent = `${slider.value}%`; });
    slider.addEventListener("change", () => setVolume(s, Number(slider.value), value, back));
    back.addEventListener("click", () => { slider.value = "100"; value.textContent = "100%"; setVolume(s, 100, value, back); });
    return [el("label", { className: "decoy-slider", title: w.tip_decoy_volume },
               el("span", { className: "small", textContent: w.decoy_volume }), slider, value), back];
  }

  async function setVolume(s, pct, value, back) {
    const w = W();
    try {
      await api().decoy_volume(s.member, pct);
      s.volume = pct;
      value.textContent = `${pct}%`;
      back.classList.toggle("hidden", pct === 100);
      if (s.rowEl) s.rowEl.classList.toggle("edited", Boolean(s.mine) || pct !== 100);
      say(fill(pct === 100 ? w.decoy_volume_back : w.decoy_volume_saved, { name: s.name, pct }), "ok");
      clearTimeout(D.timer);
      D.timer = setTimeout(() => api().decoy(D.lang).then((d) => { D.data = d; kinds(); }).catch(() => {}), 400);
    } catch (err) { problem(err); }
  }

  async function play(btn, s, pct, mine) {
    const w = W();
    if (btn.dataset.playing) { window.SoundView.stop(); return; }
    const label = btn.textContent;
    btn.disabled = true;
    btn.textContent = w.music_reading;
    let buffer;
    try { buffer = mine ? await window.SoundView.modBuffer(s.member) : await window.SoundView.gameBuffer(s.member); }
    catch (err) { btn.disabled = false; btn.textContent = label; problem(err); return; }
    btn.disabled = false;
    btn.textContent = "■ " + w.music_stop;
    btn.dataset.playing = "1";
    window.SoundView.playAt(buffer, pct, () => { delete btn.dataset.playing; btn.textContent = label; });
  }

  async function setAll() {
    const w = W();
    const pct = Number($("decoy-all").value);
    const perLang = D.kind === "dialogue" || D.kind === "hq_voices";
    const n = D.unit ? D.unit.count : D.kind === "music" ? (D.data.kinds.find((k) => k.id === "music") || {}).count : D.total;
    const what = D.unit ? D.unit.name : (w[`decoy_kind_${D.kind}`] || D.kind);
    if (!window.confirm(fill(w.decoy_all_confirm, { n: (n || 0).toLocaleString(), pct, kind: what }))) return;
    try {
      const got = D.unit ? await api().decoy_unit_volume(D.unit.address, pct)
        : await api().decoy_volume_all(D.kind, pct, D.kind === "dialogue" ? (D.mission || null) : null,
                                       perLang ? (D.in_lang || null) : null);
      say(fill(w.decoy_all_done, { n: got.count.toLocaleString(), pct }), "ok");
      await open(D.words, D.lang);
    } catch (err) { problem(err); }
  }

  function wire() {
    if (!document.getElementById("decoy-view")) return;
    let typing = null;
    $("decoy-search").addEventListener("input", () => {
      clearTimeout(typing);
      typing = setTimeout(() => { D.words_q = $("decoy-search").value.trim(); list(true); }, 250);
    });
    $("decoy-mission").addEventListener("change", () => { D.mission = $("decoy-mission").value; list(true); });
    $("decoy-lang").addEventListener("change", () => { D.in_lang = $("decoy-lang").value; list(true); });
    $("decoy-more").addEventListener("click", () => list(false));
    $("decoy-all").addEventListener("input", () => { $("decoy-all-value").textContent = `${$("decoy-all").value}%`; });
    $("decoy-all-set").addEventListener("click", setAll);
    // the animation editor: every change saved at once, the 3D view made again as the build will make the clip
    $("da-speed").addEventListener("input", () => { $("da-speed-value").textContent = `${$("da-speed").value}%`; });
    $("da-speed").addEventListener("change", () => saveAnim({ speed: Number($("da-speed").value) }));
    $("da-use").addEventListener("change", () => saveAnim({ use: $("da-use").value }));
    $("da-bone").addEventListener("change", boneControls);
    $("da-size").addEventListener("input", () => { $("da-size-value").textContent = `${$("da-size").value}%`; });
    $("da-size").addEventListener("change", () => saveAnim({ bone: $("da-bone").value, size: Number($("da-size").value) / 100 }));
    $("da-turn").addEventListener("input", () => { $("da-turn-value").textContent = `${$("da-turn").value}°`; });
    const turn = () => saveAnim({ bone: $("da-bone").value, turn: Number($("da-turn").value) ? [$("da-axis").value, Number($("da-turn").value)] : [] });
    $("da-turn").addEventListener("change", turn);
    $("da-axis").addEventListener("change", () => { if (Number($("da-turn").value)) turn(); });
    $("da-reset").addEventListener("click", async () => {
      const a = D.anim, unit = scopeUnit();
      if (!a) return;
      const copy = copyOf(a);
      try {
        const got = await api().decoy_anim_reset(a.member, unit, D.copy);
        if (copy) Object.assign(copy, got);   // (the copy plays the game's clip again, still ticked as it was)
        else if (unit) a.own = null;   // (it plays the clip as every unit does: the controls show that)
        else Object.assign(a, { speed: 100, from: null, tweaks: {}, changed: false, mine: false });
        animControls(a); showClip(a);
        say(copy ? fill(W().decoy_copy_reset_done, { name: copy.name })
          : unit ? fill(W().decoy_anim_reset_own_done, { name: a.name, unit: D.unit.name })
            : fill(W().decoy_anim_reset_done, { name: a.name }), "ok");
      } catch (err) { problem(err); }
    });
    $("da-close").addEventListener("click", () => $("decoy-anim").close());
    $("da-mc-pick").addEventListener("click", () => $("da-mc-file").click());
    $("da-mc-file").addEventListener("change", mocapPicked);
    $("da-mc-from").addEventListener("input", mocapLabels);
    $("da-mc-len").addEventListener("input", mocapLabels);
    $("da-mc-watch").addEventListener("click", mocapWatch);
    $("da-mc-use").addEventListener("click", mocapUse);
    $("da-lib-kind").addEventListener("change", () => { LIB.kind = $("da-lib-kind").value; libLoad(true); });
    $("da-lib-search").addEventListener("input", () => {
      clearTimeout(LIB.timer);
      LIB.timer = setTimeout(() => { LIB.words = $("da-lib-search").value.trim(); libLoad(true); }, 250);
    });
    $("da-lib-more").addEventListener("click", () => libLoad(false));
    $("da-lib-get").addEventListener("click", libGetSet);
    $("decoy-anim").addEventListener("close", () => {
      V.mixer = null; D.anim = null; D.copy = null; D.who = null;
      open(D.words, D.lang);
    });
    $("decoy-anim").addEventListener("keydown", (e) => e.stopPropagation());
  }

  window.DecoyView = {
    open(words, lang) { return open(words, lang); },
    setWords(words, lang) { open(words, lang); },
    modChanged() { open(D.words, D.lang); },
    leave() { if (window.SoundView) window.SoundView.stop(); },
    // a unit's page: "Sounds and animation" opens here on that unit's own sounds (StudioApi.decoy_unit_list)
    unit(address, name, count) { D.unit = { address, name, count }; D.kind = null; D.blender = null; D.said = null; },
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire); else wire();
})();
