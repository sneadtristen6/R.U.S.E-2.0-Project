// The Maps view: the game's maps on the left, one map's ground in 3D on the right, and brushes that reshape it
// (PLAN.md milestone MT, step T4). The ground is the map's own visual mesh, lit by the game's own normals and draped
// with the map's overview picture (StudioApi.map_view, rusemod/terrain.py). Brush strokes are saved in the current
// mod's maps/<map>/terrain.toml (StudioApi.terrain_add); this view draws them on the game's ground with the same
// maths as the build (rusemod/brush.py), and "Test in game" builds them into all four files that hold the ground.
// three.js is loaded from the internet (see index.html) the first time the view opens.
const $ = (id) => document.getElementById(id);
const SCALE = 1 / 1000;  // world units to scene units: a standard map is about 1,300 scene units wide
const mv = { api: null, words: {}, maps: [], current: null, lod: "lowdef", water: true, gl: null, ask: 0,
  stats: null, groundTex: {}, edit: null,
  // brush: the tool picked, its size and strength per brush (slider values), the strokes on this map (as saved),
  // the size of each group of strokes made this session (for Undo), the drag being painted, and the mod saved into
  brush: { on: false, name: "hill", settings: {}, strokes: [], groups: [], painting: null, mod: null, rampStart: null } };

// --- brushes: the same shapes and rules as rusemod/brush.py (the build's own copy decides; this one only draws) ---
// name: [kind, shape, sign, one dab per click (else dabs along a drag), size %, strength %]
const BRUSHES = {
  hill: ["add", "soft", 1, true, 6, 50],
  raise: ["add", "soft", 1, false, 3, 8],
  lower: ["add", "soft", -1, false, 3, 8],
  crater: ["add", "crater", 1, true, 4, 25],
  plateau: ["level", "flat", 1, true, 6, 15],
  flatten: ["level", "soft", 1, false, 4, 60],
  smooth: ["smooth", "soft", 1, false, 4, 60],
  ramp: ["ramp", "flat", 1, true, 3, 100],  // two clicks: where it starts, then where it ends; size is half its width
};
const CRATER_RIM = 0.35;
const HEIGHT_SHARE = 0.6;  // strength 100% = this share of the map's height range (hill, raise, lower, crater, plateau)

function shapeWeight(shape, t2) {
  if (shape === "soft") { const u = 1 - t2; return u * u; }
  const t = Math.sqrt(t2);
  if (shape === "flat") {
    if (t <= 0.5) return 1;
    const s = (t - 0.5) * 2;
    return 1 - s * s * (3 - 2 * s);
  }
  let bowl = 0, rim = 0;
  if (t2 < 0.5625) { const u = 1 - t2 / 0.5625; bowl = u * u; }
  const v = (t - 0.8) / 0.2;
  if (v > -1 && v < 1) { const w = 1 - v * v; rim = w * w; }
  return CRATER_RIM * rim - bowl;
}

// A ramp: how far along its centre line the nearest point lies (0 at the start, 1 at the end), and the squared
// distance to that point.
function along(s, x, y) {
  const dx = s.x2 - s.x, dy = s.y2 - s.y, len2 = dx * dx + dy * dy;
  let t = 0;
  if (len2 > 0) { t = ((x - s.x) * dx + (y - s.y) * dy) / len2; t = t < 0 ? 0 : t > 1 ? 1 : t; }
  const px = x - (s.x + dx * t), py = y - (s.y + dy * t);
  return [t, px * px + py * py];
}

function heightAt(s, x, y, z, average) {
  const [kind, shape, sign] = BRUSHES[s.brush], r2 = s.radius * s.radius;
  if (kind === "ramp") {
    const [t, d2] = along(s, x, y);
    if (d2 >= r2) return z;
    const target = s.level + (s.level2 - s.level) * t;
    return z + (target - z) * (s.weight * shapeWeight(shape, d2 / r2));
  }
  const dx = x - s.x, dy = y - s.y, d2 = dx * dx + dy * dy;
  if (d2 >= r2) return z;
  const p = shapeWeight(shape, d2 / r2);
  if (kind === "add") return z + sign * s.height * p;
  if (kind === "level") return z + (s.level - z) * (s.weight * p);
  return z + (average(x, y) - z) * (s.weight * p);
}

// The square around a stroke's circle (a ramp: around its whole band): x min, x max, y min, y max.
function boxOf(s) {
  if (s.brush === "ramp") {
    return [Math.min(s.x, s.x2) - s.radius, Math.max(s.x, s.x2) + s.radius,
            Math.min(s.y, s.y2) - s.radius, Math.max(s.y, s.y2) + s.radius];
  }
  return [s.x - s.radius, s.x + s.radius, s.y - s.radius, s.y + s.radius];
}

function covers(s, x, y) {
  const r2 = s.radius * s.radius;
  if (s.brush === "ramp") return along(s, x, y)[1] < r2;
  const dx = x - s.x, dy = y - s.y;
  return dx * dx + dy * dy < r2;
}

function el(tag, props, ...children) {
  const node = document.createElement(tag);
  Object.assign(node, props || {});
  for (const c of children) node.append(c);
  return node;
}

function fill(text, values) {
  return text.replace(/\{(\w+)\}/g, (_, k) => (k in values ? values[k] : `{${k}}`));
}

// A buffer from rusemod.terrain._pack: base64 of zlib data, unpacked with the browser's own inflater.
async function unpack(b64, Type) {
  const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
  const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream("deflate"));
  return new Type(await new Response(stream).arrayBuffer());
}

// --- the 3D scene, made once ---
async function scene3d() {
  if (mv.gl) return mv.gl;
  const THREE = await import("three");
  const { OrbitControls } = await import("three/addons/controls/OrbitControls.js");
  const host = $("map-canvas");
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  host.append(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x9fb8c8);
  const camera = new THREE.PerspectiveCamera(45, 1, 1, 20000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.maxPolarAngle = Math.PI * 0.48;  // never under the ground
  controls.screenSpacePanning = false;       // right-drag slides over the map instead of up into the sky
  scene.add(new THREE.HemisphereLight(0xe3ecf2, 0x40372a, 1.4));
  const sun = new THREE.DirectionalLight(0xfff1dc, 2.0);
  sun.position.set(-0.6, 1.0, -0.35);         // from the north-west, high: slopes read clearly
  scene.add(sun);
  const draw = () => renderer.render(scene, camera);
  controls.addEventListener("change", draw);
  new ResizeObserver(() => {
    const w = host.clientWidth, h = host.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    draw();
  }).observe(host);
  const ring = new THREE.Mesh(new THREE.RingGeometry(0.94, 1, 72),
    new THREE.MeshBasicMaterial({ color: 0xc8a64b, transparent: true, opacity: 0.9, depthTest: false, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2;
  ring.renderOrder = 10;
  ring.visible = false;
  scene.add(ring);
  // a ramp being made: a ring where it starts and a line from there to the pointer
  const startRing = ring.clone();
  const guide = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
    new THREE.LineBasicMaterial({ color: 0xc8a64b, transparent: true, opacity: 0.9, depthTest: false }));
  guide.renderOrder = 10;
  guide.visible = false;
  scene.add(startRing, guide);
  mv.gl = { THREE, renderer, scene, camera, controls, draw, ground: null, water: null, ring, startRing, guide,
    raycaster: new THREE.Raycaster(), ndc: new THREE.Vector2() };
  watchPointer();
  setBrushMode(mv.brush.on);
  return mv.gl;
}

// Game axes are x east, y south, z up; the scene's are X east, Y up, Z south (so north is away from the camera).
async function meshes(view) {
  const { THREE, renderer } = mv.gl;
  const [x0, y0, z0, x1, y1, z1] = view.bounds;
  const Q = view.q_max, n = view.vertices;
  const [q, nb, wq, tri, wtri] = await Promise.all([unpack(view.positions, Uint16Array),
    unpack(view.normals, Uint8Array), unpack(view.water_heights, Uint16Array), unpack(view.triangles, Uint32Array),
    unpack(view.water, Uint32Array)]);
  // turning the game's axes into the scene's mirrors the map, which flips every triangle's winding: flip it back, so
  // the side facing up is the front and is lit from above
  for (const list of [tri, wtri]) {
    for (let k = 0; k < list.length; k += 3) { const b = list[k + 1]; list[k + 1] = list[k + 2]; list[k + 2] = b; }
  }
  const sx = (x1 - x0) / Q, sy = (y1 - y0) / Q, sz = (z1 - z0) / Q;
  const pos = new Float32Array(n * 3), wpos = new Float32Array(n * 3), nor = new Float32Array(n * 3);
  const uv = new Float32Array(n * 2);
  const wx = new Float64Array(n), wy = new Float64Array(n), base = new Float64Array(n), fixed = new Uint8Array(n);
  for (let i = 0; i < n; i++) {
    const qx = q[3 * i], qy = q[3 * i + 1];
    wx[i] = x0 + qx * sx; wy[i] = y0 + qy * sy; base[i] = z0 + q[3 * i + 2] * sz;
    fixed[i] = qx === 0 || qx === Q || qy === 0 || qy === Q ? 1 : 0;  // the map's edge never moves
    const X = (x0 + qx * sx) * SCALE, Z = (y0 + qy * sy) * SCALE;
    pos[3 * i] = X; pos[3 * i + 1] = (z0 + q[3 * i + 2] * sz) * SCALE; pos[3 * i + 2] = Z;
    wpos[3 * i] = X; wpos[3 * i + 1] = (z0 + wq[i] * sz) * SCALE; wpos[3 * i + 2] = Z;
    nor[3 * i] = nb[3 * i] / 127.5 - 1; nor[3 * i + 1] = nb[3 * i + 2] / 127.5 - 1; nor[3 * i + 2] = nb[3 * i + 1] / 127.5 - 1;
    uv[2 * i] = qx / Q; uv[2 * i + 1] = 1 - qy / Q;  // the picture is north up: row = y / map size
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setAttribute("normal", new THREE.BufferAttribute(nor, 3));
  g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  g.setIndex(new THREE.BufferAttribute(tri, 1));
  let picture = mv.groundTex[view.pack] || null;  // the real ground textures, if this map already has them
  if (!picture && view.picture) {
    picture = await new THREE.TextureLoader().loadAsync(view.picture);
    picture.colorSpace = THREE.SRGBColorSpace;
    picture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  }
  const ground = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ map: picture, color: picture ? 0xffffff : 0x7d8a5a,
    side: THREE.DoubleSide }));
  const wg = new THREE.BufferGeometry();
  wg.setAttribute("position", new THREE.BufferAttribute(wpos, 3));
  wg.setIndex(new THREE.BufferAttribute(wtri, 1));
  wg.computeVertexNormals();
  const water = new THREE.Mesh(wg, new THREE.MeshLambertMaterial({ color: 0x2f6f8f, transparent: true, opacity: 0.72,
    side: THREE.DoubleSide, depthWrite: false }));
  const edit = { n, wx, wy, base, z: Float64Array.from(base), fixed, touched: new Uint8Array(n),
    baseNormals: nor.slice(), bounds: view.bounds, index: bucketIndex(wx, wy, x0, y0, x1, y1), grid: null };
  return { ground, water, center: [(x0 + x1) / 2 * SCALE, (z0 + z1) / 2 * SCALE, (y0 + y1) / 2 * SCALE],
    size: Math.max(x1 - x0, y1 - y0) * SCALE, edit };
}

// --- the drawn ground, reshaped by the strokes ---
function bucketIndex(wx, wy, x0, y0, x1, y1) {
  const step = Math.max(x1 - x0, y1 - y0, 1) / 128, cells = new Map();
  for (let i = 0; i < wx.length; i++) {
    const key = Math.floor((wx[i] - x0) / step) * 65536 + Math.floor((wy[i] - y0) / step);
    let list = cells.get(key);
    if (!list) cells.set(key, (list = []));
    list.push(i);
  }
  return { step, x0, y0, cells };
}

function near(index, xlo, xhi, ylo, yhi, fn) {
  const b0 = Math.max(-1, Math.floor((xlo - index.x0) / index.step)), b1 = Math.min(129, Math.floor((xhi - index.x0) / index.step));
  const c0 = Math.max(-1, Math.floor((ylo - index.y0) / index.step)), c1 = Math.min(129, Math.floor((yhi - index.y0) / index.step));
  for (let bx = b0; bx <= b1; bx++) {
    for (let by = c0; by <= c1; by++) {
      const list = index.cells.get(bx * 65536 + by);
      if (list) for (const i of list) fn(i);
    }
  }
}

// The ground as a coarse grid of heights that follows every stroke: the smooth brush pulls toward its local average
// (the mean over about a third of the brush's radius), like HeightGrid in rusemod/brush.py.
function makeGrid(ed) {
  const [x0, y0, , x1, y1] = ed.bounds;
  const cols = 256, rows = Math.max(1, Math.round(256 * (y1 - y0) / (x1 - x0)));
  const sx = (x1 - x0) / cols, sy = (y1 - y0) / rows;
  const sum = new Float64Array(rows * cols), cnt = new Uint32Array(rows * cols);
  for (let i = 0; i < ed.n; i++) {
    const c = Math.min(cols - 1, Math.max(0, Math.floor((ed.wx[i] - x0) / sx)));
    const r = Math.min(rows - 1, Math.max(0, Math.floor((ed.wy[i] - y0) / sy)));
    sum[r * cols + c] += ed.z[i];
    cnt[r * cols + c] += 1;
  }
  const z = new Float64Array(rows * cols).fill(NaN);
  for (let k = 0; k < z.length; k++) if (cnt[k]) z[k] = sum[k] / cnt[k];
  const fillLine = (get, set, len) => {
    let last = NaN;
    const vals = Array.from({ length: len }, (_, i) => get(i));
    const known = vals.map((v, i) => (Number.isNaN(v) ? -1 : i)).filter((i) => i >= 0);
    if (!known.length) return;
    let j = 0;
    for (let i = 0; i < len; i++) {
      if (!Number.isNaN(vals[i])) continue;
      while (j + 1 < known.length && Math.abs(known[j + 1] - i) < Math.abs(known[j] - i)) j++;
      set(i, vals[known[j]]);
      last = vals[known[j]];
    }
    return last;
  };
  for (let r = 0; r < rows; r++) fillLine((c) => z[r * cols + c], (c, v) => { z[r * cols + c] = v; }, cols);
  for (let c = 0; c < cols; c++) fillLine((r) => z[r * cols + c], (r, v) => { z[r * cols + c] = v; }, rows);
  let low = Infinity;
  for (const v of z) if (!Number.isNaN(v) && v < low) low = v;
  for (let k = 0; k < z.length; k++) if (Number.isNaN(z[k])) z[k] = Number.isFinite(low) ? low : 0;
  return { rows, cols, x0, y0, sx, sy, z };
}

function gridSpan(g, s) {
  const [xlo, xhi, ylo, yhi] = boxOf(s);
  const c0 = Math.max(0, Math.floor((xlo - g.x0) / g.sx) - 1);
  const c1 = Math.min(g.cols - 1, Math.floor((xhi - g.x0) / g.sx) + 1);
  const r0 = Math.max(0, Math.floor((ylo - g.y0) / g.sy) - 1);
  const r1 = Math.min(g.rows - 1, Math.floor((yhi - g.y0) / g.sy) + 1);
  return [r0, r1, c0, c1];
}

function gridAverage(g, s) {
  const k = Math.max(1, Math.min(8, Math.round(s.radius / (3 * Math.min(g.sx, g.sy)))));
  const [r0, r1, c0, c1] = gridSpan(g, s);
  const mean = new Map();
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      let total = 0, count = 0;
      for (let rr = Math.max(0, r - k); rr <= Math.min(g.rows - 1, r + k); rr++) {
        for (let cc = Math.max(0, c - k); cc <= Math.min(g.cols - 1, c + k); cc++) { total += g.z[rr * g.cols + cc]; count++; }
      }
      mean.set(r * g.cols + c, total / count);
    }
  }
  const at = (r, c) => mean.get(Math.min(Math.max(r, r0), r1) * g.cols + Math.min(Math.max(c, c0), c1));
  return (x, y) => {
    const fc = (x - g.x0) / g.sx - 0.5, fr = (y - g.y0) / g.sy - 0.5;
    const c = Math.min(Math.max(Math.floor(fc), c0), c1), r = Math.min(Math.max(Math.floor(fr), r0), r1);
    const tx = Math.min(Math.max(fc - c, 0), 1), ty = Math.min(Math.max(fr - r, 0), 1);
    const top = at(r, c) + (at(r, c + 1) - at(r, c)) * tx, bottom = at(r + 1, c) + (at(r + 1, c + 1) - at(r + 1, c)) * tx;
    return top + (bottom - top) * ty;
  };
}

function gridApply(g, s, average) {
  const [r0, r1, c0, c1] = gridSpan(g, s);
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      const k = r * g.cols + c;
      g.z[k] = heightAt(s, g.x0 + (c + 0.5) * g.sx, g.y0 + (r + 0.5) * g.sy, g.z[k], average);
    }
  }
}

function applyStroke(ed, s) {
  let average = null;
  if (s.brush === "smooth") {
    if (!ed.grid) ed.grid = makeGrid(ed);
    average = gridAverage(ed.grid, s);
  }
  const [xlo, xhi, ylo, yhi] = boxOf(s);
  near(ed.index, xlo, xhi, ylo, yhi, (i) => {
    if (ed.fixed[i] || !covers(s, ed.wx[i], ed.wy[i])) return;
    ed.z[i] = heightAt(s, ed.wx[i], ed.wy[i], ed.z[i], average);
    ed.touched[i] = 1;
  });
  if (ed.grid) gridApply(ed.grid, s, average);
}

// Copy the heights into what the screen draws; `all` also puts back the points no stroke touches any more.
// Normals are worked out again where the ground moved (the game's own everywhere else).
function redraw(all, normals) {
  const ed = mv.edit, gl = mv.gl;
  if (!ed || !gl || !gl.ground) return;
  const g = gl.ground.geometry, pos = g.attributes.position.array;
  const z0 = ed.bounds[2], z1 = ed.bounds[5];
  for (let i = 0; i < ed.n; i++) {
    if (all || ed.touched[i]) pos[3 * i + 1] = Math.min(Math.max(ed.z[i], z0), z1) * SCALE;
  }
  g.attributes.position.needsUpdate = true;
  if (normals) {
    g.computeVertexNormals();
    const nor = g.attributes.normal.array;
    for (let i = 0; i < ed.n; i++) {
      if (!ed.touched[i]) { nor[3 * i] = ed.baseNormals[3 * i]; nor[3 * i + 1] = ed.baseNormals[3 * i + 1]; nor[3 * i + 2] = ed.baseNormals[3 * i + 2]; }
    }
    g.attributes.normal.needsUpdate = true;
    ed.normalsAt = performance.now();
  }
  g.computeBoundingSphere();
  g.computeBoundingBox();
  gl.draw();
}

// Back to the game's ground, then every stroke again, in order (after Undo, another mod, or the other detail level).
function reapply() {
  const ed = mv.edit;
  if (!ed) return;
  ed.z.set(ed.base);
  ed.touched.fill(0);
  ed.grid = null;
  for (const s of mv.brush.strokes) applyStroke(ed, s);
  redraw(true, true);
}

function forget(mesh) {
  if (!mesh) return;
  mv.gl.scene.remove(mesh);
  mesh.geometry.dispose();
  if (mesh.material.map && !mesh.material.map.userData.keep) mesh.material.map.dispose();
  mesh.material.dispose();
}

function wait(ms) { return new Promise((r) => setTimeout(r, ms)); }

// The map's real ground textures (its texture tiles, stitched once by the engine and kept in the cache) replace the
// small overview picture as soon as they're ready. Kept per map, so switching detail doesn't load them again.
async function realGround(pack, ask) {
  const w = mv.words, note = $("map-ground");
  let tex = mv.groundTex[pack];
  if (!tex) {
    let res = await mv.api.map_ground(pack);
    while (res && res.job) {
      let view, since = 0;
      do {
        await wait(700);
        view = await mv.api.job(res.job, since);
        since = view.count;
        if (ask !== mv.ask) return;
        if (view.lines.length) note.textContent = fill(w.ground_loading, { progress: view.lines[view.lines.length - 1] });
      } while (view.state === "running");
      if (view.state !== "done") { note.textContent = view.message; return; }
      res = await mv.api.map_ground(pack);
    }
    if (!res || !res.url) { note.textContent = ""; return; }
    note.textContent = fill(w.ground_loading, { progress: "" });
    const { THREE, renderer } = mv.gl;
    tex = await new THREE.TextureLoader().loadAsync(res.url);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = renderer.capabilities.getMaxAnisotropy();
    tex.userData.keep = true;
    mv.groundTex[pack] = tex;
  }
  if (ask !== mv.ask || !mv.gl.ground) return;
  const mat = mv.gl.ground.material;
  if (mat.map && !mat.map.userData.keep) mat.map.dispose();
  mat.map = tex;
  mat.color.set(0xffffff);
  mat.needsUpdate = true;
  mv.gl.draw();
  note.textContent = "";
}

// --- showing one map ---
async function show(pack, keepCamera) {
  const w = mv.words, ask = ++mv.ask;
  mv.current = pack;
  renderList();
  $("map-pick").textContent = w.map_loading;
  $("map-pick").classList.remove("hidden");
  try {
    await scene3d();
  } catch (err) {
    $("map-pick").textContent = w.no_viewer;
    console.error(err);
    return;
  }
  let view, made;
  try {
    view = await mv.api.map_view(pack, mv.lod);
    if (ask !== mv.ask) return;  // another map was picked meanwhile
    made = await meshes(view);
  } catch (err) {
    $("map-pick").textContent = (err && err.message) || String(err);
    return;
  }
  if (ask !== mv.ask) return;
  const gl = mv.gl;
  forget(gl.ground);
  forget(gl.water);
  gl.ground = made.ground;
  gl.water = made.water;
  gl.water.visible = mv.water;
  gl.scene.add(gl.ground, gl.water);
  mv.edit = made.edit;
  mv.brush.painting = null;
  cancelRamp();
  if (!keepCamera) {
    const [cx, cy, cz] = made.center, d = made.size;
    gl.camera.near = d / 2000;
    gl.camera.far = d * 8;
    gl.camera.updateProjectionMatrix();
    gl.camera.position.set(cx, cy + d * 0.55, cz + d * 0.75);  // from the south, looking north
    gl.controls.target.set(cx, cy, cz);
    gl.controls.update();
  }
  gl.draw();
  const m = mv.maps.find((x) => x.pack === pack);
  $("map-title").textContent = m ? m.names[0] || m.pack : pack;
  mv.stats = { points: view.vertices.toLocaleString(), triangles: view.triangle_count.toLocaleString() };
  $("map-stats").textContent = fill(w.map_stats, mv.stats);
  $("map-pick").classList.add("hidden");
  $("map-hud").classList.remove("hidden");
  $("map-tools").classList.remove("hidden");
  loadStrokes(pack, ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
  realGround(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
}

// --- the brush tools ---
function settingsOf(name) {
  if (!mv.brush.settings[name]) mv.brush.settings[name] = { size: BRUSHES[name][4], strength: BRUSHES[name][5] };
  return mv.brush.settings[name];
}

function brushNote(text, kind) {
  const note = $("brush-note");
  note.textContent = text || "";
  note.className = "small" + (kind === "error" ? " error-text" : "");
}

function showCount() {
  const w = mv.words, n = mv.brush.strokes.length;
  $("brush-count").textContent = n ? fill(w.brush_count, { n: n.toLocaleString() }) : "";
  $("brush-undo").disabled = !n || !mv.brush.mod;
  $("brush-clear").disabled = !n || !mv.brush.mod;
  if (!n) $("brush-sure").classList.add("hidden");
}

async function loadStrokes(pack, ask) {
  const res = await mv.api.terrain(pack);
  if (ask !== mv.ask) return;
  mv.brush.mod = res.mod;
  mv.brush.strokes = res.strokes;
  mv.brush.groups = [];
  cancelRamp();
  $("brush-sure").classList.add("hidden");
  reapply();
  showCount();
  renderBrushes();
  brushNote(res.mod ? (res.strokes.length ? mv.words.brush_note : "") : mv.words.no_mod);
}

function renderBrushes() {
  const w = mv.words, b = mv.brush;
  $("brush-list").replaceChildren(...Object.keys(BRUSHES).map((name) => {
    const chip = el("button", { type: "button", className: "chip", textContent: w["brush_" + name] || name });
    chip.setAttribute("aria-pressed", String(b.on && b.name === name));
    chip.addEventListener("click", () => pickBrush(name));
    return chip;
  }));
  const set = settingsOf(b.name);
  $("brush-size").value = set.size;
  $("brush-strength").value = set.strength;
  $("brush-look").setAttribute("aria-pressed", String(!b.on));
  $("map-help").textContent = b.on ? w.brush_help : w.map_help;
  showCount();
}

function pickBrush(name) {
  const b = mv.brush;
  if (b.name !== name) cancelRamp();
  b.name = name;
  setBrushMode(true);
  if (!b.mod) brushNote(mv.words.no_mod, "error");
  else if (name === "ramp") brushNote(mv.words.ramp_help);
}

// A ramp half made (its start clicked) is dropped: another brush, another map or mod, Look around, Esc.
function cancelRamp() {
  mv.brush.rampStart = null;
  const gl = mv.gl;
  if (gl && gl.guide && (gl.guide.visible || gl.startRing.visible)) {
    gl.guide.visible = false;
    gl.startRing.visible = false;
    gl.draw();
  }
}

function setBrushMode(on) {
  const gl = mv.gl;
  mv.brush.on = on;
  if (!on) cancelRamp();
  if (gl) {
    const M = gl.THREE.MOUSE;
    gl.controls.mouseButtons = on ? { LEFT: null, MIDDLE: M.ROTATE, RIGHT: M.PAN }
                                  : { LEFT: M.ROTATE, MIDDLE: M.DOLLY, RIGHT: M.PAN };
    if (!on && gl.ring) { gl.ring.visible = false; gl.draw(); }
    gl.renderer.domElement.style.cursor = on ? "crosshair" : "";
  }
  renderBrushes();
}

// The world numbers of a new stroke, from the brush picked and its sliders.
function newStroke(x, y, level, end) {
  const name = mv.brush.name, [kind] = BRUSHES[name], set = settingsOf(name);
  const [x0, , z0, x1, , z1] = mv.edit.bounds;
  const s = { brush: name, x, y, radius: set.size / 100 * (x1 - x0) };
  if (kind === "add") s.height = set.strength / 100 * HEIGHT_SHARE * (z1 - z0);
  if (kind === "level") { s.level = level; s.weight = name === "plateau" ? 1 : set.strength / 100; }
  if (kind === "smooth") s.weight = set.strength / 100;
  if (kind === "ramp") { s.level = level; s.weight = set.strength / 100; s.x2 = end.x; s.y2 = end.y; s.level2 = end.z; }
  return s;
}

function hitGround(ev) {
  const gl = mv.gl, rect = gl.renderer.domElement.getBoundingClientRect();
  gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  gl.raycaster.setFromCamera(gl.ndc, gl.camera);
  const hit = gl.raycaster.intersectObject(gl.ground, false)[0];
  return hit ? hit.point : null;  // scene: X east, Y up, Z south
}

function showRing(p) {
  const gl = mv.gl;
  if (!gl.ring) return;
  const set = settingsOf(mv.brush.name), [x0, , , x1] = mv.edit.bounds;
  const r = set.size / 100 * (x1 - x0) * SCALE, lift = r * 0.02;
  gl.ring.visible = Boolean(p);
  if (p) {
    gl.ring.position.set(p.x, p.y + lift, p.z);
    gl.ring.scale.set(r, r, r);
  }
  const start = mv.brush.rampStart;
  gl.startRing.visible = Boolean(start);
  gl.guide.visible = Boolean(start && p);
  if (start) {
    gl.startRing.position.set(start.sx, start.sy + lift, start.sz);
    gl.startRing.scale.set(r, r, r);
  }
  if (start && p) {
    const pos = gl.guide.geometry.attributes.position;
    pos.setXYZ(0, start.sx, start.sy + lift, start.sz);
    pos.setXYZ(1, p.x, p.y + lift, p.z);
    pos.needsUpdate = true;
    gl.guide.geometry.computeBoundingSphere();
  }
  gl.draw();
}

function dab(group, x, y) {
  const s = newStroke(x, y, group.level, group.end);
  group.strokes.push(s);
  group.last = [x, y];
  mv.brush.strokes.push(s);
  applyStroke(mv.edit, s);
  const ed = mv.edit;
  redraw(false, !ed.normalsAt || performance.now() - ed.normalsAt > 150);
}

function paintTo(p) {
  const g = mv.brush.painting;
  if (!g || g.stamp || !g.last) return;
  const x = p.x / SCALE, y = p.z / SCALE, spacing = g.strokes[0].radius / 3;
  let [lx, ly] = g.last;
  let dist = Math.hypot(x - lx, y - ly);
  while (dist >= spacing) {
    lx += (x - lx) * spacing / dist;
    ly += (y - ly) * spacing / dist;
    dab(g, lx, ly);
    dist = Math.hypot(x - lx, y - ly);
  }
}

async function finishStroke() {
  const g = mv.brush.painting;
  mv.brush.painting = null;
  if (!g || !g.strokes.length) return;
  redraw(false, true);
  const pack = mv.current;
  try {
    await mv.api.terrain_add(pack, g.strokes);
    if (pack !== mv.current) return;
    mv.brush.groups.push(g.strokes.length);
    showCount();
    brushNote(mv.words.brush_note);
  } catch (err) {
    if (pack !== mv.current) return;
    mv.brush.strokes.splice(g.start, g.strokes.length);  // not saved: take it off the view again
    reapply();
    showCount();
    brushNote((err && err.message) || String(err), "error");
  }
}

async function undoStroke() {
  const b = mv.brush, pack = mv.current;
  if (!b.mod || !b.strokes.length || b.painting) return;
  const n = b.groups.length ? b.groups.pop() : 1;
  try {
    const res = await mv.api.terrain_undo(pack, n);
    if (pack !== mv.current) return;
    b.strokes.splice(b.strokes.length - res.removed, res.removed);
    reapply();
    showCount();
  } catch (err) { brushNote((err && err.message) || String(err), "error"); }
}

// "Start over": every stroke on this map goes (after the question under the button).
async function clearStrokes() {
  const b = mv.brush, pack = mv.current;
  $("brush-sure").classList.add("hidden");
  if (!b.mod || !b.strokes.length || b.painting) return;
  try {
    await mv.api.terrain_undo(pack, b.strokes.length);
    if (pack !== mv.current) return;
    b.strokes = [];
    b.groups = [];
    reapply();
    showCount();
    brushNote(b.name === "ramp" ? mv.words.ramp_help : "");
  } catch (err) { brushNote((err && err.message) || String(err), "error"); }
}

function watchPointer() {
  const gl = mv.gl, canvas = gl.renderer.domElement;
  let pending = null, frame = 0;
  const tick = () => {
    frame = 0;
    if (!pending || !mv.brush.on || !gl.ground) return;
    const p = hitGround(pending);
    showRing(p);
    if (p && mv.brush.painting) paintTo(p);
  };
  canvas.addEventListener("pointermove", (ev) => {
    if (!mv.brush.on) return;
    pending = ev;
    if (!frame) frame = requestAnimationFrame(tick);
  });
  canvas.addEventListener("pointerdown", (ev) => {
    if (!mv.brush.on || ev.button !== 0 || !gl.ground || !mv.edit) return;
    if (!mv.brush.mod) { brushNote(mv.words.no_mod, "error"); return; }
    const p = hitGround(ev);
    if (!p) return;
    ev.preventDefault();
    const name = mv.brush.name, [kind, , , stamp] = BRUSHES[name], set = settingsOf(name);
    const x = p.x / SCALE, y = p.z / SCALE, z = p.y / SCALE, [, , z0, , , z1] = mv.edit.bounds;
    const level = kind !== "level" ? 0 : name === "plateau" ? z + set.strength / 100 * HEIGHT_SHARE * (z1 - z0) : z;
    if (kind === "ramp") {  // two clicks: where it starts (the ground's height there), then where it ends
      const start = mv.brush.rampStart;
      if (!start) { mv.brush.rampStart = { x, y, z, sx: p.x, sy: p.y, sz: p.z }; showRing(p); return; }
      if (start.x === x && start.y === y) return;
      mv.brush.rampStart = null;
      showRing(p);
      const ramp = { strokes: [], last: null, level: start.z, stamp: true, start: mv.brush.strokes.length, end: { x, y, z } };
      mv.brush.painting = ramp;
      dab(ramp, start.x, start.y);
      finishStroke();
      return;
    }
    const group = { strokes: [], last: null, level, stamp, start: mv.brush.strokes.length };
    mv.brush.painting = group;
    dab(group, x, y);
    if (stamp) finishStroke();
    else canvas.setPointerCapture(ev.pointerId);
  });
  for (const type of ["pointerup", "pointercancel"]) {
    canvas.addEventListener(type, () => { if (mv.brush.painting) finishStroke(); });
  }
  canvas.addEventListener("pointerleave", () => { if (mv.brush.on && gl.ring) { gl.ring.visible = false; gl.draw(); } });
}

function renderList() {
  $("map-list").replaceChildren(...mv.maps.map((m) => {
    const b = el("button", { type: "button", title: m.file },
      el("span", { className: "name", textContent: m.names[0] || m.pack }),
      el("span", { className: "sub", textContent: m.names.length > 1 ? `${m.pack} · ${m.names.length}` : m.pack }));
    b.setAttribute("aria-current", String(m.pack === mv.current));
    b.addEventListener("click", () => show(m.pack));
    return el("li", null, b);
  }));
}

function renderWords() {
  const w = mv.words;
  $("map-detail").textContent = mv.lod === "highdef" ? w.detail_high : w.detail_low;
  $("map-water-label").textContent = w.water;
  $("map-help").textContent = mv.brush.on ? w.brush_help : w.map_help;
  $("brush-title").textContent = w.shape_ground;
  $("brush-size-label").textContent = w.brush_size;
  $("brush-strength-label").textContent = w.brush_strength;
  $("brush-look").textContent = w.brush_look;
  $("brush-undo").textContent = w.brush_undo;
  $("brush-clear").textContent = w.brush_clear;
  $("brush-clear-yes").textContent = w.remove_all;
  $("brush-clear-no").textContent = w.cancel;
  if (!mv.current) $("map-pick").textContent = w.pick_map;
  renderBrushes();
}

let wired = false;
function wire() {
  if (wired) return;
  wired = true;
  $("map-detail").addEventListener("click", () => {
    mv.lod = mv.lod === "lowdef" ? "highdef" : "lowdef";
    renderWords();
    if (mv.current) show(mv.current, true);
  });
  $("map-water").addEventListener("change", (e) => {
    mv.water = e.target.checked;
    if (mv.gl && mv.gl.water) { mv.gl.water.visible = mv.water; mv.gl.draw(); }
  });
  $("brush-size").addEventListener("input", (e) => { settingsOf(mv.brush.name).size = Number(e.target.value); });
  $("brush-strength").addEventListener("input", (e) => { settingsOf(mv.brush.name).strength = Number(e.target.value); });
  $("brush-look").addEventListener("click", () => setBrushMode(false));
  $("brush-undo").addEventListener("click", () => undoStroke());
  $("brush-clear").addEventListener("click", () => {
    $("brush-sure-text").textContent = fill(mv.words.really_clear, { n: mv.brush.strokes.length.toLocaleString() });
    $("brush-sure").classList.remove("hidden");
    $("brush-clear-yes").focus();
  });
  $("brush-clear-no").addEventListener("click", () => $("brush-sure").classList.add("hidden"));
  $("brush-clear-yes").addEventListener("click", () => clearStrokes());
  window.addEventListener("keydown", (e) => { if (e.key === "Escape") cancelRamp(); });
}

// app.js opens the view when its tab is picked, and passes the words on every language change.
window.MapView = {
  async open(api, words) {
    mv.api = api;
    mv.words = words;
    wire();
    renderWords();
    if (!mv.maps.length) {
      try {
        mv.maps = (await api.maps()).maps;
      } catch (err) {
        $("map-pick").textContent = (err && err.message) || String(err);
        return;
      }
      renderList();
    }
  },
  setWords(words) {
    mv.words = words;
    renderWords();
    if (mv.stats) $("map-stats").textContent = fill(words.map_stats, mv.stats);
  },
  // another mod was picked: its strokes on this map (or none) replace the ones drawn
  modChanged() {
    if (mv.current && mv.edit) loadStrokes(mv.current, mv.ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
  },
};
window.dispatchEvent(new Event("mapview-ready"));
