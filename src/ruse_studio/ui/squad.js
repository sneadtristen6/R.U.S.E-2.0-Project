// A squad's page starts with its soldiers (the owner, 2026-11-11, on the page before: "so stupidly laid out", "a ton of
// scrolling", "squint down at this tiny text", "so many things that say change it in Blender, bring back the model.
// It's overwhelming"; who it is for: someone "not very good with computers", "an older person", who wants the GIs to
// "look more like Marines": "very easy to either change the whole squad at once ... or be able to change each one
// individually"; his "Yes, it matches" to the squad contracts' list the same night). Full width at the top of the page:
//
// - the squad card: the squad in 3D (the page's own view, with its Use this view as the card), its name, what it is
//   made of (squad_info's line), and ONE big button, Open in Blender (the one Blender button, ruse_studio.oneblender:
//   the owner, 2026-11-13, "you can either take the whole unit or ... select which ones you want to bring into
//   Blender"): what's ticked under it (its soldiers, its model, its bones, its paint) in one Blender, the soldiers side
//   by side; change one and only he changes. While its Blender is open the same place reads Bring my changes back, and
//   afterwards the card says who changed and who didn't, and what unticked was kept. Test in game beside it.
// - a line per soldier: his picture, his name and how many ("Rifleman ×4"), what he fires, Import a model… (his model
//   from a file) and, once he has one, Back to the game's look.
// - More options, small, last: where the files are kept, each soldier's model and what of it won't work in the game.
//
// A game squad's card says why its soldiers aren't changed here, with the page's way to a new unit from it. Add a
// soldier and Remove are drawn only when squad_info's "can" says so, and when it can't, its "limits" say why in a plain
// sentence (at most 8 soldiers for now, at least 2: the owner's picks of 2026-11-12). Each squad its own soldiers, each
// his own look: one line per soldier ("Soldier 3: Rifleman"); Add a soldier opens Blender with just him, and he joins
// the squad when Bring my changes back brings him; −1 and +1 above it take one away or add one at once, no Blender
// (the owner, 2026-11-12). The squad's uniform stays in the Look and moves section beside the values (app.js
// lookMovesBox, its row then named Uniform). Calls: StudioApi.squad_info, blender_parts, blender_open, blender_back,
// soldier_import, soldier_reset, soldier_add, soldier_remove (the squad contracts' section 4), soldier_plus,
// soldier_minus, look, units. Uses app.js's el, fill, say, stayToast, problem, api, state, keptRow, fitBox,
// alphaLostLines, notKeptSaid, sayBroughtBack, oneBlenderTicks, oneKeptSaid and testInGame; app.js's showUnit puts it on
// the page when squad_info answers for the unit.
(function () {
  "use strict";

  function W() { return state.words || {}; }

  // squad_info for a unit's page: its soldiers, null for a unit that isn't a squad (and in a Studio without the call:
  // the page as it was), or { error } when it couldn't be read (showUnit says so, and draws the page as it was)
  async function infoOf(address) {
    if (typeof api().squad_info !== "function") return null;
    try { return (await api().squad_info(address, state.lang)) || null; }
    catch (err) { return { error: (err && err.message) || String(err) }; }
  }

  // --- each soldier's picture: his model (squad_info's preview, a .glb as the 3D view draws them) drawn once, small and
  // off the page, from the front corner as the 3D view first shows a unit; a plain figure while it's drawn, and when it
  // can't be (no preview, or the 3D library, which comes from the internet, couldn't load) ---
  const FACE_W = 96, FACE_H = 120;   // (drawn twice as big, then shown at this size: smoother)
  const PLAIN = '<svg viewBox="0 0 48 60" aria-hidden="true"><circle cx="24" cy="10" r="7"/>'
    + '<path d="M13 21h22l3 17h-6l-2 20h-6l-1-13-1 13h-6l-2-20h-6z"/></svg>';
  const faces = new Map();   // a preview's address -> its picture, a PNG data address (or null)
  let painter = null;        // one small renderer for every picture, made when the first is drawn

  function faceOf(url) {
    if (!faces.has(url)) faces.set(url, drawFace(url).catch(() => null));
    return faces.get(url);
  }

  async function drawFace(url) {
    const THREE = await import("three");
    if (!painter) {
      const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
      renderer.setPixelRatio(1);
      renderer.setSize(FACE_W * 2, FACE_H * 2, false);
      const scene = new THREE.Scene();
      scene.add(new THREE.HemisphereLight(0xeef3f8, 0x4a4234, 2.2));
      const sun = new THREE.DirectionalLight(0xfff4e0, 2.4);
      sun.position.set(3, 5, 4);
      const camera = new THREE.PerspectiveCamera(30, FACE_W / FACE_H, 0.01, 1000);
      camera.add(new THREE.DirectionalLight(0xffffff, 0.8));   // (a little light from where we look, as the 3D view)
      scene.add(sun, camera);
      painter = { renderer, scene, camera, loader: new GLTFLoader() };
    }
    const { renderer, scene, camera, loader } = painter;
    const g = await loader.loadAsync(url);
    scene.add(g.scene);
    try {
      g.scene.updateMatrixWorld(true);
      const bounds = new THREE.Box3().setFromObject(g.scene);
      if (bounds.isEmpty()) return null;
      const centre = bounds.getCenter(new THREE.Vector3());
      const radius = Math.max(bounds.getSize(new THREE.Vector3()).length() / 2, 0.01);
      const half = Math.atan(Math.tan(camera.fov * Math.PI / 360) * Math.min(1, camera.aspect));
      camera.near = radius / 100;
      camera.far = radius * 20;
      camera.updateProjectionMatrix();
      camera.position.copy(centre).add(new THREE.Vector3(0.85, 0.42, 0.85).normalize()
        .multiplyScalar(radius / Math.sin(half) * 0.92));
      camera.lookAt(centre);
      renderer.render(scene, camera);
      return renderer.domElement.toDataURL("image/png");
    } finally {
      scene.remove(g.scene);
      g.scene.traverse((o) => {
        if (!o.isMesh) return;
        o.geometry.dispose();
        for (const m of [].concat(o.material)) { if (m.map) m.map.dispose(); m.dispose(); }
      });
    }
  }

  // a soldier's picture in `box`: the plain figure, then his model's once it's drawn
  function putFace(box, s) {
    const plain = el("span", { className: "squad-face-plain" });
    plain.innerHTML = PLAIN;   // (the page's own drawing, nothing from outside)
    box.replaceChildren(plain);
    if (!s.preview || !s.preview.url) return;
    faceOf(s.preview.url).then((png) => {
      if (png && box.isConnected) box.replaceChildren(el("img", { src: png, alt: s.label }));
    });
  }

  // "Soldier 3: Rifleman", and what he fires ("Soldier 5: Bazooka man, fires Bazooka"): one line per soldier (each squad
  // its own soldiers, each his own look); a line for several of one kind ("Rifleman ×4") from a Studio that had those
  function soldierWords(s) {
    const w = W(), fires = (s.fires || []).filter(Boolean);
    if (s.number != null) {
      return fill(fires.length ? w.squad_soldier_one_fires : w.squad_soldier_one,
        { who: s.label, n: s.number, weapons: fires.join(", ") });
    }
    return fill(fires.length ? w.squad_soldier_fires : w.squad_soldier,
      { who: s.label, n: s.count, weapons: fires.join(", ") });
  }

  // a soldier's name alone ("Soldier 3: Rifleman"; "Rifleman ×4" for a line of several)
  function soldierName(s) {
    const w = W();
    return s.number != null ? fill(w.squad_soldier_one, { who: s.label, n: s.number })
      : fill(w.squad_soldier, { who: s.label, n: s.count });
  }

  // the folder a file or folder is in (a path as the Studio gives it, \ or /)
  const folderOf = (path) => String(path || "").replace(/[\\/]+$/, "").replace(/[\\/][^\\/]*$/, "");

  // --- the squad's part of its page, above its values. `first`: squad_info's answer for it; `page`: the page's 3D view
  // (view, put on the card), its Look and moves section (looks: read again after a change here) and its New unit form's
  // opener (startNew, a game squad's way to a squad of its own) ---
  function section(u, first, page) {
    const address = u.address;
    const S = { info: first, look: null, said: null, busy: false, adding: null, sure: null };
    const box = el("section", { className: "squad" });
    const picture = el("div", { className: "squad-picture" });
    if (page.view) picture.append(page.view);
    const words = el("div", { className: "squad-words" });
    // (its words and big button first: on a narrow window, where the picture goes under them, they are still in sight)
    const card = el("div", { className: "squad-card" }, words, picture);
    const lines = el("div", { className: "squad-soldiers" });
    const opened = state.squadMore === true;   // (More options as it was left, from one squad to the next)
    const moreToggle = el("button", { type: "button", className: "ghost small squad-more-toggle", title: W().tip_squad_more });
    moreToggle.addEventListener("click", () => { state.squadMore = moreBody.classList.contains("hidden"); showMore(); });
    const moreBody = el("div", { className: "squad-more-body" + (opened ? "" : " hidden") });
    box.append(card, lines, el("div", { className: "squad-more" }, moreToggle, moreBody));
    const mine = () => !S.info.why_not && S.info.own !== false;   // (a squad of this mod's own: its soldiers change here)

    const showMore = () => {
      const w = W(), on = state.squadMore === true;
      moreBody.classList.toggle("hidden", !on);
      moreToggle.textContent = on ? w.squad_less : w.squad_more;
      moreToggle.title = on ? w.tip_squad_less : w.tip_squad_more;
      moreToggle.setAttribute("aria-expanded", String(on));
    };

    // --- the card ---
    const drawCard = () => {
      const w = W(), info = S.info;
      const parts = [el("h2", { className: "squad-name", textContent: info.name || u.name }),
        el("p", { className: "squad-line", textContent: info.line || "" })];
      if (!mine()) {
        // a game squad: what it is, why its soldiers aren't changed here, and the page's way to a new unit from it
        const go = el("button", { type: "button", className: "primary squad-big", textContent: w.model_want_button,
          title: w.tip_model_want, disabled: !page.startNew });
        if (page.startNew) go.addEventListener("click", page.startNew);
        parts.push(el("p", { className: "squad-why", textContent: info.why_not || w.squad_game }),
          el("div", { className: "squad-go" }, go));
      } else parts.push(...blenderParts());
      if (mine()) parts.push(countParts());
      if (mine() && info.can && info.can.add) parts.push(...addParts());
      // (why there's no Add a soldier: the most soldiers a squad has, said)
      else if (mine() && info.limits && info.limits.add) parts.push(el("p", { className: "squad-limit", textContent: info.limits.add }));
      words.replaceChildren(...parts);
    };

    // the big button: Open in Blender with what's ticked under it, or Bring my changes back while its Blender is open;
    // without Blender on the PC, the way to get it
    const blenderParts = () => {
      const w = W(), info = S.info, can = info.can || {};
      const open = Boolean(info.blender && info.blender.open) || Boolean(S.parts && S.parts.open);
      const missing = Boolean(S.look) && S.look.blender === "" && !open;   // (look(): Blender isn't found on this PC)
      const big = el("button", { type: "button", className: "primary squad-big",
        textContent: open ? w.squad_blender_back : w.look_open, title: open ? w.tip_one_back : w.tip_one_open,
        disabled: S.busy || missing || !can.blender });
      big.addEventListener("click", open ? bringBack : openBlender);
      const test = el("button", { type: "button", className: "squad-test", textContent: w.test_in_game, title: w.tip_test });
      test.addEventListener("click", () => testInGame());
      // (what the last bring-back did, right under the button that did it)
      S.ticks = !open && S.parts && S.parts.can ? oneBlenderTicks(S.parts, S.ticks ? S.ticks.ticks() : null) : null;
      const out = [el("div", { className: "squad-go" }, big, test, ...(S.ticks ? [S.ticks.toggle] : [])),
        ...(S.ticks ? [S.ticks.box] : []), ...(S.said ? [S.said] : []),
        el("p", { className: "squad-how", textContent: open ? w.squad_blender_open_how
          : S.parts && S.parts.route === "kinds" ? w.one_how_model : w.one_how_squad })];   // (one model, or the ticked)
      if (missing) {
        const get = el("button", { type: "button", textContent: w.look_get_blender, title: w.tip_look_get_blender });
        get.addEventListener("click", () => api().get_blender().catch(problem));
        const choose = el("button", { type: "button", className: "ghost", textContent: w.look_choose_blender,
          title: w.tip_look_choose_blender });
        choose.addEventListener("click", async () => {
          try {
            const r = await api().choose_blender();
            if (r.message) say(r.message, "error");
            await reload(false);
          } catch (err) { problem(err); }
        });
        out.push(el("p", { className: "squad-how", textContent: w.squad_blender_needs }),
          el("div", { className: "squad-go" }, get, choose));
      } else if (!open && info.blender && ("waiting" in info.blender ? info.blender.waiting : info.blender.made)) {
        // Blender closed with a sending not brought back yet (squad_info's blender.waiting; without that field, its
        // folder being there): what was last sent from it can still come back (a bring-back takes a closed
        // Blender's last sending; one brought back already changes nothing)
        const again = el("button", { type: "button", className: "ghost squad-again", textContent: w.squad_blender_back,
          title: w.tip_squad_blender_back_closed, disabled: S.busy || !can.blender });
        again.addEventListener("click", bringBack);
        out.push(el("div", { className: "squad-go" }, again));
      }
      return out;
    };

    const openBlender = async () => {
      const w = W();
      const ticks = S.ticks ? S.ticks.ticks() : { model: true };   // (read before the card is drawn again)
      S.busy = true;
      S.said = null;
      drawCard();
      say(w.squad_blender_opening);
      let opened = false;
      try {
        const r = await api().blender_open(address, ticks, state.lang);
        // (the squad's own Blender answers with squad_info, its work folder and who was opened; the model's Blender,
        // the Generic Horse's, with the unit's look, which has soldiers too but no squad's blender: taken as the
        // squad's, the card's redraw threw on it, found in the stand-in page's console 2026-11-13)
        if (r && r.door === "squad" && r.soldiers) S.info = r;
        opened = true;
        say(w.squad_blender_opened, "ok");
      } catch (err) { problem(err); }
      S.busy = false;
      // (read again, so the button reads Bring my changes back: the model's Blender too, the Generic Horse's, whose
      // answer isn't the squad's)
      if (opened) await reload(false);
      else draw();
    };

    // who changed and who didn't, plainly, on the card and in a pop-up
    const bringBack = async () => {
      const w = W();
      S.busy = true;
      S.said = null;
      drawCard();
      say(w.squad_blender_bringing);
      let r = null;
      try { r = await api().blender_back(address, state.lang); } catch (err) { problem(err); }
      S.busy = false;
      if (!r) { draw(); return; }
      await reload(true);
      if (r.door && r.door !== "squad") {   // (the model's Blender, a squad on bones of its own, or the paint's)
        // the model's: whose model it is now (the riflemen's, the heavy-weapon soldier keeping his; or his), what of
        // the modder's it took the place of and what of its shine and side colour it couldn't keep, as the Model row's
        // Bring back the model said them
        const m = (r.door === "model" && r.model) || {};
        const kinds = Boolean(S.parts && S.parts.kinds && S.parts.kinds.length > 1);
        const head = r.door === "paint" ? r.message : r.kind ? fill(w.model_kind_done, { file: m.file || "" })
          : kinds ? w.model_blender_done_kinds : w.model_blender_done;
        const lost = notKeptSaid(m.not_kept);
        const done = [head, lost, oneKeptSaid(r)].filter(Boolean).join(" ");
        S.said = el("p", { className: "squad-result", role: "status", textContent: done });
        if (alphaLostLines(m).length) sayBroughtBack(done, m);
        else say(done, lost ? "" : "ok");
        drawCard();
        return;
      }
      const named = (ids) => (ids || []).map((id) => {
        const s = S.info.soldiers.find((x) => x.id === id) || (r.soldiers || []).find((x) => x.id === id);
        return s ? soldierName(s) : String(id);
      }).join(", ");
      const changed = r.changed || [], same = r.unchanged || [];
      // (Add a soldier's Blender brought back: he joined the squad)
      const text = r.joined ? fill(w.squad_added, { n: r.count }) : !changed.length ? w.squad_back_none : same.length
        ? fill(w.squad_back_some, { changed: named(changed), unchanged: named(same) })
        : fill(w.squad_back_all, { changed: named(changed) });
      // what Blender sent on no soldier, not brought back (its answer's left_out), on the card too
      const left = (r.left_out || []).length ? fill(w.blender_squad_left_out_back, { names: r.left_out.join(", ") }) : "";
      const result = [text, left, oneKeptSaid(r)].filter(Boolean).join(" ");
      S.said = el("p", { className: "squad-result" + (changed.length ? "" : " none"), role: "status", textContent: result });
      // what a soldier brought back couldn't keep of his shine and side colour (his import's report: app.js
      // alphaLostLines), in the pop-up, which then waits to be closed; his line says it too, from squad_info
      const lost = Object.values(r.reports || {}).flatMap((report) => alphaLostLines(report));
      // and what of the modder's a soldier's model brought back took the place of (its report's not_kept: app.js
      // notKeptSaid), as the unit page's Bring back says it (the one check, finding 10)
      const notKept = Object.values(r.reports || {}).map((report) => notKeptSaid(report && report.not_kept))
        .filter(Boolean).filter((t, i, all) => all.indexOf(t) === i);
      lost.push(...notKept);
      if (lost.length || left) stayToast(say([result, ...lost].join(" "), "warn"));
      else say(result, changed.length ? "ok" : "");
      drawCard();
    };

    // --- a line per soldier ---
    const drawLines = () => {
      const w = W(), info = S.info, soldiers = info.soldiers || [];
      // (why there's no Remove: the fewest soldiers a squad keeps, said under its soldiers)
      const limit = mine() && info.limits && info.limits.remove
        ? [el("p", { className: "squad-limit", textContent: info.limits.remove })] : [];
      lines.replaceChildren(...(soldiers.length ? [el("h3", { className: "squad-each", textContent: w.squad_each })] : []),
        ...soldiers.map(soldierLine), ...limit);
    };

    const soldierLine = (s) => {
      const w = W(), info = S.info, can = info.can || {};
      const face = el("div", { className: "squad-face" });
      putFace(face, s);
      const now = !s.own_model ? w.squad_now_game : s.blender_changed ? w.squad_now_blender
        : fill(w.squad_now_file, { file: s.from || "" });
      const acts = el("div", { className: "squad-acts" });
      if (mine()) {
        if (can.import) {
          const pick = el("button", { type: "button", textContent: w.squad_import,
            title: s.count > 1 ? w.tip_squad_import_all : w.tip_squad_import, disabled: S.busy });
          pick.addEventListener("click", () => importFor(s, pick));
          acts.append(pick);
        }
        if (can.reset && s.own_model) {
          const back = el("button", { type: "button", className: "ghost", textContent: w.squad_reset,
            title: w.tip_squad_reset, disabled: S.busy });
          back.addEventListener("click", () => resetOf(s, back));
          acts.append(back);
        }
        if (can.remove) acts.append(...removeParts(s));
      }
      // the parts of his model without their own shine and side colour, and why, for as long as it has them (squad_info
      // says them on the first soldier who wears that model: app.js alphaLostLines)
      const lost = alphaLostLines(s).map((line) => el("span", { className: "squad-lost", textContent: line }));
      return el("div", { className: "squad-soldier" }, face,
        el("div", { className: "squad-who" }, el("strong", { textContent: soldierWords(s) }),
          el("span", { className: "squad-now", textContent: now }), ...lost), acts);
    };

    // his model from a file: the file picker, then what came in said (a Custom uniform it took the place of, too)
    const importFor = async (s, button) => {
      const w = W();
      button.disabled = true;
      say(w.squad_importing);
      try {
        const r = await api().soldier_import(address, s.id);
        if (r && r.model) {   // (none: the file picker was closed)
          say(fill(w.squad_import_done, { who: s.label, file: r.model.file || "" })
            + (r.copy_out ? ` ${w.squad_copy_out}` : ""), "ok");
          S.said = null;
          await reload(true);
          return;
        }
      } catch (err) { problem(err); }
      button.disabled = false;
    };

    // back to the game's look: his model out of the mod, and what went with it said as the page always has ("kinds_out":
    // a soldier whose model was on his model's bones; "copy_back": the Custom uniform his model took the place of)
    const resetOf = async (s, button) => {
      const w = W(), before = S.info.soldiers || [];
      button.disabled = true;
      try {
        const r = await api().soldier_reset(address, s.id);
        const gone = (r.kinds_out || []).map((id) => (before.find((x) => x.id === id) || { label: id }).label);
        say([fill(w.squad_reset_done, { who: s.label }), r.copy_back ? w.squad_reset_uniform : "",
          gone.length ? fill(w.model_kinds_out, { who: gone.join(", ") }) : ""].filter(Boolean).join(" "), "ok");
        S.said = null;
        await reload(true);
      } catch (err) { problem(err); button.disabled = false; }
    };

    // --- Remove on a soldier's line, asked first; never fewer than 2 soldiers, nor than the weapons its last soldiers
    // fire one each (squad_info's can.remove; its limits.remove says why not)
    const removeParts = (s) => {
      const w = W();
      if (S.sure !== s.id) {
        const remove = el("button", { type: "button", className: "ghost danger", textContent: w.squad_remove,
          title: w.tip_squad_remove, disabled: S.busy });
        remove.addEventListener("click", () => { S.sure = s.id; drawLines(); });
        return [remove];
      }
      const yes = el("button", { type: "button", className: "ghost danger", textContent: w.squad_remove_yes,
        title: w.tip_squad_remove_yes, disabled: S.busy });
      const no = el("button", { type: "button", className: "ghost", textContent: w.cancel, title: w.tip_cancel });
      no.addEventListener("click", () => { S.sure = null; drawLines(); });
      yes.addEventListener("click", async () => {
        yes.disabled = true;
        try {
          const r = await api().soldier_remove(address, s.id);
          S.sure = null;
          say([fill(w.squad_removed, { number: s.number != null ? s.number : s.id, n: r && r.count != null ? r.count : "" }),
            r && r.copy_back ? w.squad_reset_uniform : ""].filter(Boolean).join(" "), "ok");
          await reload(true);
        } catch (err) { problem(err); yes.disabled = false; }
      });
      return [el("span", { className: "squad-sure", textContent: fill(w.squad_remove_sure, { who: s.label }) }), yes, no];
    };

    // --- −1 and +1 on the card, at once, no Blender (the owner, 2026-11-12: "I would like to add the +1 button because
    // that seems a lot easier than 4 steps to add 1 unit"; "You should be able to subtract from the base unit. And
    // add."): +1 adds a rifleman before the bazooka man, looking like most of the riflemen; −1 takes out the soldier
    // standing there. Each only when squad_info's "can" says so (its limits say why not: Add a soldier's on the card,
    // Remove's under the soldiers) ---
    const countParts = () => {
      const w = W(), can = S.info.can || {};
      const minus = el("button", { type: "button", className: "squad-count", textContent: w.squad_minus,
        title: w.tip_squad_minus, disabled: S.busy || !can.remove });
      minus.addEventListener("click", () => countBy(-1));
      const plus = el("button", { type: "button", className: "squad-count", textContent: w.squad_plus,
        title: w.tip_squad_plus, disabled: S.busy || !can.add });
      plus.addEventListener("click", () => countBy(1));
      return el("div", { className: "squad-go" }, minus, plus);
    };

    // one soldier more or fewer, said on the card and in a pop-up: how many now, and for −1 a look of his own kept
    // aside and a Custom uniform that came back
    const countBy = async (step) => {
      const w = W();
      S.busy = true;
      S.adding = null;
      drawCard();
      let r = null;
      try { r = step > 0 ? await api().soldier_plus(address) : await api().soldier_minus(address); }
      catch (err) { problem(err); }
      S.busy = false;
      if (!r) { draw(); return; }
      const text = step > 0 ? fill(w.squad_added, { n: r.count })
        : [fill(w.squad_removed, { number: r.removed, n: r.count }), r.look_kept ? w.squad_minus_kept : "",
          r.copy_back ? w.squad_reset_uniform : ""].filter(Boolean).join(" ");
      S.said = el("p", { className: "squad-result", role: "status", textContent: text });
      say(text, "ok");
      await reload(true);
    };

    // --- Add a soldier on the card (squad_info's can.add; its limits.add says why not): a copy of one in this squad, a
    // soldier from another unit picked by his picture, or a model file (the owner, 2026-11-11: "copy an existing unit or
    // import a model, and then that takes you to Blender. And when you bring it back, that unit can be then added to
    // that squad"; his picture of the page: "duplicate one of the existing ... soldiers inside of the GI squad already,
    // or you could then add a model of another unit"): Blender opens with just him, and he joins the squad when Bring
    // my changes back brings him ---
    const addParts = () => {
      const w = W();
      const add = el("button", { type: "button", textContent: w.squad_add, title: w.tip_squad_add, disabled: S.busy });
      add.setAttribute("aria-expanded", String(Boolean(S.adding)));
      add.addEventListener("click", () => { S.adding = S.adding ? null : { step: "how" }; drawCard(); });
      return [el("div", { className: "squad-go" }, add), ...(S.adding ? [addPanel()] : [])];
    };

    const addPanel = () => {
      const w = W(), A = S.adding;
      const panel = el("div", { className: "squad-add" });
      const cancel = el("button", { type: "button", className: "ghost", textContent: w.cancel, title: w.tip_cancel });
      cancel.addEventListener("click", () => { S.adding = null; drawCard(); });
      const way = (label, tip, act) => {
        const b = el("button", { type: "button", textContent: label, title: tip, disabled: S.busy });
        b.addEventListener("click", act);
        return b;
      };
      if (A.step === "how") {
        panel.append(el("p", { textContent: w.squad_add_how }), el("div", { className: "squad-go" },
          way(w.squad_add_copy, w.tip_squad_add_copy, () => { S.adding = { step: "copy" }; drawCard(); }),
          way(w.squad_add_unit, w.tip_squad_add_unit, () => { S.adding = { step: "unit" }; drawCard(); listSquads(); }),
          way(w.squad_add_file, w.tip_squad_add_file, () => addSoldier("file")), cancel));
      } else if (A.step === "copy") {   // one of this squad, by his picture
        panel.append(el("p", { textContent: w.squad_add_pick }),
          el("div", { className: "squad-picks" }, ...(S.info.soldiers || []).map((s) => pickOf(s, () => addSoldier("copy", s.id)))),
          el("div", { className: "squad-go" }, cancel));
      } else {   // another unit: which squad, then which of its soldiers, by his picture
        const units = el("select", { title: w.tip_squad_add_unit_pick, disabled: !A.units || !A.units.length });
        units.setAttribute("aria-label", w.squad_add_unit_pick);
        units.append(el("option", { value: "", disabled: true, selected: !A.unit,
          textContent: !A.units ? w.squad_add_loading : A.units.length ? w.squad_add_unit_pick : w.squad_add_none }));
        for (const x of A.units || []) units.append(el("option", { value: x.address, textContent: x.name, selected: x.address === A.unit }));
        units.addEventListener("change", () => showSquad(units.value));
        panel.append(el("div", { className: "squad-add-unit" }, units));   // (its first line asks: From which unit?)
        if (A.soldiers) {
          panel.append(el("p", { textContent: w.squad_add_pick }), el("div", { className: "squad-picks" },
            ...A.soldiers.map((s) => pickOf(s, () => addSoldier("unit", s.id, A.unit)))));
        }
        panel.append(el("div", { className: "squad-go" }, cancel));
      }
      return panel;
    };

    // a soldier to pick, as his picture with his name under it
    const pickOf = (s, act) => {
      const w = W();
      const face = el("span", { className: "squad-face" });
      putFace(face, s);
      const b = el("button", { type: "button", className: "squad-pick", title: fill(w.tip_squad_add_pick, { who: soldierName(s) }),
        disabled: S.busy }, face, el("span", { textContent: soldierName(s) }));
      b.addEventListener("click", act);
      return b;
    };

    // the other squads (the Units tab's infantry, this one left out), for a soldier from another unit
    const listSquads = async () => {
      let res = null;
      try { res = await api().units(state.lang, "infantry", -1, "", "all"); } catch (err) { problem(err); }
      if (!S.adding || S.adding.step !== "unit") return;
      S.adding.units = ((res && res.units) || []).filter((x) => x.address !== address)
        .map((x) => ({ address: x.address, name: x.name }));
      drawCard();
    };

    const showSquad = async (other) => {
      if (!S.adding) return;
      S.adding.unit = other;
      S.adding.soldiers = null;
      drawCard();
      let r = null;
      try { r = await api().squad_info(other, state.lang); } catch (err) { problem(err); }
      if (!S.adding || S.adding.unit !== other) return;
      S.adding.soldiers = (r && r.soldiers) || [];
      if (!r) say(W().squad_add_none, "error");
      drawCard();
    };

    // Blender opens with just him (squad_info back, its Blender open: the big button reads Bring my changes back, which
    // brings him into the squad); none back: the file picker was closed
    const addSoldier = async (source, of = null, unit = null) => {
      const w = W();
      S.busy = true;
      drawCard();
      try {
        const r = await api().soldier_add(address, source, of, unit, null);
        S.adding = null;
        if (r && r.soldiers) {
          S.info = r;
          say(w.squad_add_opened, "ok");
        }
      } catch (err) { problem(err); }
      S.busy = false;
      draw();
    };

    // --- More options: where the files are kept, each soldier's model, and two how-tos ---
    const drawMore = () => {
      const w = W(), info = S.info, look = S.look || {}, kept = look.kept || null;
      const parts = [];
      const files = [];
      // each soldier's model file, made or not (squad_info's "kept"); Show in folder opens the mod's files\models once
      // anything of this unit's is there (look()'s "kept")
      for (const s of info.soldiers || []) {
        if (!s.kept) continue;
        files.push(keptRow(address, "model", fill(s.own_model ? w.squad_kept : w.squad_kept_later, { who: s.label }), s.kept,
          kept ? kept.folder : folderOf(s.kept), Boolean(kept && kept.made), w.tip_squad_folder_none));
      }
      // its Custom uniform's file, when that's what it has
      if (kept && kept.copy) {
        files.push(keptRow(address, "model", w.model_kept_uniform, kept.file, kept.folder, kept.made, w.tip_model_folder_none));
      }
      // the squad's Blender files, <mod>\blender\<unit>\squad: Show in folder opens the unit's Blender folder they're in
      if (info.blender && info.blender.work) {
        files.push(keptRow(address, "blender", info.blender.made ? w.squad_blender_kept : w.squad_blender_kept_later,
          info.blender.work, folderOf(info.blender.work), Boolean(info.blender.made), w.tip_squad_blender_folder_none));
      }
      if (files.length) parts.push(el("h4", { textContent: w.squad_more_files }), ...files);
      const models = modelNotes();
      if (models.length) parts.push(el("h4", { textContent: w.squad_more_models }), ...models);
      if (mine()) {
        parts.push(el("p", { className: "squad-note", textContent: w.squad_more_asset }),
          el("p", { className: "squad-note", textContent: w.squad_more_bones }));
      }
      moreBody.replaceChildren(...parts);
      showMore();
    };

    // each soldier's model as look() has it: the squad's own model (its riflemen's, on the first line), what of it isn't
    // there or won't work in the game; another soldier's on bones that aren't theirs; the figures drawn with his model
    const modelNotes = () => {
      const w = W(), info = S.info, look = S.look || {}, out = [];
      const own = look.own_model, rows = look.kinds || [];
      const figure = (role) => ({ far: w.fit_fig_far, fallen: w.fit_fig_fallen })[role] || w.fit_fig_other;
      (info.soldiers || []).forEach((s, i) => {
        const notes = [];
        const row = rows.find((r) => r.kind === s.id);
        if (i === 0 && s.own_model && own) {
          notes.push(el("p", { className: "small", textContent: fill(w.model_own, { file: own.file || s.from || "",
            points: (own.vertices || 0).toLocaleString(), triangles: (own.triangles || 0).toLocaleString() }) }));
          if (own.missing && own.missing.length) {
            notes.push(el("p", { className: "notice warn", textContent: fill(w.model_missing, { names: own.missing.join(", ") }) }));
          }
          if (own.no_bone) notes.push(el("p", { className: "notice warn", textContent: fill(w.model_no_bone, { n: own.no_bone }) }));
          notes.push(el("p", { className: "muted small", textContent: own.own_skeleton ? w.model_own_bones_fit : w.model_squad_fit }));
          if (look.own_copy) notes.push(el("p", { className: "notice warn", textContent: fill(w.squad_both, { who: s.label }) }));
          if (own.rigged) notes.push(fitBox(address, () => reload(true), "problems"));   // (what of it won't work in the game)
        }
        if (row && row.same_bones === false) notes.push(el("p", { className: "notice warn", textContent: w.model_kind_bones_other }));
        if (row && row.also && row.also.length) {
          notes.push(el("p", { className: "muted small", textContent: fill(w.model_kind_also, { figures: row.also.map(figure).join(", ") }) }));
        }
        if (notes.length) out.push(el("div", { className: "squad-model" }, el("strong", { textContent: soldierWords(s) }), ...notes));
      });
      return out;
    };

    // --- reading again: squad_info and look(), then the 3D view and the Look and moves section with them (`views`) ---
    const draw = () => { drawCard(); drawLines(); drawMore(); };
    const reload = async (views) => {
      let next = null;
      try { next = await api().squad_info(address, state.lang); } catch (err) { problem(err); }
      if (next && next.soldiers) S.info = next;
      S.look = await api().look(address).catch(() => null);
      S.parts = await api().blender_parts(address, state.lang).catch(() => null);
      draw();
      if (views) {
        if (page.view && page.view.reload) page.view.reload();
        if (page.looks && page.looks.reload) page.looks.reload();
      }
    };
    box.reload = () => reload(false);   // (the Look and moves section's Uniform row changed: its files are said here)

    draw();
    api().look(address).then((look) => { S.look = look; draw(); }).catch(() => {});
    // the one Blender button's tick list (StudioApi.blender_parts: its soldiers, or which model, its bones, its paint)
    api().blender_parts(address, state.lang).then((p) => { S.parts = p; draw(); }).catch(() => {});
    // the card in sight when the squad's page opens (`page.fresh`: another unit was shown; the same one drawn again keeps
    // its place), and a squad just made (New unit) at its big button, lit a moment, as the Model row is for other units
    const made = state.focusModel === address;
    if (made) state.focusModel = null;
    if (page.fresh || made) {
      requestAnimationFrame(() => {
        const detail = box.closest(".detail");
        if (detail) detail.scrollTop = 0;
        if (!made) return;
        card.classList.add("lit");
        const big = words.querySelector(".squad-big");
        if (big) big.focus({ preventScroll: true });
      });
    }
    return box;
  }

  window.SquadView = { infoOf, section };
})();
