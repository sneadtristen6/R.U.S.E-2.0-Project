// The board (StudioApi.board / board_picker / board_put / board_order / board_move / board_research / board_take_out
// / board_cards, ruse_studio/board.py; the owner, 2026-10-18: "a new screen for buildings where you're able to edit the
// order and how many units are for what building"): one nation's buildings, each a row of boxes like its build menu in
// the game, in the game's order. + adds a unit (the nation's own, a copy of another nation's, an era unit), a box is
// dragged along its row or to another row, × takes it out, and Research… puts it under the unit it comes after: "you'll
// select it and then select the spot where it goes and then boom" (his words), never a "researched from" box. Add a
// building (board_building_sources / board_add_building / board_remove_building): a copy of one of the game's
// buildings, making the same units as it or units of its own, in a row and a tab of its own (three a nation: "buildings
// 3 limit"). Each row shows its build list's groups (groups.py; the owner, 2026-10-31: "We just need to limit how many
// can be in a certain group. Because it's buggy.", a unit more in a full group: "Refuse it"; 11-01: at most 10 groups a
// building), each one row of the game's build list: a unit and its upgrades, how full it is, and its units; a unit is
// dropped into a group, or onto a row's New group, and a group's name is dragged along its row to move the whole group.
// Used by the Nations tab under each nation, and by a new mod's Buildings step (startflow.js). Uses app.js's el, fill,
// say, problem, api, state, showView and showUnit.
(function () {
  "use strict";
  const ROW_GROUP = { 8: "barracks", 13: "artillery", 10: "armor", 11: "antitank", 9: "airfield", 12: "prototype" };
  const ERA_WORD = { WWI: "eras_era_ww1", WWII: "eras_era_ww2", "Cold War": "eras_era_cold", Modern: "eras_era_modern" };
  const MOST_TRIED = 10;  // board.py MOST_TRIED: the most places a game building uses
  const NEW_GROUP = "new";  // board_put / board_move's group for a group of its own (groups.py NEW)

  // a row's top-level units' addresses, in the board's order (board_order's and the places' list)
  const topsOf = (row) => row.units.filter((u) => u.depth === 0).map((u) => u.address);

  // the place in `tops` right after group `g`'s last top-level unit there (null: none of its units is one)
  function endOf(g, tops) {
    let at = -1;
    tops.forEach((a, k) => { if (g.units.includes(a)) at = k; });
    return at < 0 ? null : at + 1;
  }

  function W() { return state.words || {}; }

  // what a unit's battle dates say on its box (board.py dates_of); nothing when it's in every battle
  function datesText(d) {
    const w = W();
    if (!d) return "";
    if (d.from === null) return d.nuclear ? w.board_dates_nuclear_only : w.board_dates_none;
    const parts = [];
    if (d.from !== 1939) parts.push(fill(w.board_dates_from, { year: d.from }));
    if (!d.nuclear) parts.push(w.board_dates_no_nuclear);
    return parts.join(" · ");
  }

  function buildingName(row) {
    const w = W();
    return row.building || w["group_" + ROW_GROUP[row.factory]] || String(row.factory);
  }

  // One board in `box` for nation `nation` (`label`: what the page calls the nation). Returns { refresh }.
  function mount(box, nation, label, opts = {}) {
    const B = { data: null, picking: null, cards: {}, busy: false };

    async function load() {
      const w = W();
      if (!B.data) box.replaceChildren(el("p", { className: "muted small", textContent: w.board_loading }));
      let data;
      try { data = await api().board(nation, state.lang); } catch (err) { problem(err); return; }
      B.data = data;
      draw();
      pictures();
    }

    // the build-menu pictures, asked once the boxes are drawn (each is read from the game's files the first time)
    async function pictures() {
      const want = [];
      for (const r of B.data.rows) for (const u of r.units) if (!(u.address in B.cards)) want.push(u.address);
      if (!want.length) return;
      let got = {};
      try { got = await api().board_cards(want); } catch { return; }
      for (const [a, url] of Object.entries(got)) if (url) B.cards[a] = url;  // (one not had now: asked again later)
      for (const img of box.querySelectorAll("img.board-card[data-address]")) {
        const url = B.cards[img.dataset.address];
        if (url) { img.src = url; img.classList.remove("hidden"); }
      }
    }

    // a change made: the board as the back end now has it, and what else changed said in one line
    function changed(res, said) {
      const w = W();
      B.data = res;
      B.picking = null;
      const more = [];
      const note = res.note || {};
      if (note.copied) more.push(w.board_copied);
      if (note.unlinked && note.unlinked.length) more.push(fill(w.board_unlinked, { list: note.unlinked.join(", ") }));
      if (note.dates) more.push(w.board_dates_narrowed);
      if (res.relinked && res.relinked.length) more.push(fill(w.board_relinked, { list: res.relinked.join(", ") }));
      if (said) say([said, ...more].join(" "), "ok");
      draw();
      pictures();
      if (opts.onChanged) opts.onChanged(res);
    }

    async function run(call, said) {
      if (B.busy) return;
      B.busy = true;
      box.classList.add("busy");
      try { changed(await call(), said); } catch (err) { problem(err); }
      B.busy = false;
      box.classList.remove("busy");
    }

    function draw() {
      const w = W(), data = B.data;
      const parts = [];
      if (!data.can) parts.push(el("p", { className: "notice warn small", textContent: w.board_no_mod }));
      if (B.picking) {
        const cancel = el("button", { type: "button", className: "small ghost", textContent: w.board_research_cancel,
          title: w.tip_board_research_cancel });
        cancel.addEventListener("click", () => { B.picking = null; draw(); });
        const none = el("button", { type: "button", className: "small", textContent: w.board_research_none,
          title: w.tip_board_research_none });
        none.addEventListener("click", () => run(() => api().board_research(nation, B.picking.address, null, state.lang),
          fill(w.board_research_none_done, { name: B.picking.name })));
        parts.push(el("div", { className: "notice board-picking", role: "status" },
          el("span", { className: "small", textContent: fill(w.board_research_pick, { name: B.picking.name, nation: label }) }),
          none, cancel));
      }
      for (const row of data.rows) parts.push(drawRow(row));
      const addBuilding = el("button", { type: "button", className: "small", textContent: w.board_add_building,
        title: fill(w.tip_board_add_building, { nation: label }), disabled: !data.can });
      addBuilding.addEventListener("click", openBuilding);
      parts.push(el("div", { className: "board-foot" }, addBuilding,
        el("span", { className: "muted small", textContent: " " + fill(w.board_own_left, { n: data.own_left }) })));
      box.replaceChildren(...parts);
    }

    // a row's buildings, when the mod adds one: each named, a new one with × to take it out of the mod
    function buildingChips(row) {
      const w = W(), list = row.buildings || [];
      if (!list.some((b) => b.new)) return null;
      const chips = el("span", { className: "board-buildings small" },
        el("span", { className: "muted", textContent: w.board_buildings_label + " " }));
      for (const b of list) {
        const chip = el("span", { className: "board-tag" + (b.new ? " mine" : ""), textContent: b.name });
        if (b.new) {
          const x = el("button", { type: "button", className: "board-x ghost", textContent: "×",
            title: fill(w.tip_board_building_remove, { name: b.name }), disabled: !B.data.can,
            ariaLabel: fill(w.tip_board_building_remove, { name: b.name }) });
          x.addEventListener("click", () => run(() => api().board_remove_building(nation, b.address, state.lang),
            fill(w.board_building_removed, { name: b.name })));
          chip.append(x);
        }
        chips.append(chip, " ");
      }
      return chips;
    }

    function drawRow(row) {
      const w = W(), name = buildingName(row), groups = row.groups || [];
      const head = el("div", { className: "board-row-head" },
        el("strong", { textContent: name }),
        el("span", { className: "muted small", textContent: " " + fill(w.board_count, { n: row.units.length }) }));
      if (groups.length) head.append(groupsTag(row, name));
      if (row.own) head.append(el("span", { className: "board-tag mine", textContent: w.board_own_tag,
        title: w.tip_board_own_tag }));
      const chips = buildingChips(row);
      if (chips) head.append(" ", chips);
      if (row.untried) head.append(el("span", { className: "board-tag warn", textContent: w.board_untried,
        title: fill(w.tip_board_untried, { n: MOST_TRIED }) }));
      const line = el("div", { className: "board-line" });
      line.dataset.factory = row.factory;
      // each group a row of its own, as the game's build list shows it; a unit in none (not looked for: groups.py
      // puts every unit shown in a building in one) is still shown, by itself
      const units = new Map(row.units.map((u) => [u.address, u]));
      const seen = new Set();
      for (const g of groups) {
        line.append(drawGroup(row, g, g.units.map((a) => units.get(a)).filter(Boolean)));
        for (const a of g.units) seen.add(a);
      }
      const loose = row.units.filter((u) => !seen.has(u.address));
      if (loose.length) line.append(drawGroup(row, null, loose));
      line.append(rowFoot(row, name));
      const out = [head, line];
      if (!row.units.length) out.push(el("p", { className: "muted small",
        textContent: row.own ? w.board_empty_own_row : w.board_empty_row }));
      return el("section", { className: "board-row" }, ...out);
    }

    // how many groups the row has, of the most a building holds (more: a mod made before the limit, said plainly)
    function groupsTag(row, name) {
      const w = W(), n = row.groups.length, most = row.most_groups, over = n > most;
      const values = { n, most, extra: n - most, building: name };
      return el("span", { className: "board-tag" + (over ? " bad" : n >= most ? " full" : ""),
        textContent: fill(over ? w.board_groups_over : w.board_groups_count, values),
        title: fill(over ? w.tip_board_groups_over : w.tip_board_groups, values) });
    }

    // one group of a row (`g` null: units in none): its head, then its units in the board's order, each with the ones
    // researched from it in the same group pushed in under it; dropped on, a unit goes into it
    function drawGroup(row, g, list) {
      const node = el("div", { className: "board-menu-group" + (!g ? " loose" : g.over ? " over" : g.full ? " full" : "") });
      if (g) {
        node.dataset.root = g.root;
        node.append(groupHead(row, g));
      }
      dropOn(node, row, g, null);
      const inside = new Set(list.map((u) => u.address)), boxes = el("div", { className: "board-menu-group-units" });
      node.append(boxes);
      let block = null, top = 0;
      for (const u of list) {
        if (!block || u.depth === 0 || !inside.has(u.parent)) {
          block = el("div", { className: "board-group" });
          top = u.depth;
          boxes.append(block);
          if (u.depth === 0) dropOn(block, row, g, u.address);  // put before it
        }
        block.append(boxOf(u, row, u.depth - top));
      }
      return node;
    }

    // a group's name, how full it is (an over-full one, of a mod made before the limit, says how many to take out)
    // and its + ; dragged, the whole group moves along its row
    function groupHead(row, g) {
      const w = W(), where = buildingName(row);
      const values = { name: g.name, n: g.count, most: g.most, extra: g.count - g.most, building: where };
      const count = el("span", { className: "board-tag" + (g.over ? " bad" : g.full ? " full" : ""),
        textContent: fill(g.over ? w.board_group_over : g.full ? w.board_group_full : w.board_group_count, values),
        title: fill(g.over ? w.tip_board_group_over : g.full ? w.tip_board_group_full : w.tip_board_group_count, values) });
      const tip = fill(w.tip_board_group_add, values);
      const add = el("button", { type: "button", className: "board-x ghost board-group-add", textContent: "+",
        title: g.full ? fill(w.board_group_no_room, { ...values, n: g.count + 1 }) : tip, ariaLabel: tip,
        disabled: !B.data.can || g.full });
      add.addEventListener("click", () => openPicker(row, endOf(g, topsOf(row)), g.root, g.name));
      const head = el("div", { className: "board-menu-group-head", title: w.tip_board_group,
        draggable: B.data.can && row.groups.length > 1 },
        el("span", { className: "board-menu-group-name small", textContent: fill(w.board_group_name, values) }),
        el("span", { className: "board-menu-group-count" }, count, add));
      head.addEventListener("dragstart", (e) => {
        B.dragging = { group: g.root, units: g.units.slice(), factory: row.factory, name: g.name };
        e.dataTransfer.effectAllowed = "move";
        try { e.dataTransfer.setData("text/plain", g.root); } catch { /* some windows: the board keeps it */ }
      });
      head.addEventListener("dragend", () => { B.dragging = null; });
      return head;
    }

    // the row's end: + (a unit added goes into the group of its kind, as before) and New group (a group of its own:
    // off, with the reason, when the building already has the most groups)
    function rowFoot(row, name) {
      const w = W(), n = (row.groups || []).length;
      const add = el("button", { type: "button", className: "board-add", textContent: "+",
        title: fill(w.tip_board_add, { nation: label, building: name }), disabled: !B.data.can,
        ariaLabel: fill(w.tip_board_add, { nation: label, building: name }) });
      add.addEventListener("click", () => openPicker(row, null));
      dropOn(add, row, null, null);
      const roomless = n >= row.most_groups;
      const tip = roomless ? fill(w.board_new_group_no_room, { building: name, n: n + 1, most: row.most_groups })
        : fill(w.tip_board_new_group, { building: name });
      const start = el("button", { type: "button", className: "small ghost", textContent: "+ " + w.board_new_group,
        title: tip, disabled: !B.data.can || roomless });
      start.addEventListener("click", () => openPicker(row, null, NEW_GROUP));
      const place = el("div", { className: "board-new-group" + (roomless ? " no-room" : ""), title: tip }, start);
      if (roomless) place.append(el("span", { className: "muted small",  // why it's off, in sight
        textContent: fill(w.board_groups_count, { n, most: row.most_groups }) }));
      dropOn(place, row, NEW_GROUP, null);
      return el("div", { className: "board-row-foot" }, add, place);
    }

    // why a dragged unit can't go into group `g` of `row` (NEW_GROUP: a group of its own), said on the page before the
    // Studio is asked; "" when it can (the Studio still checks): no room for it and the units researched from it that
    // come along, or no room for another group
    function refusal(d, row, g) {
      if (d.group || !g) return "";
      const w = W(), where = buildingName(row), groups = row.groups || [];
      const from = d.factory === row.factory ? groups.find((x) => x.units.includes(d.address)) : null;
      const coming = from ? d.inGroup : d.line;
      if (g === NEW_GROUP) {
        if (from && from.units.length <= coming) return "";  // its whole group goes: no group more
        return groups.length >= row.most_groups
          ? fill(w.board_new_group_no_room, { building: where, n: groups.length + 1, most: row.most_groups }) : "";
      }
      if (from && from.root === g.root) return "";
      return g.count + coming > g.most
        ? fill(w.board_group_no_room, { name: g.name, building: where, n: g.count + coming, most: g.most }) : "";
    }

    // a place that takes a dragged unit or group: group `g` of `row` (null: the row by its kind, as before; NEW_GROUP: a
    // group of its own), before top-level unit `before` (null: at the group's end, or the row's)
    function dropOn(node, row, g, before) {
      node.addEventListener("dragover", (e) => {
        const d = B.dragging;
        if (!d || (d.group && d.factory !== row.factory)) return;  // a group moves along its own row only
        e.preventDefault();
        e.stopPropagation();
        node.classList.add("drop");
        node.classList.toggle("drop-no", Boolean(refusal(d, row, g)));
      });
      node.addEventListener("dragleave", () => node.classList.remove("drop", "drop-no"));
      node.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        node.classList.remove("drop", "drop-no");
        const d = B.dragging;
        B.dragging = null;
        if (d) landed(d, row, g, before);
      });
    }

    function landed(d, row, g, before) {
      const w = W(), where = buildingName(row), tops = topsOf(row);
      if (d.group) {  // a whole group: before group `g`'s first unit, or at the row's end
        if (g && g !== NEW_GROUP && g.root === d.group) return;
        const rest = tops.filter((a) => !d.units.includes(a));
        const first = g && g !== NEW_GROUP ? rest.findIndex((a) => g.units.includes(a)) : -1;
        rest.splice(first < 0 ? rest.length : first, 0, ...tops.filter((a) => d.units.includes(a)));
        run(() => api().board_order(nation, row.factory, rest, state.lang), "");
        return;
      }
      const why = refusal(d, row, g);
      if (why) { say(why, "error"); return; }
      const from = d.factory === row.factory ? (row.groups || []).find((x) => x.units.includes(d.address)) : null;
      const rest = tops.filter((a) => a !== d.address);
      let index = before ? rest.indexOf(before) : g && g !== NEW_GROUP ? endOf(g, rest) : null;
      if (index !== null && index < 0) index = null;
      if (d.factory === row.factory && (!g || (g !== NEW_GROUP && from && from.root === g.root))) {
        if (before === d.address) return;  // along its row, in its own group: its place only
        rest.splice(index === null ? rest.length : index, 0, d.address);
        run(() => api().board_order(nation, row.factory, rest, state.lang), "");
        return;
      }
      const group = g === NEW_GROUP ? NEW_GROUP : g ? g.root : null;
      const said = g === NEW_GROUP ? fill(w.board_moved_new_group, { name: d.name, building: where })
        : g ? fill(w.board_moved_group, { name: d.name, group: g.name, building: where })
          : fill(w.board_moved, { name: d.name, building: where });
      run(() => api().board_move(nation, d.address, row.factory, index, group, state.lang), said);
    }

    // `depth`: how far it's pushed in under the unit it's researched from in its group
    function boxOf(u, row, depth = u.depth) {
      const w = W();
      const card = el("img", { className: "board-card hidden", alt: "" });
      card.dataset.address = u.address;
      if (B.cards[u.address]) { card.src = B.cards[u.address]; card.classList.remove("hidden"); }
      const open = el("button", { type: "button", className: "link board-name", textContent: u.name,
        title: fill(w.tip_board_open, { name: u.name }) });
      open.addEventListener("click", async () => {
        showView("units");
        try { await showUnit(u.address); } catch (err) { problem(err); }
      });
      const tags = el("div", { className: "board-tags" });
      const dates = datesText(u.dates);
      if (dates) tags.append(el("span", { className: "board-tag", textContent: dates, title: w.tip_board_dates }));
      if (u.new) tags.append(el("span", { className: "board-tag mine", textContent: w.board_new, title: w.tip_board_new }));
      if (u.untried_mix) tags.append(el("span", { className: "board-tag warn", textContent: w.board_mix_short, title: w.board_mix }));
      if (u.parent_factory !== null && u.parent_factory !== undefined) {
        const where = buildingName(B.data.rows.find((r) => r.factory === u.parent_factory) || { factory: u.parent_factory });
        tags.append(el("span", { className: "board-tag warn", textContent: fill(w.board_from_other, { name: u.parent_name, building: where }),
          title: w.tip_board_from_other }));
      }
      const take = el("button", { type: "button", className: "board-x ghost", textContent: "×",
        title: fill(w.tip_board_take_out, { name: u.name }), ariaLabel: fill(w.tip_board_take_out, { name: u.name }),
        disabled: !B.data.can });
      take.addEventListener("click", () => takeOut(u));
      const research = el("button", { type: "button", className: "small ghost board-research",
        textContent: w.board_research, title: fill(w.tip_board_research, { name: u.name }), disabled: !B.data.can });
      research.addEventListener("click", () => { B.picking = { address: u.address, name: u.name }; draw(); });
      const node = el("div", { className: "board-box" + (depth ? " researched" : "") + (u.new ? " new" : ""),
        draggable: B.data.can, title: w.tip_board_drag });
      node.style.setProperty("--depth", String(depth));
      node.dataset.address = u.address;
      node.addEventListener("dragstart", (e) => {
        // what comes along: the units researched from it in its row (to another building), those in its group (along
        // its row), as board_move moves them
        const at = row.units.indexOf(u);
        let end = at + 1;
        while (end < row.units.length && row.units[end].depth > u.depth) end += 1;
        const line = row.units.slice(at, end).map((x) => x.address);
        const mine = (row.groups || []).find((x) => x.units.includes(u.address));
        B.dragging = { address: u.address, factory: row.factory, name: u.name, line: line.length,
          inGroup: mine ? line.filter((a) => mine.units.includes(a)).length : 1 };
        e.dataTransfer.effectAllowed = "move";
        try { e.dataTransfer.setData("text/plain", u.address); } catch { /* some windows: the board keeps it */ }
      });
      node.addEventListener("dragend", () => { B.dragging = null; });
      node.append(el("div", { className: "board-box-top" }, card, take), open, tags);
      if (u.parent && u.research) node.append(researchCost(u));
      node.append(research);
      // picking where a unit goes: every other box is a spot to put it under
      if (B.picking && B.picking.address !== u.address) {
        const under = el("button", { type: "button", className: "small primary board-under", textContent: w.board_under,
          title: fill(w.tip_board_under, { name: B.picking.name, parent: u.name }) });
        under.addEventListener("click", () => {
          const p = B.picking;
          run(() => api().board_research(nation, p.address, u.address, state.lang),
            fill(w.board_research_done, { name: p.name, parent: u.name }));
        });
        node.append(under);
        node.classList.add("target");
      }
      if (B.picking && B.picking.address === u.address) node.classList.add("picked");
      return node;
    }

    // a researched unit's research cost and time, changed where it is (StudioApi.set_research)
    function researchCost(u) {
      const w = W(), row = el("div", { className: "board-cost" });
      for (const [prop, label, tip] of [["UpgradePrice", w.board_price, w.tip_board_price],
        ["UpgradeTime", w.board_time, w.tip_board_time]]) {
        const input = el("input", { type: "number", min: 0, step: 1, value: u.research[prop] ?? "", title: tip,
          className: "short", disabled: !B.data.can });
        input.addEventListener("change", async () => {
          const v = input.value === "" ? null : Number(input.value);
          try { await api().set_research(u.address, prop, v); say(fill(w.board_cost_saved, { name: u.name }), "ok"); }
          catch (err) { problem(err); }
        });
        row.append(el("label", { className: "small", title: tip }, label + " ", input));
      }
      return row;
    }

    async function takeOut(u, researched = null) {
      const w = W();
      let res;
      try { res = await api().board_take_out(nation, u.address, researched, state.lang); } catch (err) { problem(err); return; }
      if (res.ask && res.ask.length) {  // a unit of the mod others are researched from: asked first, then relinked
        if (!window.confirm(fill(w.board_ask_delete, { name: u.name, list: res.ask.join(", ") }))) { changed(res, ""); return; }
        return takeOut(u, "relink");
      }
      changed(res, fill(u.new ? w.board_deleted : w.board_taken_out, { name: u.name }));
    }

    // --- the empty box's list: this nation's own units, the other nations' (a copy is made), the era units; put in
    // `group` (a group's first unit's address; NEW_GROUP: a group of its own; null: the group of its kind) ---
    async function openPicker(row, index, group = null, groupName = "") {
      const w = W();
      let data;
      try { data = await api().board_picker(nation, state.lang); } catch (err) { problem(err); return; }
      const dlg = pickerDialog();
      const where = buildingName(row);
      dlg.querySelector(".board-pick-title").textContent = group === NEW_GROUP
        ? fill(w.board_pick_title_new_group, { building: where, nation: label })
        : group ? fill(w.board_pick_title_group, { name: groupName, building: where, nation: label })
          : fill(w.board_pick_title, { building: where, nation: label });
      const search = dlg.querySelector(".board-pick-search");
      search.placeholder = w.board_pick_search;
      search.title = w.tip_board_pick_search;
      search.value = "";
      const close = dlg.querySelector(".board-pick-close");
      close.textContent = w.board_pick_close;
      close.title = w.board_pick_close;
      const list = dlg.querySelector(".board-pick-list");
      // the + at a row's end: the group it goes in is picked here, the group of its kind first (a unit with no card
      // type has none: the Studio then asks for one, said below, and another group is picked and the unit again)
      const pickGroup = dlg.querySelector(".board-pick-group"), why = dlg.querySelector(".board-pick-why");
      const groups = row.groups || [];
      pickGroup.replaceChildren(el("option", { value: "", textContent: w.board_pick_group_kind }),
        ...groups.map((g) => el("option", { value: g.root, disabled: g.full,
          textContent: fill(g.full ? w.eras_group_choice_full : w.eras_group_choice, { name: g.name, n: g.count, most: g.most }) })),
        el("option", { value: NEW_GROUP, disabled: groups.length >= row.most_groups,
          textContent: fill(groups.length >= row.most_groups ? w.eras_group_own_full : w.eras_group_own,
            { groups: groups.length, most_groups: row.most_groups }) }));
      pickGroup.value = "";
      pickGroup.title = fill(w.tip_board_pick_group, { building: where });
      dlg.querySelector(".board-pick-group-label").textContent = w.board_pick_group;
      dlg.querySelector(".board-pick-group-box").classList.toggle("hidden", group !== null);
      why.classList.add("hidden");
      const put = async (what, name) => {
        if (B.busy) return;
        const chosen = group !== null ? group : (pickGroup.value || null);
        const picked = group === null && chosen && chosen !== NEW_GROUP ? groups.find((g) => g.root === chosen) : null;
        const at = picked ? endOf(picked, topsOf(row)) : index;  // a group picked here: at that group's end
        const named = picked ? picked.name : groupName;
        const said = chosen === NEW_GROUP ? fill(w.board_moved_new_group, { name, building: where })
          : chosen ? fill(w.board_moved_group, { name, group: named, building: where })
            : fill(w.board_put_done, { name, building: where });
        B.busy = true;
        box.classList.add("busy");
        try {
          const res = await api().board_put(nation, row.factory, what.unit || "", what.era || "", at, chosen, state.lang);
          dlg.close();
          changed(res, said);
        } catch (err) {  // refused: said here, the list stays open for another group
          why.textContent = (err && err.message) || String(err);
          why.classList.remove("hidden");
          if (group === null) pickGroup.focus();
        }
        B.busy = false;
        box.classList.remove("busy");
      };
      const render = () => {
        const q = search.value.trim().toLowerCase();
        const hit = (s) => !q || String(s).toLowerCase().includes(q);
        const sections = [];
        for (const g of data.nations) {
          const own = g.nation === nation;
          const units = g.units.filter((u) => hit(u.name) && !(own && u.here && u.factory === row.factory));
          if (!units.length) continue;
          sections.push(el("h3", { textContent: own ? fill(w.board_pick_own, { nation: g.name }) : g.name,
            title: own ? w.tip_board_pick_own : w.tip_board_pick_copy }));
          sections.push(el("div", { className: "board-pick-units" }, ...units.map((u) => {
            const b = el("button", { type: "button", className: "chip",
              title: own ? fill(w.tip_board_pick_move, { name: u.name, building: where }) : fill(w.tip_board_pick_copy_one, { name: u.name, nation: label }) },
              u.name);
            const r = B.data.rows.find((x) => x.factory === u.factory);
            const sub = u.taken_out ? w.board_pick_out : own ? fill(w.board_pick_where, { building: r ? buildingName(r) : "" }) : "";
            if (sub) b.append(el("small", { className: "muted", textContent: " " + sub }));
            if (u.new) b.append(el("small", { className: "board-tag mine", textContent: " " + w.board_new }));
            b.addEventListener("click", () => put({ unit: u.address }, u.name));
            return b;
          })));
        }
        if (data.eras.length) {
          for (const era of data.eras) {
            const units = era.units.filter((u) => hit(u.name) || hit(u.nation));
            if (!units.length) continue;
            sections.push(el("h3", { textContent: fill(w.board_pick_era, { era: w[ERA_WORD[era.era]] || era.era }), title: w.tip_board_pick_era }));
            sections.push(el("div", { className: "board-pick-units" }, ...units.map((u) => {
              const b = el("button", { type: "button", className: "chip", disabled: u.added,
                title: u.added ? w.board_pick_added : fill(w.tip_board_pick_era_one, { name: u.name, building: where }) },
                u.name, el("small", { className: "muted", textContent: " " + u.nation }));
              b.addEventListener("click", () => put({ era: u.key }, u.name));
              return b;
            })));
          }
        } else {
          sections.push(el("p", { className: "muted small", textContent: w.board_pick_no_eras }));
        }
        if (!sections.length) sections.push(el("p", { className: "muted small", textContent: w.board_pick_none }));
        list.replaceChildren(...sections);
      };
      search.oninput = render;
      render();
      dlg.showModal();
      search.focus();
    }

    // --- Add a building: a copy of one of the game's buildings, making the same units or units of its own ---
    async function openBuilding() {
      const w = W();
      let data;
      try { data = await api().board_building_sources(nation, state.lang); } catch (err) { problem(err); return; }
      const dlg = buildingDialog();
      dlg.querySelector(".board-bld-title").textContent = fill(w.board_building_title, { nation: label });
      const pick = dlg.querySelector(".board-bld-source");
      const groups = new Map();
      for (const b of data.buildings) {
        if (!groups.has(b.nation)) groups.set(b.nation, el("optgroup", { label: b.nation_name }));
        groups.get(b.nation).append(el("option", { value: b.address, textContent: b.name }));
      }
      pick.replaceChildren(...groups.values());
      pick.title = w.tip_board_building_copy;
      const nameInput = dlg.querySelector(".board-bld-name");
      nameInput.value = "";
      nameInput.title = w.tip_board_building_name;
      nameInput.placeholder = w.board_building_name;
      const same = dlg.querySelector(".board-bld-same"), own = dlg.querySelector(".board-bld-own");
      same.checked = true;
      own.disabled = data.own_left <= 0;
      dlg.querySelector(".board-bld-copy-label").textContent = w.board_building_copy;
      dlg.querySelector(".board-bld-name-label").textContent = w.board_building_name;
      const sameLabel = dlg.querySelector(".board-bld-same-label"), ownLabel = dlg.querySelector(".board-bld-own-label");
      sameLabel.textContent = w.board_building_same;
      sameLabel.title = w.tip_board_building_same;
      ownLabel.textContent = data.own_left > 0 ? fill(w.board_building_own, { n: data.own_left })
        : w.board_building_own_full;
      ownLabel.title = data.own_left > 0 ? w.tip_board_building_own : w.board_building_own_full;
      same.title = sameLabel.title;
      own.title = ownLabel.title;
      const patchNote = dlg.querySelector(".board-bld-patch");
      patchNote.textContent = w.board_building_patch;
      const showNote = () => patchNote.classList.toggle("hidden",
        !(own.checked && data.patch_kinds.includes(data.next_kind)));
      same.onchange = showNote;
      own.onchange = showNote;
      showNote();
      const add = dlg.querySelector(".board-bld-add"), cancel = dlg.querySelector(".board-bld-cancel");
      add.textContent = w.board_building_add;
      add.title = w.tip_board_building_add;
      cancel.textContent = w.board_building_cancel;
      cancel.title = w.board_building_cancel;
      add.onclick = () => {
        const name = nameInput.value.trim();
        if (!name) { nameInput.focus(); return; }
        dlg.close();
        run(() => api().board_add_building(nation, pick.value, name, own.checked, state.lang),
          fill(w.board_building_added, { name }));
      };
      dlg.showModal();
      nameInput.focus();
    }

    load();
    return { refresh: load };
  }

  // Add a building's window, made once
  function buildingDialog() {
    let dlg = document.getElementById("board-bld");
    if (dlg) return dlg;
    const id = "board-bld-kind";
    dlg = el("dialog", { id: "board-bld", className: "doctor board-pick" },
      el("h2", { className: "board-bld-title" }),
      el("label", { className: "small" }, el("span", { className: "board-bld-copy-label" }), " ",
        el("select", { className: "board-bld-source", title: "" })),
      el("label", { className: "small" }, el("span", { className: "board-bld-name-label" }), " ",
        el("input", { type: "text", className: "board-bld-name", maxLength: 60, autocomplete: "off", title: "" })),
      el("label", { className: "small board-bld-choice" },
        el("input", { type: "radio", name: id, className: "board-bld-same", title: "" }), " ",
        el("span", { className: "board-bld-same-label" })),
      el("label", { className: "small board-bld-choice" },
        el("input", { type: "radio", name: id, className: "board-bld-own", title: "" }), " ",
        el("span", { className: "board-bld-own-label" })),
      el("p", { className: "notice small board-bld-patch hidden" }),
      el("div", { className: "actions" },
        el("button", { type: "button", className: "small primary board-bld-add", title: "" }),
        el("button", { type: "button", className: "small ghost board-bld-cancel", title: "" })));
    dlg.querySelector(".board-bld-cancel").addEventListener("click", () => dlg.close());
    dlg.addEventListener("keydown", (e) => e.stopPropagation());
    document.body.append(dlg);
    return dlg;
  }

  // the picker's window, made once
  function pickerDialog() {
    let dlg = document.getElementById("board-pick");
    if (dlg) return dlg;
    dlg = el("dialog", { id: "board-pick", className: "doctor board-pick" },
      el("h2", { className: "board-pick-title" }),
      el("label", { className: "small board-pick-group-box" }, el("span", { className: "board-pick-group-label" }), " ",
        el("select", { className: "board-pick-group", title: "" })),
      el("p", { className: "notice error small board-pick-why hidden", role: "alert" }),
      el("input", { type: "search", className: "board-pick-search", autocomplete: "off", title: "" }),
      el("div", { className: "board-pick-list" }),
      el("div", { className: "actions" }, el("button", { type: "button", className: "small ghost board-pick-close", title: "" })));
    dlg.querySelector(".board-pick-close").addEventListener("click", () => dlg.close());
    // keys typed in the list stay in it: the unit list's and the map's own keys wait behind it
    dlg.addEventListener("keydown", (e) => e.stopPropagation());
    document.body.append(dlg);
    return dlg;
  }

  // On a unit's page in the Units tab: the building that makes it and its place there, with a way to its board (the
  // owner, 2026-10-18: the Units and Nations tabs "should definitely become more intertwined")
  function unitLink(u) {
    const w = W(), line = el("p", { className: "small board-where" });
    (async () => {
      let where;
      try { where = await api().board_where(u.address, state.lang); } catch { return; }
      if (where.factory === null || where.factory === undefined) return;
      const building = where.building || W()["group_" + ROW_GROUP[where.factory]] || "";
      const show = el("button", { type: "button", className: "link", textContent: w.board_show,
        title: fill(w.tip_board_show, { nation: (state.nationNames || [])[where.nation] || "" }) });
      show.addEventListener("click", () => {
        if (window.NationsView && window.NationsView.openNation) window.NationsView.openNation(where.nation, where.factory);
        else showView("nations");
      });
      line.append(where.place ? fill(w.board_where, { building, n: where.place, all: where.count })
        : fill(w.board_where_out, { building }), " ", show);
    })();
    return line;
  }

  window.BoardView = { mount, datesText, unitLink };
})();
