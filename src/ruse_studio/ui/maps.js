// The Maps view: the game's maps on the left, one map's ground in 3D on the right, and brushes that reshape it
// (PLAN.md milestone MT, step T4). The ground is the map's own visual mesh, lit by the game's own normals and draped
// with the map's overview picture (StudioApi.map_view, rusemod/terrain.py). Brush strokes are saved in the current
// mod's maps/<map>/terrain.toml (StudioApi.terrain_add); this view draws them on the game's ground with the same
// maths as the build (rusemod/brush.py), and "Test in game" builds them into all four files that hold the ground.
// three.js is loaded from the internet (see index.html) the first time the view opens.
const $ = (id) => document.getElementById(id);
const SCALE = 1 / 1000;  // world units to scene units: a standard map is about 1,300 scene units wide
const mv = { api: null, words: {}, lang: "base", maps: [], current: null, lod: "lowdef", water: true, gl: null, ask: 0,
  stats: null, groundTex: {}, edit: null, size: 0,  // size: the map's longer side in scene units (the keys' speed)
  // brush: the tool picked, its size and strength per brush (slider values), the strokes on this map (as saved),
  // the size of each group of strokes made this session (for Undo), the drag being painted, and the mod saved into
  brush: { on: false, name: "hill", settings: {}, strokes: [], groups: [], painting: null, mod: null, rampStart: null },
  // scenery: which groups are shown, the map's scenery (StudioApi.map_scenery) and its drawn shapes per group
  scenery: { show: { building: true, prop: true, vegetation: true }, data: null, meshes: {}, models: {} },
  // placing: on or not, the group and type picked, the next object's turn and size, what the mod places on this map
  place: { on: false, group: "building", type: null, turn: 0, size: 1, objects: [], meshes: {}, mod: null,
    // how: one, area or line; area: the area brush's radius and spacing: per kind, in metres; groups: how many objects
    // each click, area or line placed (for Undo); lineStart: a line's first click; painting: an area being dragged
    how: "one", area: 40, spacing: {}, groups: [], lineStart: null, painting: null } };

// --- brushes: the same shapes and rules as rusemod/brush.py (the build's own copy decides; this one only draws) ---
// name: [kind, shape, sign, one dab per click (else dabs along a drag), size %, strength %]
const BRUSHES = {
  hill: ["add", "soft", 1, true, 6, 40],
  raise: ["add", "soft", 1, false, 3, 10],
  lower: ["add", "soft", -1, false, 3, 10],
  crater: ["add", "crater", 1, true, 4, 30],
  plateau: ["level", "flat", 1, true, 6, 20],
  flatten: ["level", "soft", 1, false, 4, 60],
  level: ["level", "flat", 1, false, 3, 100],  // the ground where the drag starts, painted flat at that height
  smooth: ["smooth", "soft", 1, false, 4, 60],
  ramp: ["ramp", "flat", 1, true, 3, 100],  // two clicks: where it starts, then where it ends; size is half its width
};
const CRATER_RIM = 0.35;
const HEIGHT_SHARE = 0.6;  // strength 100% = this share of the map's height range (hill, raise, lower, crater, plateau)

// How far one dab moves the ground at a strength (1-100): the square of the slider, so its lower half moves the
// ground in small steps (strength 10 = 1% of the top) and its top still makes big hills.
function lift(strength, z0, z1) {
  const s = strength / 100;
  return s * s * HEIGHT_SHARE * (z1 - z0);
}

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
  placeScenery();
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

// --- the real 3D models (StudioApi.map_models: the game's .spk models and their atlases, made once per map and
// kept in the cache; from DomesticNukes and his Claude's notes). Until they're in, and for a type without a model,
// the simple shapes below stand in. Each type is one instanced mesh per part (a part: one atlas), drawn where the
// shapes stand; the shapes stay, unseen, for pointing at things (sceneryAt). ---
async function loadModels(pack, ask) {
  const w = mv.words, note = $("map-ground");
  let res = await mv.api.map_models(pack);
  while (res && res.job) {
    let view, since = 0;
    do {
      await wait(700);
      view = await mv.api.job(res.job, since);
      since = view.count;
      if (ask !== mv.ask) return;
      if (view.lines.length) note.textContent = fill(w.models_loading, { progress: view.lines[view.lines.length - 1] });
    } while (view.state === "running");
    if (view.state !== "done") { note.textContent = view.message; return; }
    res = await mv.api.map_models(pack);
  }
  if (!res || !res.index || ask !== mv.ask || !mv.scenery.data) return;
  note.textContent = fill(w.models_loading, { progress: "" });
  const { THREE } = mv.gl, idx = res.index;
  const buf = await (await fetch(res.base + idx.bin)).arrayBuffer();
  if (ask !== mv.ask) return;
  const loader = new THREE.TextureLoader(), textures = {};
  const textureOf = (key) => {
    if (!key || !idx.textures[key]) return null;
    if (!textures[key]) {
      const t = loader.load(res.base + idx.textures[key], () => mv.gl.draw());
      t.flipY = false;  // the game's UVs start at the picture's top
      t.colorSpace = THREE.SRGBColorSpace;
      textures[key] = t;
    }
    return textures[key];
  };
  const geometries = {};
  const geometryOf = (typeIdx) => {
    if (geometries[typeIdx]) return geometries[typeIdx];
    const parts = (idx.models[typeIdx] || []).map((p) => {
      const n = p.vertices;
      const src = new Float32Array(buf, p.positions, 3 * n), pos = new Float32Array(3 * n);
      for (let i = 0; i < n; i++) {  // map units, x east, y south, z up -> the scene's x east, y up, z south
        pos[3 * i] = src[3 * i]; pos[3 * i + 1] = src[3 * i + 2]; pos[3 * i + 2] = src[3 * i + 1];
      }
      const nsrc = new Int8Array(buf, p.normals, 4 * n), nrm = new Float32Array(3 * n);
      for (let i = 0; i < n; i++) {
        nrm[3 * i] = nsrc[4 * i] / 127; nrm[3 * i + 1] = nsrc[4 * i + 2] / 127; nrm[3 * i + 2] = nsrc[4 * i + 1] / 127;
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      geo.setAttribute("normal", new THREE.BufferAttribute(nrm, 3));
      geo.setAttribute("uv", new THREE.BufferAttribute(new Float32Array(buf, p.uvs, 2 * n).slice(), 2));
      geo.setIndex(new THREE.BufferAttribute(new Uint32Array(buf, p.indices, 3 * p.triangles).slice(), 1));
      return { geo, texture: p.texture };
    });
    return (geometries[typeIdx] = parts);
  };
  clearModels();
  const models = {};
  for (const [group, mesh] of Object.entries(mv.scenery.meshes)) {
    const flat = mesh.userData.flat, byType = new Map();
    for (let k = 0; k < flat.length / 5; k++) {
      const t = flat[5 * k];
      if (idx.models[t] && idx.models[t].length) (byType.get(t) || byType.set(t, []).get(t)).push(k);
    }
    const colour = SCENERY_LOOK[group][3], list = [], rest = [];
    for (let k = 0; k < flat.length / 5; k++) if (!byType.has(flat[5 * k])) rest.push(k);
    for (const [t, rows] of byType) {
      for (const part of geometryOf(t)) {
        const map = textureOf(part.texture);
        const mat = new THREE.MeshLambertMaterial(map ? { map, alphaTest: 0.5, side: THREE.DoubleSide }
                                                      : { color: colour, side: THREE.DoubleSide });
        const inst = new THREE.InstancedMesh(part.geo, mat, rows.length);
        inst.userData = { group, rows, flat, real: true };
        inst.visible = mv.scenery.show[group];
        mv.gl.scene.add(inst);
        list.push(inst);
      }
    }
    if (rest.length) {  // types without a model keep their shape
      const inst = new THREE.InstancedMesh(mesh.geometry.clone(), mesh.material.clone(), rest.length);
      inst.userData = { group, rows: rest, flat };
      inst.visible = mv.scenery.show[group];
      mv.gl.scene.add(inst);
      list.push(inst);
    }
    models[group] = list;
    mesh.material.visible = false;  // the shapes aren't drawn any more: they stay to point at (sceneryAt)
  }
  mv.scenery.models = models;
  placeScenery();
  note.textContent = "";
}

function clearModels() {
  for (const list of Object.values(mv.scenery.models || {})) for (const m of list) forget(m);
  mv.scenery.models = {};
}

// --- what stands on the map: every building, a sample of props and trees (StudioApi.map_scenery) ---
// Simple shapes until the game's models can be read: a building is a box, a prop a small block, a tree a cone, turned
// and sized as the game places them and stood on the ground (the game sets scenery on the ground itself).
const SCENERY_LOOK = {  // group: [shape, width, height (map units at size 1), colour]
  building: ["box", 1100, 900, 0xb4866a],
  prop: ["box", 260, 220, 0x8f8a7c],
  vegetation: ["cone", 420, 1300, 0x3c6a34],
};

function groundAt(g, x, y) {
  const fc = (x - g.x0) / g.sx - 0.5, fr = (y - g.y0) / g.sy - 0.5;
  const c = Math.max(0, Math.min(Math.floor(fc), g.cols - 2)), r = Math.max(0, Math.min(Math.floor(fr), g.rows - 2));
  const tx = Math.min(Math.max(fc - c, 0), 1), ty = Math.min(Math.max(fr - r, 0), 1), z = g.z, k = r * g.cols + c;
  const right = g.cols > 1 ? 1 : 0, down = g.rows > 1 ? g.cols : 0;
  const top = z[k] + (z[k + right] - z[k]) * tx, bottom = z[k + down] + (z[k + down + right] - z[k + down]) * tx;
  return top + (bottom - top) * ty;
}

function sceneryMeshes(data) {
  const { THREE } = mv.gl, out = {};
  for (const [group, [shape, , , colour]] of Object.entries(SCENERY_LOOK)) {
    const flat = (data.items || {})[group] || [], n = flat.length / 5;
    if (!n) continue;
    const geo = shape === "cone" ? new THREE.ConeGeometry(0.5, 1, 6) : new THREE.BoxGeometry(1, 1, 1);
    geo.translate(0, 0.5, 0);  // standing on the ground, not half in it
    const mesh = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: colour }), n);
    mesh.userData = { group, flat };
    mesh.visible = mv.scenery.show[group];
    out[group] = mesh;
  }
  return out;
}

// Stand every shown object on the ground as it is now (after strokes, too).
// A shape mesh holds every shown object of its group (userData.flat); a model mesh or a stand-in holds some of them
// (userData.rows: their numbers in flat). Shapes are scaled to the look's size; models keep their own, times the
// object's size.
function placeScenery() {
  const shapes = Object.values(mv.scenery.meshes);
  if (!shapes.length || !mv.edit) return;
  const models = Object.values(mv.scenery.models || {}).flat();
  const { THREE } = mv.gl, grid = makeGrid(mv.edit);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), p = new THREE.Vector3(), s = new THREE.Vector3();
  const up = new THREE.Vector3(0, 1, 0);
  for (const mesh of shapes.concat(models)) {
    const { group, flat, rows, real } = mesh.userData, [, width, height] = SCENERY_LOOK[group];
    const n = rows ? rows.length : flat.length / 5;
    for (let j = 0; j < n; j++) {
      const k = rows ? rows[j] : j;
      const x = flat[5 * k + 1], y = flat[5 * k + 2], size = Math.max(0.3, Math.min(flat[5 * k + 4], 4));
      p.set(x * SCALE, groundAt(grid, x, y) * SCALE, y * SCALE);
      q.setFromAxisAngle(up, -flat[5 * k + 3]);  // the game turns from east toward south; the scene's Y turns the other way
      if (real) s.set(size * SCALE, size * SCALE, size * SCALE);
      else s.set(width * size * SCALE, height * size * SCALE, width * size * SCALE);
      mesh.setMatrixAt(j, m.compose(p, q, s));
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
  }
  drawPlaced();
}

function clearScenery() {
  clearModels();
  for (const mesh of Object.values(mv.scenery.meshes)) forget(mesh);
  mv.scenery.meshes = {};
  mv.scenery.data = null;
  $("scenery-stats").textContent = "";
  $("scenery-hover").textContent = "";
}

function showSceneryStats() {
  const d = mv.scenery.data, w = mv.words;
  if (!d) return;
  const g = d.groups, n = (k, f) => ((g[k] || {})[f] || 0).toLocaleString();
  $("scenery-stats").textContent = fill(w.scenery_stats, { buildings: n("building", "shown"), props: n("prop", "shown"),
    props_total: n("prop", "total"), trees: n("vegetation", "shown"), trees_total: n("vegetation", "total") });
}

async function loadScenery(pack, ask) {
  clearScenery();
  $("scenery-stats").textContent = mv.words.scenery_loading;
  const data = await mv.api.map_scenery(pack);
  if (ask !== mv.ask || !mv.edit) return;
  mv.scenery.data = data;
  mv.scenery.meshes = sceneryMeshes(data);
  for (const mesh of Object.values(mv.scenery.meshes)) mv.gl.scene.add(mesh);
  placeScenery();
  showSceneryStats();
  placeOptions();
  if (mv.place.on && mv.place.mod) placeNote(mv.place.type ? "" : whyNoType(), "error");  // was "reading the map…"
  drawPlaced();
}

// Pointing at an object says what it is: its name and the game editor's category.
function sceneryAt(ev) {
  const gl = mv.gl, d = mv.scenery.data;
  if (!d) return null;
  const rect = gl.renderer.domElement.getBoundingClientRect();
  gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  gl.raycaster.setFromCamera(gl.ndc, gl.camera);
  const shown = Object.values(mv.scenery.meshes).filter((m) => m.visible);
  const hit = shown.length ? gl.raycaster.intersectObjects(shown, false)[0] : null;
  if (!hit || hit.instanceId === undefined) return null;
  return d.types[hit.object.userData.flat[5 * hit.instanceId]] || null;
}

// --- placing objects: the map's own types, clicked onto the ground, saved in the current mod's
// maps/<map>/scenery.toml (StudioApi.scenery_add); drawn in gold until "Test in game" builds them into the map ---
const PLACEABLE = ["building", "prop", "vegetation"];
const PLACED_COLOUR = 0xe8c14f;
// How a click places: one object; an area, painted by dragging (objects scattered at least `spacing` apart); or a line
// between two clicks (objects every `spacing`, turned along it: a hedgerow, a tree line, a row of houses).
const PLACE_HOW = ["one", "area", "line"];
const METRE = 260;  // world units in a metre (the game's distances: 260,000 to a kilometre)
const SPACING = { building: 20, prop: 8, vegetation: 6 };  // metres between objects to start with, per kind
const MOST = 800;  // objects one area or line may place at most, so a slip of the mouse can't bury a map
const around = (turn, spread) => (turn + Math.round((Math.random() * 2 - 1) * spread) + 360) % 360;

function placeNote(text, kind) {
  const note = $("place-note");
  note.textContent = text || "";
  note.className = kind === "error" ? "small error-text" : "small";
}

// The list only holds the map's own types: the game can't take a type a map doesn't already use (StudioApi.scenery_add
// refuses it), so the search and the tooltip say so rather than offering every type in the game.
function placeOptions() {
  const d = mv.scenery.data, p = mv.place, q = $("place-search").value.trim().toLowerCase();
  const rows = ((d && d.palette) || []).filter((r) => r[2] === p.group
    && (!q || r[1].toLowerCase().includes(q) || r[3].toLowerCase().includes(q)));
  if (!rows.some((r) => r[0] === p.type)) p.type = rows.length ? rows[0][0] : null;
  $("place-type").replaceChildren(...rows.map((r) => {
    const o = el("option", { value: r[0], textContent: r[4] ? `${r[1]}  (${r[4].toLocaleString()})` : r[1], title: r[3] });
    o.selected = r[0] === p.type;
    return o;
  }));
}

function renderPlace() {
  const w = mv.words, p = mv.place;
  $("place-title").textContent = w.place_title;
  $("place-groups").replaceChildren(...PLACEABLE.map((g) => {
    const chip = el("button", { type: "button", className: "chip", textContent: w[`scenery_${g}`], title: w.tip_place_group });
    chip.setAttribute("aria-pressed", String(p.group === g));
    // picking a kind starts placing, as picking a brush starts painting: a click on the ground then does something
    chip.addEventListener("click", () => { p.group = g; placeOptions(); if (!p.on) setPlaceMode(true); else renderPlace(); });
    return chip;
  }));
  $("place-scenery-note").textContent = w.scenery_note;  // DomesticNukes' note: scenery is only for looks, for now
  $("place-search").placeholder = w.search || "";
  $("place-search").title = w.tip_place_search;
  $("place-type").title = w.tip_place_type;
  $("place-turn-label").textContent = `${w.place_turn} ${p.turn}°`;
  $("place-turn").title = w.tip_place_turn;
  $("place-size-label").textContent = `${w.brush_size} ${p.size.toFixed(1)}×`;
  $("place-size").title = w.tip_place_size;
  $("place-on").textContent = w.place_on;
  $("place-on").title = w.tip_place_on;
  $("place-on").setAttribute("aria-pressed", String(p.on));
  $("place-undo").textContent = w.brush_undo;
  $("place-undo").title = w.tip_place_undo;
  $("place-undo").disabled = !p.objects.length;
  $("place-count").textContent = p.objects.length ? fill(w.place_count, { n: p.objects.length.toLocaleString() }) : "";
  $("place-how").replaceChildren(...PLACE_HOW.map((how) => {
    const chip = el("button", { type: "button", className: "chip", textContent: w[`place_${how}`], title: w[`tip_place_${how}`] });
    chip.setAttribute("aria-pressed", String(p.how === how));
    chip.addEventListener("click", () => { p.how = how; p.lineStart = null; showPlaceGuide(null); if (!p.on) setPlaceMode(true); else renderPlace(); });
    return chip;
  }));
  $("place-spacing-row").classList.toggle("hidden", p.how === "one");
  $("place-area-row").classList.toggle("hidden", p.how !== "area");
  $("place-spacing").value = spacingOf(p.group);
  $("place-spacing-label").textContent = fill(w.place_spacing, { m: spacingOf(p.group) });
  $("place-spacing").title = w.tip_place_spacing;
  $("place-area").value = p.area;
  $("place-area-label").textContent = fill(w.place_area_size, { m: p.area });
  $("place-area").title = w.tip_place_area_size;
  if (p.on) $("map-help").textContent = p.how === "area" ? w.place_area_help : p.how === "line" ? w.place_line_help : w.place_help;
}

function spacingOf(group) {
  return mv.place.spacing[group] ?? SPACING[group] ?? 10;
}

function setPlaceMode(on) {
  mv.place.on = on;
  if (!on) { mv.place.lineStart = null; showPlaceGuide(null); }
  if (on && mv.brush.on) setBrushMode(false);
  pointerMode();
  if (on) placeNote(!mv.place.mod ? mv.words.no_mod : !mv.place.type ? whyNoType() : "", "error");
  if (!on) $("map-help").textContent = mv.brush.on ? mv.words.brush_help : mv.words.map_help;
  renderPlace();
}

// Nothing to place yet: the map's types are still being read (a second or two on a real map), or the kind picked has
// none, or the search left none.
function whyNoType() {
  return mv.scenery.data ? mv.words.place_pick : mv.words.scenery_loading;
}

// The objects this mod places, in gold, on the ground as it is now.
function drawPlaced() {
  const gl = mv.gl, p = mv.place;
  if (!gl) return;
  for (const m of Object.values(p.meshes)) forget(m);
  p.meshes = {};
  if (mv.edit && p.objects.length) {
    const groupOf = new Map(((mv.scenery.data && mv.scenery.data.palette) || []).map((r) => [r[0], r[2]]));
    const lists = {};
    for (const o of p.objects) (lists[groupOf.get(o.type) || "building"] ||= []).push(o);
    const { THREE } = gl, grid = makeGrid(mv.edit), m = new THREE.Matrix4(), q = new THREE.Quaternion();
    const at = new THREE.Vector3(), s = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
    for (const [group, list] of Object.entries(lists)) {
      const [shape, width, height] = SCENERY_LOOK[group];
      const geo = shape === "cone" ? new THREE.ConeGeometry(0.5, 1, 6) : new THREE.BoxGeometry(1, 1, 1);
      geo.translate(0, 0.5, 0);
      const mesh = new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: PLACED_COLOUR }), list.length);
      list.forEach((o, k) => {
        at.set(o.x * SCALE, groundAt(grid, o.x, o.y) * SCALE, o.y * SCALE);
        q.setFromAxisAngle(up, -o.turn * Math.PI / 180);
        s.set(width * o.size * SCALE, height * o.size * SCALE, width * o.size * SCALE);
        mesh.setMatrixAt(k, m.compose(at, q, s));
      });
      mesh.instanceMatrix.needsUpdate = true;
      mesh.computeBoundingSphere();
      gl.scene.add(mesh);
      p.meshes[group] = mesh;
    }
  }
  gl.draw();
}

async function loadPlaced(pack, ask) {
  const res = await mv.api.scenery(pack);
  if (ask !== mv.ask) return;
  mv.place.objects = res.objects;
  mv.place.groups = [];
  mv.place.lineStart = null;
  mv.place.mod = res.mod;
  placeNote("");
  drawPlaced();
  renderPlace();
}

// A click that places nothing always says why: no mod, nothing picked, or the click missed the ground (the sky, or
// the map's edge seen from the side).
async function placeAt(ev) {
  const p = mv.place, pack = mv.current, w = mv.words;
  if (!p.mod) { placeNote(w.no_mod, "error"); return; }
  if (!p.type) { placeNote(whyNoType(), "error"); return; }
  const hit = hitGround(ev);
  if (!hit) { placeNote(w.place_ground, "error"); return; }
  const obj = { type: p.type, x: Math.round(hit.x / SCALE), y: Math.round(hit.z / SCALE), turn: p.turn, size: p.size };
  p.objects.push(obj);
  drawPlaced();
  try {
    await mv.api.scenery_add(pack, [obj]);
    if (pack !== mv.current) return;
    placeNote(w.brush_note);
  } catch (err) {
    if (pack !== mv.current) return;
    p.objects.splice(p.objects.indexOf(obj), 1);
    drawPlaced();
    placeNote((err && err.message) || String(err), "error");
  }
  renderPlace();
}

// Several objects in one go (an area or a line): drawn at once, saved in one call, taken back together by Undo.
async function placeMany(objs) {
  const p = mv.place, pack = mv.current, w = mv.words;
  if (!objs.length) { placeNote(w.place_none_room, "error"); return; }
  p.objects.push(...objs);
  drawPlaced();
  try {
    await mv.api.scenery_add(pack, objs);
    if (pack !== mv.current) return;
    p.groups.push(objs.length);
    placeNote(fill(w.place_placed, { n: objs.length.toLocaleString() }) + (objs.length >= MOST ? " " + w.place_most : ""));
  } catch (err) {
    if (pack !== mv.current) return;
    p.objects.splice(p.objects.length - objs.length, objs.length);
    drawPlaced();
    placeNote((err && err.message) || String(err), "error");
  }
  renderPlace();
}

// The next object of an area or a line at world (x, y): the kind's own look, with a little variety for trees and props
// (their turn, and a tree's size) so a painted wood doesn't look stamped; buildings keep the turn they're given.
function objectAt(x, y, turn) {
  const p = mv.place, varied = p.group !== "building";
  const size = p.group === "vegetation" ? Math.round(p.size * (0.85 + Math.random() * 0.3) * 100) / 100 : p.size;
  return { type: p.type, x: Math.round(x), y: Math.round(y), turn: varied ? Math.floor(Math.random() * 360) : turn, size };
}

// Painting an area: each spot the pointer passes scatters objects in the circle, never closer than the spacing to
// another one (this stroke's, or any the mod placed before), so going over a spot twice doesn't pile them up.
function scatter(stroke, x, y) {
  const p = mv.place, gap = spacingOf(p.group) * METRE, r = p.area * METRE, cell = gap;
  const key = (a, b) => `${Math.floor(a / cell)},${Math.floor(b / cell)}`;
  if (!stroke.grid) {
    stroke.grid = new Map();
    for (const o of p.objects) (stroke.grid.get(key(o.x, o.y)) || stroke.grid.set(key(o.x, o.y), []).get(key(o.x, o.y))).push(o);
  }
  const free = (a, b) => {
    const cx = Math.floor(a / cell), cy = Math.floor(b / cell);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
      for (const o of stroke.grid.get(`${cx + i},${cy + j}`) || []) if (Math.hypot(o.x - a, o.y - b) < gap) return false;
    }
    return true;
  };
  const tries = Math.ceil(Math.PI * r * r / (gap * gap)) * 3;
  const [x0, y0, , x1, y1] = mv.edit.bounds;
  for (let t = 0; t < tries && stroke.objects.length < MOST; t++) {
    const a = Math.random() * 2 * Math.PI, d = r * Math.sqrt(Math.random());
    const ox = x + d * Math.cos(a), oy = y + d * Math.sin(a);
    if (ox < x0 || ox > x1 || oy < y0 || oy > y1 || !free(ox, oy)) continue;
    const o = objectAt(ox, oy, around(p.turn, 45));
    stroke.objects.push(o);
    (stroke.grid.get(key(o.x, o.y)) || stroke.grid.set(key(o.x, o.y), []).get(key(o.x, o.y))).push(o);
  }
  stroke.last = [x, y];
}

// A line between two clicks: an object every `spacing`, both ends included, turned along the line (buildings then
// face the same way, like houses along a street; the turn slider adds to that).
function lineOf(a, b) {
  const p = mv.place, gap = spacingOf(p.group) * METRE, len = Math.hypot(b.x - a.x, b.y - a.y);
  const n = Math.min(MOST, Math.max(1, Math.floor(len / gap) + 1));
  const heading = (Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI + 360) % 360;
  const out = [];
  for (let k = 0; k < n; k++) {
    const t = n === 1 ? 0 : k / (n - 1);
    out.push(objectAt(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, Math.round(heading + p.turn) % 360));
  }
  return out;
}

// What the area brush covers, or where a line would go, drawn with the terrain brush's own ring and guide.
function showPlaceGuide(pt) {
  const gl = mv.gl, p = mv.place;
  if (!gl || !gl.ring) return;
  const r = p.area * METRE * SCALE;
  gl.ring.visible = Boolean(pt && p.on && p.how === "area");
  if (gl.ring.visible) { gl.ring.position.set(pt.x, pt.y + r * 0.02, pt.z); gl.ring.scale.set(r, r, r); }
  const start = p.on && p.how === "line" ? p.lineStart : null, mark = spacingOf(p.group) * METRE * SCALE;
  gl.startRing.visible = Boolean(start);
  if (start) { gl.startRing.position.set(start.sx, start.sy + mark * 0.1, start.sz); gl.startRing.scale.set(mark, mark, mark); }
  gl.guide.visible = Boolean(start && pt);
  if (start && pt) {
    const pos = gl.guide.geometry.attributes.position;
    pos.setXYZ(0, start.sx, start.sy + mark * 0.1, start.sz);
    pos.setXYZ(1, pt.x, pt.y + mark * 0.1, pt.z);
    pos.needsUpdate = true;
    gl.guide.geometry.computeBoundingSphere();
  }
  gl.draw();
}

async function undoPlace() {
  const p = mv.place, pack = mv.current;
  if (!p.mod || !p.objects.length || p.painting) return;
  const n = p.groups.length ? p.groups.pop() : 1;  // an area or a line goes back in one go
  try {
    const res = await mv.api.scenery_undo(pack, n);
    if (pack !== mv.current) return;
    p.objects.splice(p.objects.length - res.removed, res.removed);
    drawPlaced();
    renderPlace();
  } catch (err) { placeNote((err && err.message) || String(err), "error"); }
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
  mv.size = made.size;
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
  showTitle();
  mv.stats = { points: view.vertices.toLocaleString(), triangles: view.triangle_count.toLocaleString() };
  $("map-stats").textContent = fill(w.map_stats, mv.stats);
  $("map-pick").classList.add("hidden");
  $("map-hud").classList.remove("hidden");
  $("map-tools").classList.remove("hidden");
  loadStrokes(pack, ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
  loadScenery(pack, ask).then(() => loadModels(pack, ask).catch((err) => {  // the shapes stay when models can't be had
    $("map-ground").textContent = (err && err.message) || String(err);
  })).catch((err) => {  // no types to place then: the place panel says so too
    $("scenery-stats").textContent = (err && err.message) || String(err);
    placeNote((err && err.message) || String(err), "error");
  });
  loadPlaced(pack, ask).catch((err) => placeNote((err && err.message) || String(err), "error"));
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
  $("brush-list").replaceChildren(...Object.keys(BRUSHES).map((name, i) => {
    const chip = el("button", { type: "button", className: "chip", textContent: w["brush_" + name] || name,
      title: (w["tip_brush_" + name] ? w["tip_brush_" + name] + " " : "") + fill(w.tip_brush || "", { n: i + 1 }) });
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
  mv.brush.on = on;
  if (on) mv.place.on = false;
  if (!on) cancelRamp();
  pointerMode();
  renderBrushes();
  renderPlace();
}

// Brushing or placing: the left button works on the ground (the middle one turns the view); else it turns the view.
function pointerMode() {
  const gl = mv.gl;
  if (!gl) return;
  const busy = mv.brush.on || mv.place.on, M = gl.THREE.MOUSE;
  gl.controls.mouseButtons = busy ? { LEFT: null, MIDDLE: M.ROTATE, RIGHT: M.PAN }
                                  : { LEFT: M.ROTATE, MIDDLE: M.DOLLY, RIGHT: M.PAN };
  if (!mv.brush.on && gl.ring) { gl.ring.visible = false; gl.draw(); }
  if (busy) $("scenery-hover").textContent = "";
  gl.renderer.domElement.style.cursor = busy ? "crosshair" : "";
}

// The world numbers of a new stroke, from the brush picked and its sliders.
function newStroke(x, y, level, end) {
  const name = mv.brush.name, [kind] = BRUSHES[name], set = settingsOf(name);
  const [x0, , z0, x1, , z1] = mv.edit.bounds;
  const s = { brush: name, x, y, radius: set.size / 100 * (x1 - x0) };
  if (kind === "add") s.height = lift(set.strength, z0, z1);
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
  placeScenery();
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
  // A click on the map takes the focus off the type list or a slider, so the keys reach the map from then on.
  canvas.tabIndex = -1;
  canvas.addEventListener("pointerdown", () => canvas.focus({ preventScroll: true }));
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
    const level = kind !== "level" ? 0 : name === "plateau" ? z + lift(set.strength, z0, z1) : z;
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
  canvas.addEventListener("pointerdown", (ev) => {
    const p = mv.place;
    if (!p.on || ev.button !== 0 || !gl.ground || !mv.edit) return;
    ev.preventDefault();
    if (p.how === "one") { placeAt(ev); return; }
    const w = mv.words;
    if (!p.mod) { placeNote(w.no_mod, "error"); return; }
    if (!p.type) { placeNote(whyNoType(), "error"); return; }
    const hit = hitGround(ev);
    if (!hit) { placeNote(w.place_ground, "error"); return; }
    const x = hit.x / SCALE, y = hit.z / SCALE;
    if (p.how === "line") {  // two clicks: where it starts, then where it ends
      if (!p.lineStart) { p.lineStart = { x, y, sx: hit.x, sy: hit.y, sz: hit.z }; placeNote(w.place_line_next); showPlaceGuide(hit); return; }
      const start = p.lineStart;
      p.lineStart = null;
      showPlaceGuide(null);
      placeMany(lineOf(start, { x, y }));
      return;
    }
    p.painting = { objects: [], last: null };  // an area: scatter here, then wherever the pointer is dragged
    scatter(p.painting, x, y);
    drawStroke();
    canvas.setPointerCapture(ev.pointerId);
  });
  // an area being painted: shown as it grows, saved when the button comes up
  const drawStroke = () => {
    const p = mv.place, keep = p.objects;
    p.objects = keep.concat(p.painting.objects);
    drawPlaced();
    p.objects = keep;
  };
  let placeMove = null, placeFrame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    const p = mv.place;
    if (!p.on || p.how === "one") return;
    placeMove = ev;
    if (placeFrame) return;
    placeFrame = requestAnimationFrame(() => {
      placeFrame = 0;
      const hit = placeMove && hitGround(placeMove);
      showPlaceGuide(hit);
      const stroke = p.painting;
      if (!hit || !stroke || !stroke.last) return;
      const x = hit.x / SCALE, y = hit.z / SCALE, step = p.area * METRE / 2;
      if (Math.hypot(x - stroke.last[0], y - stroke.last[1]) < step) return;
      scatter(stroke, x, y);
      drawStroke();
    });
  });
  for (const type of ["pointerup", "pointercancel"]) {
    canvas.addEventListener(type, () => {
      const p = mv.place, stroke = p.painting;
      if (!stroke) return;
      p.painting = null;
      placeMany(stroke.objects);
    });
  }
  let hoverEv = null, hoverFrame = 0;
  // Looking around: say what the pointer is on. Only then: the ray is tested against every drawn object (tens of
  // thousands on a real map), which is too slow to run under a painting or placing pointer.
  canvas.addEventListener("pointermove", (ev) => {
    if (mv.brush.on || mv.place.on || !mv.scenery.data) return;
    hoverEv = ev;
    if (!hoverFrame) hoverFrame = requestAnimationFrame(() => {
      hoverFrame = 0;
      const t = sceneryAt(hoverEv);
      $("scenery-hover").textContent = t ? `${t[0]} · ${t[2] || t[1]}` : "";
    });
  });
  canvas.addEventListener("pointerleave", () => {
    if (mv.brush.on && gl.ring) { gl.ring.visible = false; gl.draw(); }
    if (mv.place.on && mv.place.how === "area" && gl.ring) { gl.ring.visible = false; gl.draw(); }
  });
}

// What the game's menus call a map in the Studio's language, best first (a map can hold a multiplayer map, campaign
// chapters and challenges); none in "Code names", which shows the maps' own names (rusemod/terrain.py map_list).
function menuNames(m) {
  if (mv.lang === "base") return [];
  const t = m.titles || {};
  return t[mv.lang] || t.us || [];
}

// "Strongholds · Swamps": the name players know, then the map's own name, the one its files and folders go by
function nameLine(m) {
  const names = menuNames(m);
  return names.length ? [names[0], el("span", { className: "map-code", textContent: ` · ${m.pack}` })] : [m.pack];
}

function renderList() {
  $("map-list").replaceChildren(...mv.maps.map((m) => {
    const names = menuNames(m);
    const b = el("button", { type: "button", title: fill(mv.words.tip_open_map || "{file}", { file: m.file }) },
      el("span", { className: "name" }, ...nameLine(m)),
      el("span", { className: "sub", textContent: (names.length ? names.slice(1) : m.names).join(" · ") }));
    b.setAttribute("aria-current", String(m.pack === mv.current));
    b.addEventListener("click", () => show(m.pack));
    return el("li", null, b);
  }));
}

function showTitle() {
  const m = mv.maps.find((x) => x.pack === mv.current);
  if (mv.current) $("map-title").replaceChildren(...(m ? nameLine(m) : [mv.current]));
}

function renderWords() {
  const w = mv.words;
  $("map-detail").textContent = mv.lod === "highdef" ? w.detail_high : w.detail_low;
  $("map-detail").title = w.tip_detail;
  $("map-water-label").textContent = w.water;
  $("map-water").title = w.tip_water;
  for (const g of ["building", "prop", "vegetation"]) {
    $(`scenery-${g}-label`).textContent = w[`scenery_${g}`];
    $(`scenery-${g}`).title = w.tip_show_group;
  }
  showSceneryStats();
  renderPlace();
  $("map-help").textContent = mv.brush.on ? w.brush_help : w.map_help;
  $("map-keys").textContent = w.map_keys;
  $("brush-title").textContent = w.shape_ground;
  $("brush-size-label").textContent = w.brush_size;
  $("brush-size").title = w.tip_brush_size;
  $("brush-strength-label").textContent = w.brush_strength;
  $("brush-strength").title = w.tip_brush_strength;
  $("brush-look").textContent = w.brush_look;
  $("brush-look").title = w.tip_look;
  $("brush-undo").textContent = w.brush_undo;
  $("brush-undo").title = w.tip_brush_undo;
  $("brush-clear").textContent = w.brush_clear;
  $("brush-clear").title = w.tip_brush_clear;
  $("brush-clear-yes").textContent = w.remove_all;
  $("brush-clear-yes").title = w.tip_remove_all;
  $("brush-clear-no").textContent = w.cancel;
  $("brush-clear-no").title = w.tip_cancel;
  if (!mv.current) $("map-pick").textContent = w.pick_map;
  renderBrushes();
}

// --- keys, while the map view is open and no text box has the focus ---
// W/S and A/D (or the arrows) slide the camera forward, back, left and right as it looks (turned with Q/E, W still
// goes up the screen); Q/E turn it around the point it looks at; R/F zoom. Held keys move smoothly, frame by frame, at a speed
// scaled to the map (and to the zoom, so a close view doesn't fly), three times as fast with Shift. The tool keys
// do what the buttons do (the tooltips name them).
const MOVE = { KeyW: [0, -1], ArrowUp: [0, -1], KeyS: [0, 1], ArrowDown: [0, 1], KeyA: [-1, 0], ArrowLeft: [-1, 0],
  KeyD: [1, 0], ArrowRight: [1, 0] };  // physical keys (e.code): the same places on an AZERTY keyboard
const HELD = new Set([...Object.keys(MOVE), "KeyQ", "KeyE", "KeyR", "KeyF"]);
const keys = { down: new Set(), shift: false, frame: 0, at: 0 };

function mapViewOpen() {
  return Boolean(mv.gl && mv.gl.ground && mv.edit) && !$("maps-view").classList.contains("hidden");
}

// Where the keys would go instead: a text box, a list or a text area take letters; `any` also counts sliders and
// check boxes, whose arrow keys are their own.
function fieldFocused(any) {
  const a = document.activeElement;
  if (!a || a === document.body) return false;
  const tag = a.tagName;
  if (tag === "TEXTAREA" || tag === "SELECT" || a.isContentEditable) return true;
  if (tag !== "INPUT") return false;
  return any || !["range", "checkbox", "radio", "button"].includes(a.type);
}

function moveStep(now) {
  keys.frame = 0;
  const gl = mv.gl, dt = Math.min(0.1, (now - keys.at) / 1000);
  keys.at = now;
  if (!keys.down.size || !mapViewOpen()) { keys.down.clear(); return; }
  const { THREE, camera, controls } = gl, fast = keys.shift ? 3 : 1;
  const offset = camera.position.clone().sub(controls.target), dist = offset.length();
  let dx = 0, dz = 0;
  for (const code of keys.down) { const m = MOVE[code]; if (m) { dx += m[0]; dz += m[1]; } }
  if (dx || dz) {
    const speed = Math.min(mv.size * 0.5, dist) * fast * dt / Math.hypot(dx, dz);
    // forward: where the camera looks, flat on the map (looking straight down: the top of the screen)
    const ahead = controls.target.clone().sub(camera.position).setY(0);
    if (ahead.lengthSq() < 1e-9 * dist * dist) ahead.set(0, 1, 0).applyQuaternion(camera.quaternion).setY(0);
    ahead.normalize();
    const right = new THREE.Vector3(-ahead.z, 0, ahead.x);
    controls.target.addScaledVector(right, dx * speed).addScaledVector(ahead, -dz * speed);
  }
  const turn = (keys.down.has("KeyQ") ? 1 : 0) - (keys.down.has("KeyE") ? 1 : 0);
  if (turn) offset.applyAxisAngle(new THREE.Vector3(0, 1, 0), turn * 1.2 * fast * dt);
  const zoom = (keys.down.has("KeyF") ? 1 : 0) - (keys.down.has("KeyR") ? 1 : 0);
  if (zoom) offset.setLength(Math.min(mv.size * 3, Math.max(mv.size * 0.01, dist * Math.pow(2, zoom * fast * dt))));
  camera.position.copy(controls.target).add(offset);
  controls.update();  // keeps the camera's own limits (never under the ground) and redraws
  gl.draw();
  keys.frame = requestAnimationFrame(moveStep);
}

// [ ] and - = : the brush's size and strength, or the next object's size and turn while placing.
function nudge(what, dir) {
  if (mv.place.on) {
    const p = mv.place;
    if (what === "size") p.size = Math.round(Math.min(3, Math.max(0.5, p.size + dir * 0.1)) * 10) / 10;
    else p.turn = (p.turn + dir * 15 + 360) % 360;
    $("place-size").value = p.size;
    $("place-turn").value = p.turn;
    renderPlace();
    return;
  }
  const set = settingsOf(mv.brush.name);
  if (what === "size") set.size = Math.min(15, Math.max(1, set.size + dir));
  else set.strength = Math.min(100, Math.max(1, set.strength + dir * 5));
  renderBrushes();
}

function lookAround() {
  cancelRamp();
  mv.place.lineStart = null;
  showPlaceGuide(null);
  mv.place.on = false;
  setBrushMode(false);
}

function onKey(e) {
  if (!mapViewOpen()) return;
  keys.shift = e.shiftKey;
  const held = HELD.has(e.code);
  if (e.type === "keyup") { if (held) keys.down.delete(e.code); return; }
  const ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && !e.altKey && e.code === "KeyZ") {  // the one shortcut that works with a modifier
    if (fieldFocused(false)) return;              // a text box has its own undo
    e.preventDefault();
    if (mv.brush.on) undoStroke(); else if (mv.place.on) undoPlace();
    return;
  }
  if (ctrl || e.altKey) return;
  if (e.key === "Escape") {
    if (fieldFocused(true)) { document.activeElement.blur(); return; }  // first out of the box, then back to Look
    lookAround();
    return;
  }
  if (held) {
    if (fieldFocused(!e.code.startsWith("Key"))) return;  // arrows in a slider are the slider's; letters in a box, the box's
    e.preventDefault();  // the arrows would scroll the page
    keys.down.add(e.code);
    if (!keys.frame) { keys.at = performance.now(); keys.frame = requestAnimationFrame(moveStep); }
    return;
  }
  if (fieldFocused(false)) return;
  const digit = /^Digit([1-9])$/.exec(e.code);
  if (digit) { pickBrush(Object.keys(BRUSHES)[Number(digit[1]) - 1]); return; }
  if (e.code === "KeyB") { if (mv.brush.on) lookAround(); else pickBrush(mv.brush.name); }
  else if (e.code === "KeyP") setPlaceMode(!mv.place.on);
  else if (e.code === "BracketLeft") nudge("size", -1);
  else if (e.code === "BracketRight") nudge("size", 1);
  else if (e.code === "Minus") nudge("strength", -1);
  else if (e.code === "Equal") nudge("strength", 1);
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
  for (const g of ["building", "prop", "vegetation"]) {
    $(`scenery-${g}`).addEventListener("change", (e) => {
      mv.scenery.show[g] = e.target.checked;
      const mesh = mv.scenery.meshes[g];
      if (mesh) mesh.visible = e.target.checked;
      for (const m of (mv.scenery.models || {})[g] || []) m.visible = e.target.checked;
      if (mv.gl) mv.gl.draw();
    });
  }
  $("brush-size").addEventListener("input", (e) => { settingsOf(mv.brush.name).size = Number(e.target.value); });
  $("brush-strength").addEventListener("input", (e) => { settingsOf(mv.brush.name).strength = Number(e.target.value); });
  $("brush-look").addEventListener("click", () => { mv.place.on = false; setBrushMode(false); });
  $("place-on").addEventListener("click", () => setPlaceMode(!mv.place.on));
  $("place-undo").addEventListener("click", () => undoPlace());
  $("place-search").addEventListener("input", () => { placeOptions(); if (mv.place.on) placeNote(mv.place.type ? "" : whyNoType(), "error"); });
  $("place-type").addEventListener("change", (e) => {  // picking a type starts placing, as picking a brush starts painting
    mv.place.type = e.target.value;
    if (!mv.place.on) setPlaceMode(true); else placeNote("");
  });
  $("place-turn").addEventListener("input", (e) => { mv.place.turn = Number(e.target.value); renderPlace(); });
  $("place-size").addEventListener("input", (e) => { mv.place.size = Number(e.target.value); renderPlace(); });
  $("place-spacing").addEventListener("input", (e) => { mv.place.spacing[mv.place.group] = Number(e.target.value); renderPlace(); });
  $("place-area").addEventListener("input", (e) => { mv.place.area = Number(e.target.value); renderPlace(); });
  $("brush-undo").addEventListener("click", () => undoStroke());
  $("brush-clear").addEventListener("click", () => {
    $("brush-sure-text").textContent = fill(mv.words.really_clear, { n: mv.brush.strokes.length.toLocaleString() });
    $("brush-sure").classList.remove("hidden");
    $("brush-clear-yes").focus();
  });
  $("brush-clear-no").addEventListener("click", () => $("brush-sure").classList.add("hidden"));
  $("brush-clear-yes").addEventListener("click", () => clearStrokes());
  window.addEventListener("keydown", onKey);
  window.addEventListener("keyup", onKey);
  window.addEventListener("blur", () => keys.down.clear());  // a key released in another window never arrives
}

// app.js opens the view when its tab is picked, and passes the words and the language on every language change.
window.MapView = {
  async open(api, words, lang) {
    mv.api = api;
    mv.words = words;
    mv.lang = lang || "base";
    wire();
    renderWords();
    if (!mv.maps.length) {
      try {
        mv.maps = (await api.maps()).maps;
      } catch (err) {
        $("map-pick").textContent = (err && err.message) || String(err);
        return;
      }
    }
    renderList();  // the language may have changed while the view was closed
    showTitle();
  },
  setWords(words, lang) {
    mv.words = words;
    mv.lang = lang || "base";
    renderWords();
    renderList();
    showTitle();
    if (mv.stats) $("map-stats").textContent = fill(words.map_stats, mv.stats);
  },
  // where the camera is and what it looks at, in scene units (for checking the keys from outside; nothing else)
  camera() {
    const gl = mv.gl;
    if (!gl) return null;
    return { position: gl.camera.position.toArray(), target: gl.controls.target.toArray(), placed: mv.place.objects.length };
  },
  // another mod was picked: its strokes on this map (or none) replace the ones drawn
  modChanged() {
    if (mv.current && mv.edit) loadStrokes(mv.current, mv.ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
    if (mv.current && mv.edit) loadPlaced(mv.current, mv.ask).catch((err) => placeNote((err && err.message) || String(err), "error"));
  },
};
window.dispatchEvent(new Event("mapview-ready"));
