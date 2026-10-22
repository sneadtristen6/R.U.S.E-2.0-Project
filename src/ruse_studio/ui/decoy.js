// RUSE Decoy, the sound and animation designer (StudioApi.decoy / decoy_list / decoy_volume / decoy_volume_all /
// decoy_volumes, rusemod.soundlist, rusemod.sound): every sound the game has, by kind (weapons near and far, impacts,
// engines, surroundings, map backgrounds, the interface, the ruse cards, unit voices, the HQ's lines, radio, mission
// dialogue, music); each heard, made louder or quieter from 0 to 200% of the game's (saved in the mod's
// files/sound/volume.toml; the build makes the sound again at it), and replaced in sound.js's editor. A mission's
// lines show what they say, in the Studio's language. "Music and jingles" is the game's songs by where they play
// (sound.js musicInto: where the Music tab was), each with its volume too. A unit's page opens it on that unit's own
// sounds (showUnitSounds). Uses app.js's $, el, fill, say, problem and api.
(function () {
  "use strict";
  const D = { words: {}, lang: "base", data: null, kind: null, words_q: "", mission: "", in_lang: "", rows: [],
              total: 0, start: 0, timer: null, unit: null, mode: "sound", akind: null, adata: null, anim: null };
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
    const music = !D.unit && !anims && D.kind === "music";
    for (const id of ["decoy-search", "decoy-count", "decoy-more"]) $(id).classList.toggle("hidden", music || (id === "decoy-search" && Boolean(D.unit)));
    for (const id of ["decoy-all-set"]) $(id).classList.toggle("hidden", anims);
    $("decoy-all").closest("label").classList.toggle("hidden", anims);
    $("decoy-kind-help").textContent = D.unit ? fill(w.decoy_unit_help_all, { name: D.unit.name })
      : anims ? (w[`tip_decoy_akind_${D.akind}`] || "") : (w[`tip_decoy_kind_${D.kind}`] || "");
    $("decoy-all").value = "100";
    $("decoy-all-value").textContent = "100%";
    if (music) { await songs(); return; }
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
          ...got.rows.map(animRow));
      }
    }
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

  function animRow(a) {
    const w = W();
    const head = el("div", { className: "music-head" },
      el("span", { className: "music-name", textContent: a.name }),
      el("span", { className: "muted small", textContent: `${a.seconds.toFixed(1)} s` }));
    const marks = [];
    if (a.speed !== 100) marks.push(fill(w.decoy_anim_speed_mark, { pct: Math.round(a.speed) }));
    if (a.from) marks.push(w.decoy_anim_from_mark);
    if (Object.keys(a.tweaks || {}).length) marks.push(fill(w.decoy_anim_bones_mark, { n: Object.keys(a.tweaks).length }));
    if (a.mine) marks.push(w.music_yours);
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
    return el("div", { className: "music-row" + (a.changed ? " edited" : "") }, head,
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
    try { got = await api().decoy_anim_preview(a.member); } catch (err) { $("da-note").textContent = (err && err.message) || String(err); return; }
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
    try {
      const got = await api().decoy_mocap_use(...mocapArgs(), $("da-mc-credit").value.trim());
      Object.assign(a, got);
      say(fill(w.decoy_mc_used, { name: a.name }), "ok");
      showClip(a);
    } catch (err) { problem(err); }
  }

  async function openAnim(a) {
    const w = W();
    D.anim = a;
    window.SoundView.stop();
    $("da-title").textContent = a.name;
    $("da-lead").textContent = [a.names.length ? fill(w.decoy_anim_names, { names: a.names.join(", ") }) : "",
      a.units ? fill(w.decoy_anim_units, { n: a.units }) : w.decoy_anim_no_units].filter(Boolean).join(" · ");
    for (const [id, word] of [["da-speed-label", "decoy_anim_speed"], ["da-use-label", "decoy_anim_use"],
      ["da-bones-label", "decoy_anim_bones"], ["da-size-label", "decoy_anim_size"], ["da-axis-label", "decoy_anim_axis"],
      ["da-turn-label", "decoy_anim_turn"], ["da-reset", "decoy_anim_reset"], ["da-close", "decoy_anim_done"]]) $(id).textContent = w[word];
    for (const [id, tip] of [["da-speed", "tip_decoy_anim_speed"], ["da-use", "tip_decoy_anim_use"], ["da-bone", "tip_decoy_anim_bone"],
      ["da-size", "tip_decoy_anim_size"], ["da-axis", "tip_decoy_anim_axis"], ["da-turn", "tip_decoy_anim_turn"],
      ["da-reset", "tip_decoy_anim_reset"]]) $(id).title = w[tip];
    $("da-speed").value = String(Math.round(a.speed));
    $("da-speed-value").textContent = `${Math.round(a.speed)}%`;
    $("da-use").replaceChildren(el("option", { value: "", textContent: w.decoy_anim_use_own }));
    $("da-bone").replaceChildren();
    tweaksLine();
    mocapWords();
    $("decoy-anim").showModal();
    showClip(a);
    let info;
    try { info = await api().decoy_anim_info(a.member); } catch (err) { problem(err); return; }
    $("da-use").append(...info.same.map((s) => el("option", { value: s.member,
      textContent: s.name + (s.names.length ? ` (${s.names.slice(0, 2).join(", ")})` : "") })));
    $("da-use").value = a.from || "";
    a.loops = info.loops;
    $("da-mc-loop").checked = info.loops;
    $("da-mc-label").closest("fieldset").classList.toggle("hidden", !info.mocap);
    $("da-bone").append(...info.bones.map((b) => el("option", { value: b, textContent: b })));
    const head = info.bones.find((b) => b.endsWith(" head"));
    $("da-bone").value = head || info.bones[0] || "";
    boneControls();
  }

  function tweaksLine() {
    const w = W(), t = (D.anim && D.anim.tweaks) || {};
    const bits = Object.entries(t).map(([b, v]) => `${b}: ${Math.round((v.size || 1) * 100)}%` +
      (v.turn ? `, ${v.turn[0].toUpperCase()} ${v.turn[1]}°` : ""));
    $("da-tweaks").textContent = bits.length ? fill(w.decoy_anim_tweaked, { bones: bits.join(" · ") }) : "";
  }

  function boneControls() {
    const t = ((D.anim && D.anim.tweaks) || {})[$("da-bone").value] || {};
    $("da-size").value = String(Math.round((t.size || 1) * 100));
    $("da-size-value").textContent = `${$("da-size").value}%`;
    $("da-axis").value = t.turn ? t.turn[0] : "z";
    $("da-turn").value = String(t.turn ? t.turn[1] : 0);
    $("da-turn-value").textContent = `${$("da-turn").value}°`;
  }

  async function saveAnim(change) {
    const w = W(), a = D.anim;
    if (!a) return;
    try {
      const got = await api().decoy_anim_set(a.member, change.speed ?? null, change.use ?? null, change.bone ?? null,
                                             change.size ?? null, change.turn ?? null);
      Object.assign(a, got);
      tweaksLine();
      say(fill(w.decoy_anim_saved, { name: a.name }), "ok");
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
      const a = D.anim;
      if (!a) return;
      try {
        await api().decoy_anim_reset(a.member);
        Object.assign(a, { speed: 100, from: null, tweaks: {}, changed: false, mine: false });
        $("da-speed").value = "100"; $("da-speed-value").textContent = "100%"; $("da-use").value = "";
        boneControls(); tweaksLine(); showClip(a);
        say(fill(W().decoy_anim_reset_done, { name: a.name }), "ok");
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
    $("decoy-anim").addEventListener("close", () => { V.mixer = null; D.anim = null; open(D.words, D.lang); });
    $("decoy-anim").addEventListener("keydown", (e) => e.stopPropagation());
  }

  window.DecoyView = {
    open(words, lang) { return open(words, lang); },
    setWords(words, lang) { open(words, lang); },
    modChanged() { open(D.words, D.lang); },
    leave() { if (window.SoundView) window.SoundView.stop(); },
    // a unit's page: "Sounds and animation" opens here on that unit's own sounds (StudioApi.decoy_unit_list)
    unit(address, name, count) { D.unit = { address, name, count }; D.kind = null; },
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire); else wire();
})();
