// The Music tab (StudioApi.music / music_sound / music_save / music_reset, rusemod.sound): every song the game plays,
// by where it plays; each can be heard, and replaced by the modder's own in a small editor kept in the Studio: a
// sound file dropped or chosen (the window itself reads WAV, MP3, OGG and FLAC), cut with two handles, faded in and
// out, made louder or quieter (or as loud as the game's), heard, then "Use this": the Studio makes it the game's
// song's own format and saves it in the current mod (files/replace/<the song>.wav); the build puts it in the game.
// Nothing to install and no settings. Uses app.js's $, el, fill, say, problem and api.
(function () {
  "use strict";
  const S = { words: {}, lang: "base", data: null, ctx: null, playing: null, cache: new Map(), ed: null };
  const W = () => S.words;

  // --- the game's songs, read here (the same steps as rusemod.sound.decode; a song plays at once, not after
  // the Studio's Python has spent half a minute on it) ---
  function decodeEss(buf) {
    const b = new Uint8Array(buf);
    const dv = new DataView(buf);
    if (b.length < 20 || b[0] !== 1 || b[1] !== 0 || b[2] !== 2 || b[3] !== 2) throw new Error("not one of the game's songs");
    const ch = b[5], rate = dv.getUint16(6), frames = dv.getUint32(8);
    const fpb = { 1: 1024, 2: 512, 6: 170 }[ch];
    if (!fpb) throw new Error(`${ch} channels`);
    let n = 1;
    while (20 + 4 * n <= b.length && dv.getUint32(16 + 4 * n) !== b.length - 20 - 4 * n) n++;
    if (20 + 4 * n > b.length) throw new Error("a song with no parts");
    const data = 20 + 4 * n, top = b.length * 8 + 64;
    const out = [];
    for (let c = 0; c < ch; c++) out.push(new Int16Array(frames));
    const bit = (p) => (p >> 3) < b.length ? (b[p >> 3] >> (7 - (p & 7))) & 1 : 0;
    let start = 0;
    for (let bi = 0; bi < n; bi++) {
      const end = dv.getUint32(20 + 4 * bi), blk = data + start;
      const count = Math.min(fpb, frames - bi * fpb);
      let pos = (blk + 20 * ch) * 8;
      for (let c = 0; c < ch; c++) {
        const o = blk + 20 * c;
        let w2 = dv.getInt16(o), w1 = dv.getInt16(o + 2), y1 = dv.getInt16(o + 4), y2 = dv.getInt16(o + 6);
        let x1 = dv.getInt16(o + 8), x2 = dv.getInt16(o + 10), x3 = dv.getInt16(o + 12);
        let c1 = dv.getInt16(o + 14), c2 = dv.getInt16(o + 16), c3 = dv.getInt16(o + 18);
        const dst = out[c];
        let f = bi * fpb;
        for (let i = 0; i < count; i++) {
          let r = 0;
          while (!bit(pos) && pos <= top) { r++; pos++; }
          if (pos > top) {
            // the file stops here (some of the game's own songs end a few codes short): only the very last part
            // may, and the rest keeps the last sample, as rusemod.sound does
            if (bi !== n - 1) throw new Error("the song ends early");
            for (; i < count; i++) dst[f++] = y1;
            break;
          }
          pos++;
          if (r === 24) { let v = 0; for (let k = 0; k < 16; k++) v = (v << 1) | bit(pos++); r = 24 + v; }
          const k = r >> 1;
          let lo, hi;
          if (k === 0) { lo = 0; hi = c1; c1 -= 2 * ((c1 + 2046) >> 11); }
          else if (k === 1) { lo = c1; hi = c1 + c2; c1 += 6 * ((c1 + 2048) >> 11); c2 -= 2 * ((c2 + 1022) >> 10); }
          else if (k === 2) {
            lo = c1 + c2; hi = lo + c3;
            c1 += 6 * ((c1 + 2048) >> 11); c2 += 6 * ((c2 + 1024) >> 10); c3 -= 2 * ((c3 + 510) >> 9);
          } else {
            lo = c1 + c2 + (c3 + 1) * (k - 2); hi = lo + c3;
            c1 += 6 * ((c1 + 2048) >> 11); c2 += 6 * ((c2 + 1024) >> 10); c3 += 6 * ((c3 + 512) >> 9);
          }
          const mid = (lo + hi) >> 1;
          if (mid <= c1) c1 -= 2 * ((c1 + 2046) >> 11);
          else if (mid <= c2) c2 -= 2 * ((c2 + 1022) >> 10);
          else if (mid <= c3) c3 -= 2 * ((c3 + 510) >> 9);
          let e;
          if (hi - lo > 64) { const q = (bit(pos) << 1) | bit(pos + 1); pos += 2; e = lo + q * (((hi - lo) >> 2) + 1); }
          else e = mid;
          if (r & 1) e = ~e;
          const p1 = 4 * x1 - 5 * x2 - 2 * x3;
          const xn = (((p1 * w1 + 128) | 0) >> 8) + e;
          if (p1 || e) w1 += (p1 ^ e) >= 0 ? 2 : -2;
          const p2 = 2 * y1 - y2;
          let y = (((p2 * w2 + 128) | 0) >> 8) + xn;
          if (p2 || xn) w2 += (p2 ^ xn) >= 0 ? 2 : -2;
          if (y > 32767) y = 32767; else if (y < -32768) y = -32768;
          x3 = x2; x2 = x1; x1 = xn; y2 = y1; y1 = y;
          dst[f++] = y;
        }
      }
      start = end;
    }
    return { channels: ch, rate, frames, pcm: out };
  }

  // --- playing ---
  function ctx() {
    if (!S.ctx) S.ctx = new AudioContext();
    if (S.ctx.state === "suspended") S.ctx.resume();
    return S.ctx;
  }

  function stop() {
    if (S.playing) {
      try { S.playing.node.stop(); } catch { /* it had ended */ }
      const done = S.playing.done;
      S.playing = null;
      if (done) done();
    }
  }

  // play `buffer` from `from` to `to` seconds through `shape` (a function given the gain node and the start time,
  // which sets the fades and volume); `done` when it ends or is stopped
  function play(buffer, from, to, shape, done) {
    stop();
    const c = ctx();
    const node = c.createBufferSource();
    node.buffer = buffer;
    const gain = c.createGain();
    node.connect(gain).connect(c.destination);
    const at = c.currentTime + 0.05;
    if (shape) shape(gain.gain, at, to - from); else gain.gain.value = 1;
    node.start(at, from, Math.max(0, to - from));
    const me = { node, done, at, from };
    node.onended = () => { if (S.playing === me) { S.playing = null; if (done) done(); } };
    S.playing = me;
    return me;
  }

  async function gameBuffer(member) {
    if (S.cache.has(member)) return S.cache.get(member);
    const got = await api().music_sound(member, "game");
    const res = await fetch(got.url);
    if (!res.ok) throw new Error(`${res.status}`);
    if (got.kind === "wav") {  // the preview's made-up songs
      const wav = await ctx().decodeAudioData(await res.arrayBuffer());
      S.cache.set(member, wav);
      return wav;
    }
    const song = decodeEss(await res.arrayBuffer());
    const buffer = new AudioBuffer({ numberOfChannels: song.channels, length: Math.max(1, song.frames), sampleRate: song.rate });
    for (let c = 0; c < song.channels; c++) {
      const f = new Float32Array(song.frames);
      const s = song.pcm[c];
      for (let i = 0; i < f.length; i++) f[i] = s[i] / 32768;
      buffer.copyToChannel(f, c);
    }
    if (S.cache.size >= 2) S.cache.delete(S.cache.keys().next().value);  // long songs are big: keep two
    S.cache.set(member, buffer);
    return buffer;
  }

  async function modBuffer(member) {
    const got = await api().music_sound(member, "mod");
    const res = await fetch(got.url);
    if (!res.ok) throw new Error(`${res.status}`);
    return ctx().decodeAudioData(await res.arrayBuffer());
  }

  // 2:55 in the list, 2:55.4 in the editor (where a cut is set to a tenth of a second)
  const clock = (s, tenths) => tenths ? `${Math.floor(s / 60)}:${(s % 60).toFixed(1).padStart(4, "0")}`
    : `${Math.floor(Math.round(s) / 60)}:${String(Math.round(s) % 60).padStart(2, "0")}`;

  // --- the list ---
  async function render() {
    const w = W();
    $("music-title").textContent = w.music_title;
    $("music-help").textContent = w.music_help;
    let data;
    try { data = await api().music(S.lang); } catch (err) { problem(err); return; }
    if (!$("music-view") || $("music-view").classList.contains("hidden")) return;  // another tab meanwhile
    S.data = data;
    $("music-nomod").textContent = data.mod ? "" : w.no_mod;
    $("music-nomod").classList.toggle("hidden", data.mod);
    $("music-groups").replaceChildren(...(data.groups.length ? data.groups.map((g) => {
      const list = el("div", { className: "music-list" });
      for (const s of g.songs) list.append(row(s));
      const head = el("h2", { textContent: w[`music_group_${g.id.replace(/\d$/, "")}`] ? fill(w[`music_group_${g.id.replace(/\d$/, "")}`], { n: Number(g.id.slice(-1)) + 1 }) : g.id });
      const first = g.id === "playlist0" || !g.id.startsWith("playlist");  // the three lists share one help line
      const help = first ? w[`music_help_${g.id.replace(/\d$/, "")}`] : null;
      return el("div", { className: "group" }, head, ...(help ? [el("p", { className: "muted small", textContent: help })] : []), list);
    }) : [el("p", { className: "muted", textContent: w.music_none })]));
  }

  function where(s) {
    const w = W();
    const bits = s.also.filter((a) => a !== "missions").map((a) => w[`music_also_${a.replace(/\d$/, "")}`] ? fill(w[`music_also_${a.replace(/\d$/, "")}`], { n: Number(a.slice(-1)) + 1 }) : a);
    const maps = s.maps.map((m) => `${m.map} (${m.parts.map((p) => p || "—").join(", ")})`);
    if (maps.length) bits.push(fill(w.music_in_missions, { n: maps.length }));
    return { line: bits.join(" · "), maps };
  }

  // --- a unit's voice lines, on its page (app.js showUnit; StudioApi.unit_voices): by moment, folded, each line
  // played and replaced like a song (the same editor) ---
  function voicesGroup(u, words, lang) {
    S.words = words;
    S.lang = lang;
    const group = el("div", { className: "group voices" });
    const fillIn = async () => {
      const w = W();
      let v;
      try { v = await api().unit_voices(u.address, lang); } catch (err) { problem(err); return; }
      if (!v.moments.length) { group.replaceChildren(); return; }
      const open = new Set([...group.querySelectorAll("details[open]")].map((d) => d.dataset.moment));
      const parts = [el("h2", { textContent: w.voice_title })];
      const sharing = [...v.shared, ...(v.hidden ? [fill(w.voice_hidden, { n: v.hidden })] : [])];
      parts.push(el("p", { className: "muted small", textContent: v.copy ? w.voice_copy
        : sharing.length ? fill(w.voice_shared, { units: sharing.join(", ") }) : w.voice_own }));
      for (const m of v.moments) {
        const list = el("div", { className: "music-list" });
        for (const line of m.lines) {
          line.name = `${w[`voice_moment_${m.id.toLowerCase()}`] || m.id} ${line.version}`;
          list.append(row(line, fillIn));
        }
        const mine = m.lines.filter((l) => l.mine).length;
        const head = el("summary", {}, `${w[`voice_moment_${m.id.toLowerCase()}`] || m.id} (${m.lines.length})`,
          ...(mine ? [el("span", { className: "music-mine small", textContent: w.music_yours })] : []));
        parts.push(el("details", { className: "voice-moment", open: open.has(m.id) }, head, list));
        parts[parts.length - 1].dataset.moment = m.id;
      }
      group.replaceChildren(...parts);
    };
    fillIn();
    return group;
  }

  function row(s, refresh = render) {
    const w = W();
    const playBtn = el("button", { type: "button", className: "small", textContent: "▶ " + w.music_play, title: w.tip_music_play });
    const name = el("span", { className: "music-name", textContent: s.name });
    const len = el("span", { className: "muted small", textContent: clock(s.seconds) });
    const mark = s.mine ? el("span", { className: "music-mine small", textContent: w.music_yours }) : "";
    const info = where(s);
    const sub = el("div", { className: "muted small music-where" });
    if (info.line) sub.append(info.line);
    if (info.maps.length) {
      const more = el("details", {}, el("summary", { textContent: w.music_which_missions }),
        el("div", { textContent: info.maps.join(" · ") }));
      sub.append(more);
    }
    const edit = el("button", { type: "button", className: "small primary", textContent: s.mine ? w.music_change : w.music_replace,
      title: w.tip_music_replace });
    const actions = el("div", { className: "music-actions" }, playBtn, edit);
    if (s.mine) {
      const mine = el("button", { type: "button", className: "small", textContent: "▶ " + w.music_play_yours });
      const back = el("button", { type: "button", className: "link small", textContent: w.music_reset, title: w.tip_music_reset });
      mine.addEventListener("click", () => toggle(mine, "▶ " + w.music_play_yours, () => modBuffer(s.member)));
      back.addEventListener("click", async () => {
        stop();
        try {
          await api().music_reset(s.member);
          say(fill(s.version !== undefined ? w.voice_back_done : w.music_back_done, { name: s.name }), "ok");
          refresh();
        }
        catch (err) { problem(err); }
      });
      actions.append(mine, back);
    }
    playBtn.addEventListener("click", () => toggle(playBtn, "▶ " + w.music_play, () => gameBuffer(s.member)));
    edit.addEventListener("click", () => openEditor(s, refresh));
    return el("div", { className: "music-row" + (s.mine ? " edited" : "") },
      el("div", { className: "music-head" }, name, len, mark), sub, actions);
  }

  // a Play button that becomes Stop while its sound plays
  async function toggle(btn, label, load) {
    const w = W();
    if (btn.dataset.playing) { stop(); return; }
    btn.disabled = true;
    btn.textContent = w.music_reading;
    let buffer;
    try { buffer = await load(); } catch (err) { btn.disabled = false; btn.textContent = label; problem(err); return; }
    btn.disabled = false;
    btn.textContent = "■ " + w.music_stop;
    btn.dataset.playing = "1";
    play(buffer, 0, buffer.duration, null, () => { delete btn.dataset.playing; btn.textContent = label; });
  }

  // --- the editor ---
  function openEditor(s, after = render) {
    const w = W();
    stop();
    S.ed = { song: s, src: null, start: 0, end: 0, fadeIn: 0, fadeOut: 0, db: 0, game: null, drag: null, after };
    const voice = s.version !== undefined;  // a unit's voice line (voicesGroup), not a song
    $("me-title").textContent = fill(voice ? w.voice_editor_title : w.music_editor_title, { name: s.name });
    $("me-lead").textContent = fill(voice ? w.voice_editor_lead : w.music_editor_lead, { len: clock(s.seconds, true) });
    $("me-drop-text").textContent = w.music_drop;
    $("me-choose").textContent = w.music_choose;
    $("me-start-label").textContent = w.music_start;
    $("me-end-label").textContent = w.music_end;
    $("me-fadein-label").textContent = w.music_fade_in;
    $("me-fadeout-label").textContent = w.music_fade_out;
    $("me-volume-label").textContent = w.music_volume;
    $("me-match").textContent = w.music_match;
    $("me-match").title = w.tip_music_match;
    $("me-play").textContent = "▶ " + w.music_play_cut;
    $("me-game").textContent = "▶ " + w.music_play_game;
    $("me-use").textContent = w.music_use;
    $("me-use").title = w.tip_music_use;
    $("me-cancel").textContent = w.cancel;
    $("me-note").textContent = "";
    $("me-fadein").value = "0";
    $("me-fadeout").value = "0";
    $("me-volume").value = "0";
    showSource();
    $("music-editor").showModal();
    gameBuffer(s.member).then((b) => { if (S.ed && S.ed.song === s) S.ed.game = b; }).catch(() => {});
    if (s.mine) modBuffer(s.member).then((b) => { if (S.ed && S.ed.song === s && !S.ed.src) setSource(b, w.music_yours); })
      .catch(() => {});
  }

  function showSource() {
    const ed = S.ed, has = Boolean(ed && ed.src);
    for (const id of ["me-wave-box", "me-cut", "me-shape", "me-play", "me-use", "me-match"]) $(id).classList.toggle("hidden", !has);
    $("me-drop").classList.toggle("small-drop", has);
    if (has) { syncInputs(); draw(); }
  }

  function setSource(buffer, label) {
    const ed = S.ed;
    ed.src = buffer;
    ed.start = 0;
    ed.end = buffer.duration;
    ed.label = label;
    $("me-file").textContent = fill(W().music_file, { name: label, len: clock(buffer.duration, true) });
    showSource();
  }

  async function readFile(file) {
    const w = W();
    if (!file) return;
    $("me-note").textContent = w.music_reading;
    try {
      const buffer = await ctx().decodeAudioData(await file.arrayBuffer());
      setSource(buffer, file.name);
      $("me-note").textContent = "";
    } catch {
      $("me-note").textContent = w.music_cant_read;
    }
  }

  function syncInputs() {
    const ed = S.ed;
    $("me-start").value = ed.start.toFixed(1);
    $("me-end").value = ed.end.toFixed(1);
    $("me-length").textContent = fill(W().music_length, { len: clock(Math.max(0, ed.end - ed.start), true) });
    $("me-fadein-value").textContent = `${ed.fadeIn.toFixed(1)} s`;
    $("me-fadeout-value").textContent = `${ed.fadeOut.toFixed(1)} s`;
    $("me-volume-value").textContent = `${ed.db > 0 ? "+" : ""}${ed.db.toFixed(1)} dB`;
  }

  function draw(playhead) {
    const ed = S.ed, cv = $("me-wave");
    if (!ed || !ed.src) return;
    const g = cv.getContext("2d"), W2 = cv.width, H = cv.height, d = ed.src.duration;
    if (!ed.peaks || ed.peaks.w !== W2 || ed.peaks.src !== ed.src) {  // the loudest point in each column, once per file
      const chans = [];
      for (let c = 0; c < ed.src.numberOfChannels; c++) chans.push(ed.src.getChannelData(c));
      const per = Math.max(1, Math.floor(chans[0].length / W2)), peaks = new Float32Array(W2);
      for (let x = 0; x < W2; x++) {
        let m = 0;
        for (const a of chans) for (let i = x * per, e = Math.min(a.length, i + per); i < e; i += 4) { const v = Math.abs(a[i]); if (v > m) m = v; }
        peaks[x] = m;
      }
      ed.peaks = { w: W2, src: ed.src, values: peaks };
    }
    const css = getComputedStyle(document.documentElement);
    g.clearRect(0, 0, W2, H);
    g.fillStyle = css.getPropertyValue("--accent") || "#c9a227";
    for (let x = 0; x < W2; x++) { const h = Math.max(1, ed.peaks.values[x] * (H - 4)); g.fillRect(x, (H - h) / 2, 1, h); }
    const xs = (ed.start / d) * W2, xe = (ed.end / d) * W2;
    g.fillStyle = "rgba(0,0,0,0.6)";  // what's cut off, darkened
    g.fillRect(0, 0, xs, H);
    g.fillRect(xe, 0, W2 - xe, H);
    g.fillStyle = css.getPropertyValue("--text") || "#fff";
    for (const x of [xs, xe]) { g.fillRect(x - 1, 0, 3, H); g.fillRect(x - 6, 0, 13, 8); }  // the two handles
    if (playhead !== undefined) { g.fillStyle = "#e05050"; g.fillRect((playhead / d) * W2, 0, 2, H); }
  }

  function shape(param, at, len) {
    const ed = S.ed, gain = Math.pow(10, ed.db / 20);
    const fi = Math.min(ed.fadeIn, len / 2), fo = Math.min(ed.fadeOut, len / 2);
    param.setValueAtTime(fi > 0 ? 0 : gain, at);
    if (fi > 0) param.linearRampToValueAtTime(gain, at + fi);
    if (fo > 0) { param.setValueAtTime(gain, at + len - fo); param.linearRampToValueAtTime(0, at + len); }
  }

  function playCut() {
    const ed = S.ed, w = W(), btn = $("me-play");
    if (btn.dataset.playing) { stop(); return; }
    btn.dataset.playing = "1";
    btn.textContent = "■ " + w.music_stop;
    const me = play(ed.src, ed.start, ed.end, shape, () => { delete btn.dataset.playing; btn.textContent = "▶ " + w.music_play_cut; draw(); });
    const tick = () => {
      if (S.playing !== me) return;
      draw(Math.min(ed.end, ed.start + Math.max(0, S.ctx.currentTime - me.at)));
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  function rms(buffer, from, to) {
    let sum = 0, n = 0;
    for (let c = 0; c < buffer.numberOfChannels; c++) {
      const a = buffer.getChannelData(c), i0 = Math.floor(from * buffer.sampleRate), i1 = Math.min(a.length, Math.floor(to * buffer.sampleRate));
      for (let i = i0; i < i1; i += 2) { sum += a[i] * a[i]; n++; }
    }
    return n ? Math.sqrt(sum / n) : 0;
  }

  async function matchLoudness() {
    const ed = S.ed, w = W();
    try { if (!ed.game) ed.game = await gameBuffer(ed.song.member); } catch (err) { problem(err); return; }
    const mine = rms(ed.src, ed.start, ed.end), game = rms(ed.game, 0, ed.game.duration);
    if (!mine || !game) return;
    ed.db = Math.max(-20, Math.min(10, Math.round(20 * Math.log10(game / mine) * 2) / 2));
    $("me-volume").value = String(ed.db);
    syncInputs();
    $("me-note").textContent = fill(w.music_matched, { db: `${ed.db > 0 ? "+" : ""}${ed.db.toFixed(1)}` });
  }

  // the cut, faded and volume-set song in the game song's own format, as a 16-bit WAV
  async function finished() {
    const ed = S.ed, s = ed.song, len = ed.end - ed.start;
    const frames = Math.max(1, Math.round(len * s.rate));
    const off = new OfflineAudioContext(s.channels, frames, s.rate);
    const node = off.createBufferSource();
    node.buffer = ed.src;
    const gain = off.createGain();
    node.connect(gain).connect(off.destination);
    shape(gain.gain, 0, len);
    node.start(0, ed.start, len);
    const out = await off.startRendering();
    const ch = out.numberOfChannels, bytes = new Uint8Array(44 + frames * ch * 2), dv = new DataView(bytes.buffer);
    const put = (o, t) => { for (let i = 0; i < t.length; i++) bytes[o + i] = t.charCodeAt(i); };
    put(0, "RIFF"); dv.setUint32(4, 36 + frames * ch * 2, true); put(8, "WAVEfmt ");
    dv.setUint32(16, 16, true); dv.setUint16(20, 1, true); dv.setUint16(22, ch, true); dv.setUint32(24, s.rate, true);
    dv.setUint32(28, s.rate * ch * 2, true); dv.setUint16(32, ch * 2, true); dv.setUint16(34, 16, true);
    put(36, "data"); dv.setUint32(40, frames * ch * 2, true);
    const chans = [];
    for (let c = 0; c < ch; c++) chans.push(out.getChannelData(c));
    let o = 44;
    for (let i = 0; i < frames; i++) {
      for (let c = 0; c < ch; c++) {
        const v = Math.max(-1, Math.min(1, chans[c][i]));
        dv.setInt16(o, Math.round(v < 0 ? v * 32768 : v * 32767), true);
        o += 2;
      }
    }
    return bytes;
  }

  function base64(bytes) {
    let s = "";
    for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 0x8000));
    return btoa(s);
  }

  async function use() {
    const ed = S.ed, w = W(), btn = $("me-use");
    if (!ed || !ed.src || ed.end - ed.start <= 0.05) return;
    stop();
    btn.disabled = true;
    try {
      $("me-note").textContent = w.music_making;
      const wav = await finished();
      const size = 3 * 512 * 1024, count = Math.ceil(wav.length / size);  // 1.5 MB a part over the window's bridge
      let res;
      for (let i = 0; i < count; i++) {
        $("me-note").textContent = fill(w.music_saving, { n: Math.round((100 * i) / count) });
        res = await api().music_save(ed.song.member, base64(wav.subarray(i * size, (i + 1) * size)), i, count);
      }
      $("music-editor").close();
      say(fill(ed.song.version !== undefined ? w.voice_saved : w.music_saved, { name: ed.song.name, file: res.saved }), "ok");
      ed.after();
    } catch (err) {
      $("me-note").textContent = (err && err.message) || String(err);
    } finally {
      btn.disabled = false;
    }
  }

  function wire() {
    if (!document.getElementById("music-editor")) return;  // a page without the tab (a check page)
    const ed = () => S.ed;
    $("me-choose").addEventListener("click", () => $("me-file-input").click());
    $("me-file-input").addEventListener("change", (e) => { readFile(e.target.files[0]); e.target.value = ""; });
    const drop = $("me-drop");
    drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("over"); });
    drop.addEventListener("dragleave", () => drop.classList.remove("over"));
    drop.addEventListener("drop", (e) => { e.preventDefault(); drop.classList.remove("over"); readFile(e.dataTransfer.files[0]); });
    const cv = $("me-wave");
    const at = (e) => { const r = cv.getBoundingClientRect(); return Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * ed().src.duration; };
    cv.addEventListener("pointerdown", (e) => {
      if (!ed() || !ed().src) return;
      const t = at(e);
      ed().drag = Math.abs(t - ed().start) <= Math.abs(t - ed().end) ? "start" : "end";  // the nearer handle
      cv.setPointerCapture(e.pointerId);
      move(t);
    });
    const move = (t) => {
      const e2 = ed();
      t = Math.round(t * 10) / 10;  // to a tenth of a second: what the boxes show is what's used
      if (e2.drag === "start") e2.start = Math.min(t, e2.end - 0.1);
      else e2.end = Math.max(t, e2.start + 0.1);
      e2.start = Math.max(0, e2.start);
      e2.end = Math.min(e2.src.duration, e2.end);
      syncInputs();
      draw();
    };
    cv.addEventListener("pointermove", (e) => { if (ed() && ed().drag) move(at(e)); });
    cv.addEventListener("pointerup", () => { if (ed()) ed().drag = null; });
    const num = (id, key) => $(id).addEventListener("change", () => {
      const e2 = ed(), v = Number($(id).value);
      if (!Number.isFinite(v)) { syncInputs(); return; }
      e2[key] = v;
      e2.start = Math.max(0, Math.min(e2.start, e2.src.duration - 0.1));
      e2.end = Math.max(e2.start + 0.1, Math.min(e2.end, e2.src.duration));
      syncInputs();
      draw();
    });
    num("me-start", "start");
    num("me-end", "end");
    const slider = (id, key) => $(id).addEventListener("input", () => { ed()[key] = Number($(id).value); syncInputs(); });
    slider("me-fadein", "fadeIn");
    slider("me-fadeout", "fadeOut");
    slider("me-volume", "db");
    $("me-match").addEventListener("click", matchLoudness);
    $("me-play").addEventListener("click", playCut);
    $("me-game").addEventListener("click", () => toggle($("me-game"), "▶ " + W().music_play_game, () => gameBuffer(ed().song.member)));
    $("me-use").addEventListener("click", use);
    $("me-cancel").addEventListener("click", () => $("music-editor").close());
    $("music-editor").addEventListener("close", () => { stop(); S.ed = null; });
  }

  window.SoundView = {
    decodeEss,
    voicesGroup,
    open(words, lang) { S.words = words; S.lang = lang; render(); },
    setWords(words, lang) { S.words = words; S.lang = lang; render(); },
    modChanged() { render(); },
    leave() { stop(); },
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", wire); else wire();
})();
