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
  // the size of each group of strokes made this session (for Undo; a Forest stroke's: { n, objects: its trees }), the
  // drag being painted, and the mod saved into
  brush: { on: false, name: "hill", settings: {}, strokes: [], groups: [], painting: null, mod: null, rampStart: null },
  // scenery: which groups are shown, the map's scenery (StudioApi.map_scenery) and its drawn shapes per group
  scenery: { show: { building: true, prop: true, vegetation: true }, data: null, meshes: {}, models: {} },
  // placing: on or not, the group and type picked, the next object's turn and size, what the mod places on this map
  place: { on: false, group: "building", type: null, turn: 0, size: 1, solid: true, objects: [], meshes: {}, mod: null,
    // how: one, area or line; area: the area brush's radius and spacing: per kind, in metres; groups: the objects each
    // click, area or line placed this session (for Undo); lineStart: a line's first click; painting: an area being dragged
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
  water: ["water", "flat", 1, false, 4, 5],  // the water surface, not the ground: a lake up to a level (rusemod.water)
  drain: ["drain", "flat", 1, false, 4, 0],  // the map's base water level again
  cover: ["cover", "flat", 1, false, 3, 0],  // where units hide (the map's cover grid, not the ground: rusemod.cover)
  uncover: ["cover", "flat", -1, false, 3, 0],
  town: ["town", "flat", 1, true, 3, 0],  // one click: cover around every building of the town clicked
  block: ["block", "all", 1, false, 3, 0],  // ground units can't use (the map's navigation graphs: rusemod.nav)
  block_infantry: ["block", "infantry", 1, false, 3, 0],
  block_vehicles: ["block", "vehicles", 1, false, 3, 0],
  open: ["open", "all", 1, false, 3, 0],  // ground units can use where the map has none (the reverse of block)
  open_infantry: ["open", "infantry", 1, false, 3, 0],
  open_vehicles: ["open", "vehicles", 1, false, 3, 0],
  forest: ["forest", "flat", 1, false, 3, 0],  // trees (as Place, Area scatters them) and cover over them: cover strokes
};
const WATER = new Set(["water", "drain"]);
const SIZE_UNIT = { cover: 0.25, uncover: 0.25, town: 0.1, block: 0.25, block_infantry: 0.25, block_vehicles: 0.25,
  open: 0.25, open_infantry: 0.25, open_vehicles: 0.25, forest: 0.25 };  // finer sizes than the ground brushes' (share of 1%)

// A brush's radius in map units: its Size slider as a share of the map's width.
function brushRadius(name) {
  const [x0, , , x1] = mv.edit.bounds;
  return settingsOf(name).size / 100 * (x1 - x0) * (SIZE_UNIT[name] || 1);
}
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
  // the water surface too: each point's level (most carry the map's base level: the sea), for the water brushes
  const w = new Float64Array(n), counts = new Map();
  for (let i = 0; i < n; i++) { w[i] = z0 + wq[i] * sz; counts.set(wq[i], (counts.get(wq[i]) || 0) + 1); }
  const baseWater = z0 + [...counts].reduce((a, b) => (b[1] > a[1] ? b : a))[0] * sz;
  const edit = { n, wx, wy, base, z: Float64Array.from(base), fixed, touched: new Uint8Array(n),
    baseNormals: nor.slice(), bounds: view.bounds, index: bucketIndex(wx, wy, x0, y0, x1, y1), grid: null,
    waterAt: w, baseW: Float64Array.from(w), baseWater, tri, waterIndex: wtri, waterTouched: false };
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
  if (PAINTS[s.brush]) { overlayDab(s); return; }  // the cover grid or where units go, not the ground
  if (WATER.has(s.brush)) {  // the water surface inside the circle, as rusemod.water does: no falloff
    const [xlo, xhi, ylo, yhi] = boxOf(s), level = s.brush === "water" ? s.level : ed.baseWater;
    near(ed.index, xlo, xhi, ylo, yhi, (i) => {
      if (ed.fixed[i] || !covers(s, ed.wx[i], ed.wy[i])) return;
      ed.waterAt[i] = level;
    });
    ed.waterTouched = true;
    return;
  }
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

// The water surface as the strokes left it: each point at its level, and a triangle is water when its three corners
// lie under the surface (the shipped meshes' rule, rusemod.tms). Untouched water keeps the game's own triangles.
function redrawWater() {
  const ed = mv.edit, gl = mv.gl;
  if (!ed || !gl || !gl.water) return;
  const g = gl.water.geometry, pos = g.attributes.position.array;
  for (let i = 0; i < ed.n; i++) pos[3 * i + 1] = ed.waterAt[i] * SCALE;
  g.attributes.position.needsUpdate = true;
  let index = ed.waterIndex;
  if (ed.waterTouched) {
    const tri = ed.tri, out = [];
    for (let k = 0; k < tri.length; k += 3) {
      const a = tri[k], b = tri[k + 1], c = tri[k + 2];
      if (ed.waterAt[a] >= ed.z[a] && ed.waterAt[b] >= ed.z[b] && ed.waterAt[c] >= ed.z[c]) out.push(a, b, c);
    }
    index = Uint32Array.from(out);
  }
  if (g.index.array !== index) g.setIndex(new gl.THREE.BufferAttribute(index, 1));
  g.computeVertexNormals();
  g.computeBoundingSphere();
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
  if (all || ed.waterTouched) redrawWater();
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
  ed.waterAt.set(ed.baseW);
  ed.waterTouched = false;
  for (const o of OVERLAYS) {
    if (o.cells) o.cells.set(o.base);
    o.batch = true;
  }
  for (const s of mv.brush.strokes) applyStroke(ed, s);
  for (const o of OVERLAYS) {
    o.batch = false;
    overlayDraw(o, 0, o.size - 1, 0, o.size - 1);
  }
  redraw(true, true);
  placeScenery();
}

// --- overlays over the ground, each a grid of cells drawn as a picture on the ground's own points (so they follow
// every stroke):
// cover, where units hide (the map's cover grid, StudioApi.map_cover), in green. The cover and uncover brushes paint
//   it and the town tool paints it around a town's buildings; the build writes them into the grid (rusemod.cover).
//   Proven in the game: infantry on painted cover are hidden (2026-09-30).
// moves, where units go (the map's two navigation graphs, StudioApi.map_movement): bit 1 = closed to infantry, bit 2
//   = closed to vehicles, so red is closed to every unit (water, cliffs, off the map), yellow to vehicles only (woods),
//   purple to infantry only. The block brushes close ground; the build takes it out of the graphs (rusemod.nav). The
//   open brushes open it again; the build adds it to the graphs where they have none (nav.Graph.open_ground).
//   Proven in the game: units plan around a blocked pit (2026-09-30). ---
const cover = { kinds: ["cover", "town", "forest"], colors: [null, [60, 210, 90, 125]] };
const moves = { kinds: ["block", "open"], colors: [null, [170, 90, 220, 120], [235, 200, 40, 115], [220, 50, 40, 120]] };
const OVERLAYS = [cover, moves];
for (const o of OVERLAYS) {
  Object.assign(o, { base: null, cells: null, size: 0, box: null, canvas: null, ctx: null, img: null, tex: null,
    mesh: null, show: false, batch: false });
}
// what a brush does to an overlay's cells: [overlay, bits it sets, bits it clears]
const PAINTS = { cover: [cover, 1, 0], uncover: [cover, 0, 1], block: [moves, 3, 0], block_infantry: [moves, 1, 0],
  block_vehicles: [moves, 2, 0], open: [moves, 0, 3], open_infantry: [moves, 0, 1], open_vehicles: [moves, 0, 2] };

function overlayShown(o) {
  return o.show || (mv.brush.on && o.kinds.includes(BRUSHES[mv.brush.name][0]));
}

function showOverlays() {
  for (const o of OVERLAYS) if (o.mesh) o.mesh.visible = overlayShown(o);
  if (mv.gl) mv.gl.draw();
}

// n*n bits in base64 (cell i at byte i >> 3, bit i & 7): `value` goes into each cell whose bit is set.
function unpackBits(bits, n, into, value) {
  const raw = atob(bits);
  for (let i = 0; i < n * n; i++) if ((raw.charCodeAt(i >> 3) >> (i & 7)) & 1) into[i] |= value;
}

async function loadCover(pack, ask) {
  dropOverlay(cover);
  const res = await mv.api.map_cover(pack);
  if (ask !== mv.ask || !mv.edit) return;
  const base = new Uint8Array(res.size * res.size);
  unpackBits(res.bits, res.size, base, 1);
  startOverlay(cover, base, res);
}

async function loadMoves(pack, ask) {
  dropOverlay(moves);
  const res = await mv.api.map_movement(pack);
  if (ask !== mv.ask || !mv.edit) return;
  const n = res.size, open = new Uint8Array(n * n);
  unpackBits(res.infantry, n, open, 1);
  unpackBits(res.vehicles, n, open, 2);
  startOverlay(moves, open.map((v) => 3 & ~v), res);
}

function startOverlay(o, base, res) {
  Object.assign(o, { base, cells: base.slice(), size: res.size, box: res.box });
  overlayMesh(o);
  o.batch = true;
  for (const s of mv.brush.strokes) if (PAINTS[s.brush] && PAINTS[s.brush][0] === o) overlayDab(s);
  o.batch = false;
  overlayDraw(o, 0, o.size - 1, 0, o.size - 1);
}

function dropOverlay(o) {
  if (o.mesh) {
    mv.gl.scene.remove(o.mesh);
    o.mesh.geometry.dispose();
    o.mesh.material.dispose();
  }
  Object.assign(o, { base: null, cells: null, mesh: null });
}

// The overlay shares the ground's points, with its own place in its picture; later overlays draw over earlier ones.
function overlayMesh(o) {
  const gl = mv.gl, ed = mv.edit, { THREE } = gl, n = o.size, [bx, by, bw, bh] = o.box, k = OVERLAYS.indexOf(o);
  if (!o.canvas || o.canvas.width !== n) {
    o.canvas = document.createElement("canvas");
    o.canvas.width = o.canvas.height = n;
    o.ctx = o.canvas.getContext("2d");
    o.img = o.ctx.createImageData(n, n);
    if (o.tex) o.tex.dispose();
    o.tex = new THREE.CanvasTexture(o.canvas);
    o.tex.flipY = false;  // row 0 is the grid's first row (y0), as the uv below says
    o.tex.userData.keep = true;
  }
  const src = gl.ground.geometry, g = new THREE.BufferGeometry(), uv = new Float32Array(ed.n * 2);
  for (let i = 0; i < ed.n; i++) { uv[2 * i] = (ed.wx[i] - bx) / bw; uv[2 * i + 1] = (ed.wy[i] - by) / bh; }
  g.setAttribute("position", src.attributes.position);
  g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
  g.setIndex(src.index);
  o.mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: o.tex, transparent: true, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2 - k, polygonOffsetUnits: -2 - k, side: THREE.DoubleSide }));
  o.mesh.frustumCulled = false;  // its points move with the ground's
  o.mesh.renderOrder = 1 + k;
  o.mesh.visible = overlayShown(o);
  gl.scene.add(o.mesh);
}

// One brush circle on the cells whose centres are inside it (rusemod.cover.paint's rule; rusemod.nav closes the
// graphs' circles that reach into it). A cover stroke with square = true (written by hand in terrain.toml, MOD_FORMAT
// §8) is a square along the map's axes, `radius` from its middle to each side, as the build paints it.
function overlayDab(s) {
  const [o, on, off] = PAINTS[s.brush];
  if (!o.cells) return;
  const n = o.size, [bx, by, bw, bh] = o.box, cw = bw / n, ch = bh / n;
  const c0 = Math.max(0, Math.floor((s.x - s.radius - bx) / cw)), c1 = Math.min(n - 1, Math.ceil((s.x + s.radius - bx) / cw));
  const r0 = Math.max(0, Math.floor((s.y - s.radius - by) / ch)), r1 = Math.min(n - 1, Math.ceil((s.y + s.radius - by) / ch));
  if (c0 > c1 || r0 > r1) return;
  const rr = s.radius * s.radius;
  for (let r = r0; r <= r1; r++) {
    const dy = by + (r + 0.5) * ch - s.y;
    for (let c = c0; c <= c1; c++) {
      const dx = bx + (c + 0.5) * cw - s.x, i = r * n + c;
      const inside = s.square ? Math.abs(dx) <= s.radius && Math.abs(dy) <= s.radius : dx * dx + dy * dy <= rr;
      if (inside) o.cells[i] = (o.cells[i] & ~off) | on;
    }
  }
  if (!o.batch) overlayDraw(o, r0, r1, c0, c1);
}

function overlayDraw(o, r0, r1, c0, c1) {
  if (!o.cells || !o.img) return;
  const n = o.size, px = o.img.data;
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      const i = r * n + c, k = 4 * i, rgba = o.colors[o.cells[i]];
      if (rgba) { px[k] = rgba[0]; px[k + 1] = rgba[1]; px[k + 2] = rgba[2]; px[k + 3] = rgba[3]; }
      else px[k + 3] = 0;
    }
  }
  o.ctx.putImageData(o.img, 0, 0, c0, r0, c1 - c0 + 1, r1 - r0 + 1);
  o.tex.needsUpdate = true;
  if (mv.gl) mv.gl.draw();
}

// --- roads: the map's own road pieces (StudioApi.map_roads: cubic Béziers), drawn in gold on the ground when the
// Roads box is ticked. Each is sampled into short lines seated on the ground, again after every stroke, so they
// follow the brushes. (Drawing new roads comes next: PLAN A3.) ---
const roads = { pieces: null, line: null, show: false };
const ROAD_STEP = 8000;  // map units per line (about 30 m): a long piece gets more, so it follows hills
const ROAD_LIFT = 600;   // map units above the ground (about 2 m), so the ground doesn't hide them

async function loadRoads(pack, ask) {
  dropRoads();
  const res = await mv.api.map_roads(pack);
  if (ask !== mv.ask || !mv.edit) return;
  roads.pieces = res.pieces;
  road.samples = null;  // snapping reads them
  drawRoads();
}

function dropRoads() {
  if (roads.line) {
    mv.gl.scene.remove(roads.line);
    roads.line.geometry.dispose();
    roads.line.material.dispose();
  }
  Object.assign(roads, { pieces: null, line: null });
}

function drawRoads() {
  const gl = mv.gl, P = roads.pieces;
  if (!gl || !P || !mv.edit) return;
  if (!roads.show && !road.on) {
    if (roads.line && roads.line.visible) { roads.line.visible = false; gl.draw(); }
    return;
  }
  const { THREE } = gl, grid = makeGrid(mv.edit), n = P.length / 8, steps = new Uint16Array(n);
  let total = 0;
  for (let i = 0; i < n; i++) {  // the control polygon's length bounds the curve's
    const o = 8 * i, len = Math.hypot(P[o + 2] - P[o], P[o + 3] - P[o + 1]) + Math.hypot(P[o + 4] - P[o + 2], P[o + 5] - P[o + 3])
      + Math.hypot(P[o + 6] - P[o + 4], P[o + 7] - P[o + 5]);
    steps[i] = Math.min(64, Math.max(2, Math.ceil(len / ROAD_STEP)));
    total += steps[i];
  }
  const pos = new Float32Array(total * 6);
  let k = 0;
  for (let i = 0; i < n; i++) {
    const o = 8 * i;
    let px = P[o], py = P[o + 1];
    for (let s = 1; s <= steps[i]; s++) {
      const t = s / steps[i], u = 1 - t, a = u * u * u, b = 3 * u * u * t, c = 3 * u * t * t, d = t * t * t;
      const x = a * P[o] + b * P[o + 2] + c * P[o + 4] + d * P[o + 6], y = a * P[o + 1] + b * P[o + 3] + c * P[o + 5] + d * P[o + 7];
      pos[k++] = px * SCALE; pos[k++] = (groundAt(grid, px, py) + ROAD_LIFT) * SCALE; pos[k++] = py * SCALE;
      pos[k++] = x * SCALE; pos[k++] = (groundAt(grid, x, y) + ROAD_LIFT) * SCALE; pos[k++] = y * SCALE;
      px = x; py = y;
    }
  }
  if (!roads.line) {
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    roads.line = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: 0xf2c12e, transparent: true, opacity: 0.95 }));
    roads.line.renderOrder = 4;
    roads.line.frustumCulled = false;
    gl.scene.add(roads.line);
  } else {
    roads.line.geometry.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  }
  roads.line.visible = true;
  gl.draw();
}

// Every building the map and the mod put here: the map's (map_scenery) and the ones placed in this mod.
function buildingSpots() {
  const d = mv.scenery.data, out = [];
  const flat = (d && d.items && d.items.building) || [];
  for (let i = 0; i < flat.length; i += 5) out.push([flat[i + 1], flat[i + 2]]);
  const groupOf = new Map(((d && d.palette) || []).map((r) => [r[0], r[2]]));
  for (const o of mv.place.objects) if (groupOf.get(o.type) === "building") out.push([o.x, o.y]);
  return out;
}

// The town clicked: the building nearest the click, and every building linked to it by a chain of neighbours
// (no further apart than twice the margin, at least 60 m), within 800 m of the click. Each gets a cover circle.
function townStrokes(x, y) {
  const r = brushRadius("town"), link = Math.max(2 * r, 6000), reach = 80000;
  const pts = buildingSpots().filter(([px, py]) => (px - x) ** 2 + (py - y) ** 2 <= reach * reach);
  let seed = -1, best = 15000 * 15000;  // a building within 150 m of the click
  pts.forEach(([px, py], i) => { const d = (px - x) ** 2 + (py - y) ** 2; if (d < best) { best = d; seed = i; } });
  if (seed < 0) return [];
  const town = new Set([seed]), queue = [seed];
  while (queue.length && town.size < 3000) {
    const [qx, qy] = pts[queue.shift()];
    pts.forEach(([px, py], j) => {
      if (!town.has(j) && (px - qx) ** 2 + (py - qy) ** 2 <= link * link) { town.add(j); queue.push(j); }
    });
  }
  return [...town].map((i) => ({ brush: "cover", x: Math.round(pts[i][0]), y: Math.round(pts[i][1]), radius: r }));
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
  if (scen.group) drawScenario();
  drawRoads();  // the roads follow the ground too
  drawModRoads();
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

// --- the map's scenarios (StudioApi.map_scenarios, rusemod.scenario): zones, starting points, spawns and names, drawn
// over the ground for the scenario picked. Read-only for now: the first step toward making maps of one's own.
const ALLIANCE = [0x3f7fe0, 0xe0503f, 0x49b85a, 0xe0c33f, 0xa35ee0, 0x3fc8d8];
// tool: "move" or "spawn" (or null); selected: the item being moved; units: what can be spawned (StudioApi.units);
// kind, type: the Spawn tool's first two dropdowns (the third is the unit, by nation)
const scen = { data: null, pick: 0, show: true, group: null, tool: null, selected: null, units: null, kind: "ground",
  type: null, camp: "-1", count: 1, formation: "line", gap: {}, team: 1, players: null };
const SPAWN_KINDS = ["buildings", "ground", "infantry", "air"];
// Several at once: how many one click adds, in which shape, how far apart (metres, per kind to start with). The shape
// faces up the screen (away from the camera), its middle on the click; each unit is turned that way too.
const SPAWN_COUNTS = [1, 2, 4, 6, 8, 10];
const FORMATIONS = ["line", "column", "wedge", "box", "circle"];
const SPAWN_GAP = { infantry: 12, ground: 25, air: 50, buildings: 60 };

// [across, ahead] of each of `n` places, in gaps, the shape's middle at [0, 0].
function formationOffsets(shape, n) {
  const out = [];
  if (n <= 1) return [[0, 0]];
  for (let i = 0; i < n; i++) {
    if (shape === "line") out.push([i - (n - 1) / 2, 0]);
    else if (shape === "column") out.push([0, -i]);
    else if (shape === "wedge") { const k = Math.ceil(i / 2); out.push([i % 2 ? -k : k, -k]); }  // a V: the leader at the tip
    else if (shape === "circle") {  // neighbours a gap apart
      const r = 0.5 / Math.sin(Math.PI / n), a = 2 * Math.PI * i / n;
      out.push([r * Math.sin(a), r * Math.cos(a)]);
    } else {  // box: two ranks up to ten, then a square
      const rows = n <= 10 ? 2 : Math.ceil(Math.sqrt(n)), cols = Math.ceil(n / rows);
      const r = Math.floor(i / cols), inRow = Math.min(cols, n - r * cols);
      out.push([i % cols - (inRow - 1) / 2, -r]);
    }
  }
  const ahead = out.map((o) => o[1]), mid = (Math.max(...ahead) + Math.min(...ahead)) / 2;
  return out.map(([a, b]) => [a, b - mid]);
}

function spawnGap() {
  return scen.gap[scen.kind] ?? SPAWN_GAP[scen.kind] ?? 25;
}

// Up the screen, on the map: the camera's looking direction across the ground, as a unit [x, y] (game x east, y
// south = the scene's X and Z).
function screenAhead() {
  const gl = mv.gl, dx = gl.controls.target.x - gl.camera.position.x, dz = gl.controls.target.z - gl.camera.position.z;
  const len = Math.hypot(dx, dz) || 1;
  return [dx / len, dz / len];
}

// The places a click at map (x, y) spawns at.
function formationPoints(x, y) {
  const gap = spawnGap() * METRE, [fx, fy] = screenAhead(), rx = -fy, ry = fx;
  return formationOffsets(scen.formation, scen.count).map(([a, b]) =>
    [Math.round(x + (a * rx + b * fx) * gap), Math.round(y + (a * ry + b * fy) * gap)]);
}

// A ring where each unit will stand, under the pointer, while adding units.
function showFormation(hit) {
  const gl = mv.gl;
  if (!gl || !gl.ring) return;
  gl.ghosts = gl.ghosts || [];
  const pts = hit && scen.tool === "spawn" ? formationPoints(hit.x / SCALE, hit.z / SCALE) : [];
  const r = spawnGap() * METRE * SCALE * 0.3;
  while (gl.ghosts.length < pts.length) { const g = gl.ring.clone(); gl.scene.add(g); gl.ghosts.push(g); }
  if (!pts.length && !gl.ghosts.some((g) => g.visible)) return;
  gl.ghosts.forEach((g, i) => {
    g.visible = i < pts.length;
    if (g.visible) { g.position.set(pts[i][0] * SCALE, hit.y + r * 0.1, pts[i][1] * SCALE); g.scale.set(r, r, r); }
  });
  gl.draw();
}
const GROUP_ORDER = ["hq", "money", "factory", "fort", "fake", "barracks", "armor", "antitank", "artillery", "prototype",
  "airfield", "turret", "other"];

async function loadScenarios(pack, ask) {
  clearScenario();
  scen.data = null;
  const data = await mv.api.map_scenarios(pack);
  if (ask !== mv.ask) return;
  scen.data = data;
  scen.pick = 0;
  scen.selected = null;
  renderScenarioPick();
  drawScenario();
  renderScenTools();
  loadPlayers(pack, ask);
}

// --- how many players the map takes (PLAN A10; StudioApi.map_players / set_players, the mod's maps/<map>/map.toml):
// the map's online entry, a count from 2 to 8, and the starting points a count still needs (Add starting point) ---
async function loadPlayers(pack, ask) {
  try {
    const got = await mv.api.map_players(pack);
    if (ask !== undefined && ask !== mv.ask) return;
    scen.players = got;
  } catch (err) { scen.players = null; }
  renderPlayers();
}

function renderPlayers() {
  const w = mv.words, box = $("scen-players"), note = $("scen-players-note"), p = scen.players;
  const entry = p ? p.entries.find((e) => !p.entry || e.name === p.entry) : null;
  box.classList.toggle("hidden", !entry);
  note.className = "small";
  if (!entry) { note.textContent = p && !p.entries.length ? w.scen_players_none : ""; return; }
  const now = p.mod || entry.players, most = p.most || 8;
  const counts = [];
  for (let n = 2; n <= most; n++) counts.push(n);
  box.replaceChildren(el("span", { className: "muted small", textContent: w.scen_players_label }),
    ...counts.map((n) => chipOf(n === entry.players ? fill(w.scen_players_game, { n }) : String(n), w.tip_scen_players,
      now === n, () => setPlayers(n === entry.players ? null : n))));
  if (!p.mod) { note.textContent = ""; return; }
  note.className = "small" + (p.missing.length ? " error-text" : "");
  const list = p.missing.map(([n, q]) => fill(w.scen_seat, { n, p: q })).join("; ");
  note.textContent = p.missing.length ? fill(w.scen_players_missing, { n: p.mod, list, where: entry.name }) : w.scen_players_ok;
}

async function setPlayers(n) {
  if (!mv.brush.mod) { scenNote(mv.words.no_mod, "error"); return; }
  try {
    scen.players = await mv.api.set_players(mv.current, n);
    renderPlayers();
  } catch (err) { scenNote((err && err.message) || String(err), "error"); }
}

function clearScenario() {
  if (scen.group && mv.gl) {
    mv.gl.scene.remove(scen.group);
    scen.group.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); }
    });
  }
  scen.group = null;
}

// A scenario's name: what the game's menus call it in the Studio's language (Code names: the map list's own name),
// else its file's name.
function scenarioLabel(s) {
  const e = (s.entries || [])[0];
  if (e) return (mv.lang !== "base" && e.titles && e.titles[mv.lang]) || e.name;
  const stem = s.file.replace(/\.scenario$/i, "").replace(/^leveldesign_?/i, "");
  return stem ? stem.replace(/_/g, " ") : mv.words.scen_main;
}

// The map's scenarios, grouped as the game uses them: skirmish maps, Operations, campaign chapters, demos, test
// setups, and files no menu loads.
function renderScenarioPick() {
  const w = mv.words, pick = $("scen-pick"), list = (scen.data || {}).scenarios || [];
  const groups = [];
  list.forEach((s, i) => {
    const kind = s.kind || "unused";
    let g = groups.find((x) => x.kind === kind);
    if (!g) groups.push(g = { kind, options: [] });
    g.options.push(el("option", { value: String(i), textContent: scenarioLabel(s), title: s.file }));
  });
  pick.replaceChildren(...groups.map((g) => el("optgroup", { label: w["scen_kind_" + g.kind] || g.kind }, ...g.options)));
  pick.value = String(scen.pick);
  pick.disabled = !list.length;
  pick.title = w.tip_scen_pick;
  const s = list[scen.pick];
  // where this setup plays in the game: its menu, its title, and the players it's made for
  $("scen-where").textContent = s && (s.entries || []).length ? fill(w.scen_where, { where: s.entries.map((e) =>
    `${w["scen_kind_" + e.kind] || e.kind} › ${(e.titles || {})[mv.lang] || (e.titles || {}).us || e.name}`
    + ((/^\((\d+)\)/.exec(e.name || "") || [])[1] ? ` (${fill(w.scen_players, { n: /^\((\d+)\)/.exec(e.name)[1] })})` : "")).join(" · ") }) : "";
  $("scen-where").title = w.tip_scen_where;
  if (!s) { $("scen-stats").textContent = scen.data ? w.scen_none : ""; return; }
  const n = (k) => s.items.filter((i) => i.kind === k).length;
  $("scen-stats").textContent = fill(w.scen_stats, { zones: s.zones.length, starts: n("StartingPoint"), spawns: n("Spawn"),
    names: n("LabelVille") + n("LabelMontagne") });
}

// A word on the map (a town's or a mountain's name), always facing the camera.
function mapLabel(text, colour, size) {
  const { THREE } = mv.gl, c = document.createElement("canvas"), g = c.getContext("2d");
  g.font = "600 44px system-ui, sans-serif";
  c.width = Math.ceil(g.measureText(text).width) + 24;
  c.height = 64;
  g.font = "600 44px system-ui, sans-serif";
  g.textBaseline = "middle";
  g.lineWidth = 8;
  g.strokeStyle = "rgba(0,0,0,0.75)";
  g.strokeText(text, 12, 32);
  g.fillStyle = colour;
  g.fillText(text, 12, 32);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true }));
  sprite.scale.set(size * c.width / c.height, size, 1);
  sprite.renderOrder = 10;
  return sprite;
}

// Everything the picked scenario puts on the map, on the ground as it is now (strokes too).
function drawScenario() {
  clearScenario();
  const gl = mv.gl, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!gl || !mv.edit || !s) { if (gl) gl.draw(); return; }
  const { THREE } = gl, grid = makeGrid(mv.edit), group = new THREE.Group(), size = mv.size || 1000;
  const lift = size * 0.0015, at = (x, y, up = 0) => new THREE.Vector3(x * SCALE, groundAt(grid, x, y) * SCALE + lift + up, y * SCALE);
  s.zones.forEach((z, k) => {  // a zone: its own triangles, see-through, in a colour of its own
    const n = z.points.length / 2, pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const v = at(z.points[2 * i], z.points[2 * i + 1]);
      pos[3 * i] = v.x; pos[3 * i + 1] = v.y; pos[3 * i + 2] = v.z;
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setIndex(z.triangles);
    const mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: new THREE.Color().setHSL((k * 0.137) % 1, 0.7, 0.55),
      transparent: true, opacity: 0.3, side: THREE.DoubleSide, depthWrite: false }));
    mesh.userData.label = `${mv.words.scen_zone} ${k + 1} · ${z.name}`;
    group.add(mesh);
  });
  const pillar = size * 0.03;
  for (const it of s.items) {
    if (it.kind === "StartingPoint") {  // a tall pillar in the alliance's colour
      const colour = ALLIANCE[((it.alliance || 1) - 1) % ALLIANCE.length];
      const m = new THREE.Mesh(new THREE.CylinderGeometry(pillar * 0.08, pillar * 0.08, pillar, 12),
        new THREE.MeshLambertMaterial({ color: scen.selected === it.item ? 0xffffff : colour }));
      m.position.copy(at(it.x, it.y, pillar / 2));
      m.userData.label = fill(mv.words.scen_start_place, { n: it.alliance || "?", p: it.place || 1 })
        + (it.name ? ` · ${it.name}` : "") + (it.moved ? ` · ${mv.words.scen_moved}` : "")
        + (it.mine ? ` · ${mv.words.scen_mine}` : "");
      m.userData.item = it.item;
      group.add(m);
    } else if (it.kind === "Spawn") {  // a small diamond where reinforcements arrive
      const colour = scen.selected === it.item ? 0xffd34d : it.mine ? PLACED_COLOUR : 0xf0f0f0;
      const m = new THREE.Mesh(new THREE.OctahedronGeometry(pillar * (it.mine ? 0.16 : 0.12)), new THREE.MeshLambertMaterial({ color: colour }));
      m.position.copy(at(it.x, it.y, pillar * 0.15));
      m.userData.label = `${mv.words.scen_spawn}${it.name ? " · " + it.name : ""}${it.what ? " · " + it.what : ""}`
        + (it.camp === -1 || (it.mine && it.camp === null) ? ` · ${mv.words.scen_side_neutral}`
          : it.camp !== undefined && it.camp !== null ? ` · ${fill(mv.words.scen_side_n, { n: it.camp })}` : "")
        + (it.mine ? ` · ${mv.words.scen_mine}` : it.moved ? ` · ${mv.words.scen_moved}` : "");
      m.userData.item = it.item;
      group.add(m);
    } else if (it.kind === "CircularZone" && it.radius) {
      const pts = [];
      for (let a = 0; a <= 64; a++) {
        const r = a / 64 * Math.PI * 2;
        pts.push(at(it.x + Math.cos(r) * it.radius, it.y + Math.sin(r) * it.radius));
      }
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x7fe0f0 }));
      line.userData.label = it.name;
      group.add(line);
    } else if (it.kind === "RectangleZone" && it.width && it.height) {
      const c = Math.cos(it.turn), sn = Math.sin(it.turn), hw = it.width / 2, hh = it.height / 2;
      const pts = [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh], [-hw, -hh]].map(([dx, dy]) =>
        at(it.x + dx * c - dy * sn, it.y + dx * sn + dy * c));
      const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x7fe0f0 }));
      line.userData.label = it.name;
      group.add(line);
    } else if ((it.kind === "LabelVille" || it.kind === "LabelMontagne") && (it.text || it.name)) {
      const sprite = mapLabel(it.text || it.name, it.kind === "LabelVille" ? "#ffffff" : "#e8d9a8", size * 0.012);
      sprite.position.copy(at(it.x, it.y, pillar * 0.4));
      group.add(sprite);
    }
  }
  group.visible = scen.show;
  scen.group = group;
  gl.scene.add(group);
  gl.draw();
}

// --- editing the picked scenario (saved in the mod's maps/<map>/scenario.toml: StudioApi.scenario_*) ---
// Move: click a starting point or a spawn, then the ground where it goes. Spawn: pick a unit or building and a side,
// then click the ground. The item picked can be put back (moved) or taken out (the mod's own spawn).
function scenNote(text, kind) {
  const n = $("scen-note");
  n.replaceChildren(text || "");
  n.className = "small" + (kind === "error" ? " error-text" : "");
}

function setScenTool(tool) {
  scen.tool = scen.tool === tool ? null : tool;
  scen.selected = null;
  if (scen.tool) { if (mv.brush.on) setBrushMode(false); if (mv.place.on) setPlaceMode(false); stopRoad(); }
  dock.scenario = true;  // the tool dropped again keeps the scenario's tray open
  pointerMode();
  renderScenTools();
  drawScenario();
  renderDock();
}

async function loadSpawnUnits() {
  if (scen.units) return;
  const res = await mv.api.units(mv.lang || "base", "all", -1, "", "all");
  scen.units = res.units.filter((u) => !u.new);  // a mod's new unit isn't in the game's files yet
  renderScenTools();
}

function renderScenTools() {
  const w = mv.words, s = ((scen.data || {}).scenarios || [])[scen.pick];
  iconTile($("scen-move"), "move", w.scen_move_tool).title = w.tip_scen_move;
  $("scen-move").setAttribute("aria-pressed", String(scen.tool === "move"));
  iconTile($("scen-spawn"), "spawn", w.scen_spawn_tool).title = w.tip_scen_spawn;
  $("scen-spawn").setAttribute("aria-pressed", String(scen.tool === "spawn"));
  iconTile($("scen-start"), "start", w.scen_start_tool).title = w.tip_scen_start;
  $("scen-start").setAttribute("aria-pressed", String(scen.tool === "start"));
  $("scen-move").disabled = $("scen-spawn").disabled = $("scen-start").disabled = !s;
  const team = $("scen-team");
  team.classList.toggle("hidden", scen.tool !== "start");
  if (scen.tool === "start") {
    team.replaceChildren(...[1, 2, 3, 4, 5, 6, 7, 8].map((n) => chipOf(fill(w.scen_team_n, { n }), w.tip_scen_team,
      scen.team === n, () => { scen.team = n; renderScenTools(); })));
  }
  const kindPick = $("scen-kind"), typePick = $("scen-group"), unit = $("scen-unit"), camp = $("scen-camp");
  for (const box of [kindPick, typePick, unit, camp, $("scen-count"), $("scen-gap-row")]) box.classList.toggle("hidden", scen.tool !== "spawn");
  $("scen-formation").classList.toggle("hidden", scen.tool !== "spawn" || scen.count === 1);
  if (scen.tool !== "spawn") showFormation(null);
  if (scen.tool === "spawn") {
    if (!scen.units) { loadSpawnUnits().catch((err) => scenNote((err && err.message) || String(err), "error")); }
    // 1: the kind; 2: what it's for (a building's job, or the factory that builds a unit); 3: the unit, by nation
    const all = scen.units || [];
    kindPick.replaceChildren(...SPAWN_KINDS.map((k) => chipOf(w[k] || k, w.tip_scen_kind, scen.kind === k,
      () => { scen.kind = k; scen.type = null; renderScenTools(); })));
    const ofKind = all.filter((u) => u.kind === scen.kind);
    const types = GROUP_ORDER.filter((g) => ofKind.some((u) => u.group === g));
    if (!types.includes(scen.type)) scen.type = types[0] || null;
    typePick.replaceChildren(...types.map((g) => chipOf(`${w["group_" + g] || g} (${ofKind.filter((u) => u.group === g).length})`,
      w.tip_group, scen.type === g, () => { scen.type = g; renderScenTools(); })));
    const keep = unit.value, byNation = new Map();
    for (const u of ofKind.filter((x) => x.group === scen.type)) {
      if (!byNation.has(u.nation_name)) byNation.set(u.nation_name, []);
      byNation.get(u.nation_name).push(u);
    }
    unit.replaceChildren(...[...byNation].map(([nation, us]) => el("optgroup", { label: nation || "?" },
      ...us.sort((a, b) => a.name.localeCompare(b.name)).map((u) => el("option", { value: u.address,
        textContent: u.name + (u.name !== u.base_name && mv.lang !== "base" ? ` (${u.base_name.replace(/^Descriptor_[A-Za-z]+_/, "")})` : "") })))));
    if (keep && [...unit.options].some((o) => o.value === keep)) unit.value = keep;
    unit.title = w.tip_scen_unit;
    // a skirmish game spawns only neutral items (camp -1): a unit for a player's side would never appear there
    const skirmish = !!s && s.kind === "skirmish";
    if (skirmish) scen.camp = "-1";
    camp.replaceChildren(...(skirmish ? ["-1"] : ["-1", "1", "2", "3", "4", "5", "6", "7", "8"]).map((n) =>
      chipOf(n === "-1" ? w.scen_side_neutral : fill(w.scen_side_n, { n }), skirmish ? w.tip_scen_camp_skirmish : w.tip_scen_camp,
        scen.camp === n, () => { scen.camp = n; renderScenTools(); })));
    $("scen-count").replaceChildren(el("span", { className: "muted small", textContent: w.scen_count }),
      ...SPAWN_COUNTS.map((n) => chipOf(String(n), w.tip_scen_count, scen.count === n, () => { scen.count = n; renderScenTools(); })));
    $("scen-formation").replaceChildren(...FORMATIONS.map((f) => {
      const tile = iconTile(el("button", { type: "button", className: "tool-tile small-tile", title: w.tip_scen_formation }),
        "formation_" + f, w["formation_" + f]);
      tile.setAttribute("aria-pressed", String(scen.formation === f));
      tile.addEventListener("click", () => { scen.formation = f; renderScenTools(); });
      return tile;
    }));
    $("scen-gap").value = spawnGap();
    $("scen-gap-label").textContent = fill(w.place_spacing, { m: spawnGap() });
    $("scen-gap-row").title = w.tip_scen_gap;
  }
  if (!mv.brush.mod && scen.tool) { scenNote(w.no_mod, "error"); return; }
  if (scen.tool === "move") {
    const it = s && scen.selected !== null ? s.items[scen.selected] : null;
    if (!it) { scenNote(w.scen_pick_item); return; }
    const parts = [fill(w.scen_pick_place, { what: it.kind === "StartingPoint"
      ? fill(w.scen_start_place, { n: it.alliance || "?", p: it.place || 1 }) : w.scen_spawn })];
    const n = $("scen-note");
    scenNote(parts[0]);
    if (it.mine || it.moved) {
      const b = el("button", { type: "button", className: "link", textContent: it.mine ? w.scen_remove : w.scen_put_back });
      b.addEventListener("click", () => it.mine
        ? scenEdit(() => it.start !== undefined ? mv.api.scenario_remove_start(mv.current, it.start)
          : mv.api.scenario_remove_spawn(mv.current, it.spawn)).then(() => loadPlayers(mv.current))
        : scenEdit(() => mv.api.scenario_put_back(mv.current, s.file, it.item)));
      n.append(" ", b);
    }
  } else if (scen.tool === "spawn") scenNote(w.scen_spawn_help);
  else if (scen.tool === "start") scenNote(w.scen_start_help);
  else scenNote("");
}

// Save a change, then draw the scenario as the mod leaves it now.
async function scenEdit(call) {
  try {
    const keepFile = ((scen.data || {}).scenarios || [])[scen.pick];
    scen.data = await call();
    const i = scen.data.scenarios.findIndex((x) => keepFile && x.file === keepFile.file);
    if (i >= 0) scen.pick = i;
    scen.selected = null;
    renderScenarioPick();
    drawScenario();
    renderScenTools();
  } catch (err) { scenNote((err && err.message) || String(err), "error"); }
}

function scenPointerDown(ev) {
  const gl = mv.gl, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!scen.tool || ev.button !== 0 || !gl.ground || !mv.edit || !s) return;
  ev.preventDefault();
  if (!mv.brush.mod) { scenNote(mv.words.no_mod, "error"); return; }
  if (scen.tool === "move" && scen.selected === null) {  // first click: which item
    const rect = gl.renderer.domElement.getBoundingClientRect();
    gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
    gl.raycaster.setFromCamera(gl.ndc, gl.camera);
    const hit = scen.group ? gl.raycaster.intersectObjects(scen.group.children.filter((o) => o.userData.item !== undefined), false)[0] : null;
    if (!hit) { scenNote(mv.words.scen_pick_item, "error"); return; }
    scen.selected = hit.object.userData.item;
    drawScenario();
    renderScenTools();
    return;
  }
  const p = hitGround(ev);
  if (!p) return;
  const x = p.x / SCALE, y = p.z / SCALE;
  if (scen.tool === "move") {
    const it = s.items[scen.selected];
    if (it.mine && it.start !== undefined) scenEdit(() => mv.api.scenario_move_start(mv.current, it.start, x, y));
    else if (it.mine) scenEdit(() => mv.api.scenario_move_spawn(mv.current, it.spawn, x, y));  // the mod's own spawn
    else scenEdit(() => mv.api.scenario_move(mv.current, s.file, it.item, x, y));
    return;
  }
  if (scen.tool === "start") {  // a new starting point: the team's next place
    scenEdit(() => mv.api.scenario_add_start(mv.current, s.file, scen.team, x, y)).then(() => loadPlayers(mv.current));
    return;
  }
  const unit = $("scen-unit").value, camp = scen.camp, [fx, fy] = screenAhead();
  if (!unit) { scenNote(mv.words.scen_pick_unit, "error"); return; }
  scenEdit(() => mv.api.scenario_spawn_many(mv.current, s.file, unit, formationPoints(x, y),
    camp === "" ? null : Number(camp), Math.atan2(fy, fx)));
}

// Pointing at a zone, a starting point or a spawn says what it is.
function scenarioAt(ev) {
  const gl = mv.gl;
  if (!scen.group || !scen.group.visible) return "";
  const rect = gl.renderer.domElement.getBoundingClientRect();
  gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  gl.raycaster.setFromCamera(gl.ndc, gl.camera);
  const shown = scen.group.children.filter((o) => o.isMesh && o.userData.label);
  const hits = gl.raycaster.intersectObjects(shown, false);
  const solid = hits.find((h) => h.object.geometry.type !== "BufferGeometry");  // a pillar or a diamond before a zone
  return ((solid || hits[0]) || { object: { userData: {} } }).object.userData.label || "";
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
// the trees Forest strokes placed: the brushes' Undo takes them back with their cover, not the Place panel's
const forestTrees = new WeakSet();
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
  $("place-scenery-note").textContent = w.scenery_note;  // no cover from placed scenery; buildings stop units
  $("place-search").placeholder = w.search || "";
  $("place-search").title = w.tip_place_search;
  $("place-type").title = w.tip_place_type;
  $("place-turn-label").textContent = `${w.place_turn} ${p.turn}°`;
  $("place-turn").title = w.tip_place_turn;
  $("place-size-label").textContent = `${w.brush_size} ${p.size.toFixed(1)}×`;
  $("place-size").title = w.tip_place_size;
  $("place-solid-row").classList.toggle("hidden", p.group !== "building");  // only buildings stop units
  $("place-solid").checked = p.solid;
  $("place-solid-label").textContent = w.place_solid;
  $("place-solid-row").title = w.tip_place_solid;
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
  if (on) { dock.scenario = false; stopRoad(); }
  if (on && scen.tool) { scen.tool = null; scen.selected = null; renderScenTools(); drawScenario(); }
  if (!on) { mv.place.lineStart = null; showPlaceGuide(null); }
  if (on && mv.brush.on) setBrushMode(false);
  pointerMode();
  if (on) placeNote(!mv.place.mod ? mv.words.no_mod : !mv.place.type ? whyNoType() : "", "error");
  if (!on) $("map-help").textContent = mv.brush.on ? mv.words.brush_help : mv.words.map_help;
  renderPlace();
  renderDock();
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
  const obj = { type: p.type, x: Math.round(hit.x / SCALE), y: Math.round(hit.z / SCALE), turn: p.turn, size: p.size,
    solid: p.solid };
  p.objects.push(obj);
  drawPlaced();
  try {
    await mv.api.scenery_add(pack, [obj]);
    if (pack !== mv.current) return;
    p.groups.push([obj]);
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
    p.groups.push(objs);
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
  return { type: p.type, x: Math.round(x), y: Math.round(y), turn: varied ? Math.floor(Math.random() * 360) : turn, size,
    solid: p.solid };
}

// Painting an area: each spot the pointer passes scatters objects in the circle, never closer than the spacing to
// another one (this stroke's, or any the mod placed before), so going over a spot twice doesn't pile them up. The
// Forest brush scatters its trees the same way: `how` gives its circle, spacing and trees ({ r, gap, make(x, y) }).
function scatter(stroke, x, y, how) {
  const p = mv.place, gap = how ? how.gap : spacingOf(p.group) * METRE, r = how ? how.r : p.area * METRE, cell = gap;
  const make = how ? how.make : (ox, oy) => objectAt(ox, oy, around(p.turn, 45));
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
    const o = make(ox, oy);
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

// Undo takes back the last click, area or line placed, by the objects themselves: a Forest stroke's trees (the
// brushes' Undo takes those, with its cover) may have come after them.
async function undoPlace() {
  const p = mv.place, pack = mv.current;
  if (!p.mod || !p.objects.length || p.painting) return;
  const mine = p.objects.filter((o) => !forestTrees.has(o));
  const group = p.groups.length ? p.groups.pop() : mine.slice(-1);  // an area or a line goes back in one go
  if (!group.length) return;
  try {
    await mv.api.scenery_undo(pack, group.length, group);
    if (pack !== mv.current) return;
    takeOff(group);
    renderPlace();
  } catch (err) { placeNote((err && err.message) || String(err), "error"); }
}

// Objects taken off the map: out of the list and the view.
function takeOff(objs) {
  const gone = new Set(objs);
  mv.place.objects = mv.place.objects.filter((o) => !gone.has(o));
  drawPlaced();
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
  for (const o of OVERLAYS) dropOverlay(o);
  dropRoads();
  dropModRoads();
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
  $("map-dock").classList.remove("hidden");
  loadStrokes(pack, ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
  loadScenery(pack, ask).then(() => loadModels(pack, ask).catch((err) => {  // the shapes stay when models can't be had
    $("map-ground").textContent = (err && err.message) || String(err);
  })).catch((err) => {  // no types to place then: the place panel says so too
    $("scenery-stats").textContent = (err && err.message) || String(err);
    placeNote((err && err.message) || String(err), "error");
  });
  loadPlaced(pack, ask).catch((err) => placeNote((err && err.message) || String(err), "error"));
  loadScenarios(pack, ask).catch((err) => { $("scen-stats").textContent = (err && err.message) || String(err); });
  loadCover(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
  loadMoves(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
  loadRoads(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
  loadModRoads(pack, ask).catch((err) => roadNote((err && err.message) || String(err), "error"));
  realGround(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
}

// --- the dock: the tools by kind along the bottom, as Cities: Skylines does it (a bar of kinds; the kind picked opens
// its tray above), drawn in the game's own HUD look (style.css). [kind, its brushes]: the three place kinds place the
// map's own types, the scenario kind edits the picked scenario. ---
const DOCK = [
  ["terrain", ["hill", "raise", "lower", "crater", "plateau", "flatten", "level", "smooth", "ramp"]],
  ["water", ["water", "drain"]],
  ["cover", ["cover", "uncover", "town", "forest"]],
  ["movement", ["block", "block_infantry", "block_vehicles", "open", "open_infantry", "open_vehicles"]],
  ["roads", null],
  ["building", null], ["prop", null], ["vegetation", null],
  ["scenario", null],
];
const dock = { scenario: false, last: {} };  // the scenario kind open (no tool picked yet); the last brush of each kind

// 24-unit line drawings, one per kind and tool (stroked, see .dock-tile svg)
const ICONS = {
  look: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6z",
  terrain: "M2 20l7-12 4 6 3-4 6 10z",
  water: "M2 9c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1.5 5-1 M2 15c2.5-2 5-2 7.5 0s5 2 7.5 0 3.5-1.5 5-1",
  cover: "M3 13a4 4 0 1 0 8 0a4 4 0 1 0-8 0z M11 10a5 5 0 1 0 10 0a5 5 0 1 0-10 0z M7 17v4 M16 15v6",
  movement: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M5.6 5.6l12.8 12.8",
  building: "M3 11l9-7 9 7 M5 10v10h14V10 M10 20v-6h4v6",
  prop: "M4 7l8-4 8 4v10l-8 4-8-4z M4 7l8 4 8-4 M12 11v10",
  vegetation: "M12 2l-6 9h4l-5 7h14l-5-7h4z M12 18v4",
  scenario: "M5 21V4 M5 4h11l-2 4 2 4H5",
  roads: "M9 21l2-18 M15 21l-2-18 M12 5v2 M12 11v2 M12 17v2",
  road_straight: "M5 20L19 4 M2 17L15 2 M8 22L22 7",
  road_curve: "M3 21C3 11 10 4 21 4 M7 21c0-7 5-12 14-12",
  road_free: "M2 18c4-7 6 1 10-5s5-8 10-6 M2 22c4-7 6 1 10-5s5-8 10-6",
  hill: "M2 19c4 0 6-11 10-11s6 11 10 11",
  raise: "M12 19V5 M6 11l6-6 6 6 M3 21h18",
  lower: "M12 5v14 M6 13l6 6 6-6 M3 3h18",
  crater: "M2 9h4c1.5 7 10.5 7 12 0h4",
  plateau: "M2 19h3l3-9h8l3 9h3",
  flatten: "M3 12h18 M12 3v6 M9 6l3 3 3-3 M12 21v-6 M9 18l3-3 3 3",
  level: "M3 9h18v6H3z M10 9v6 M14 9v6",
  smooth: "M3 16c5-7 13-7 18 0 M6 20h12",
  ramp: "M3 19h18V7z",
  drop: "M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z",
  drain: "M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z M4 4l16 16",
  uncover: "M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z M4 4l16 16",
  town: "M2 20V11l5-4 5 4v9 M12 20v-7l5-4 5 4v7 M2 20h20",
  block_infantry: "M12 3a2 2 0 1 0 0 4a2 2 0 1 0 0-4z M12 8v7 M8 11h8 M9 21l3-6 3 6 M3 3l18 18",
  block_vehicles: "M3 16h18v4H3z M7 16v-4h8v4 M15 13h6 M3 3l18 18",
  open: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M7 12h10 M13 8l4 4-4 4",
  open_infantry: "M12 3a2 2 0 1 0 0 4a2 2 0 1 0 0-4z M12 8v7 M8 11h8 M9 21l3-6 3 6",
  open_vehicles: "M3 16h18v4H3z M7 16v-4h8v4 M15 13h6",
  forest: "M7 3l-4 7h3l-3 5h8l-3-5h3z M7 15v5 M17 6l-4 7h3l-3 5h8l-3-5h3z M17 18v3",
  move: "M12 3v18 M3 12h18 M9 6l3-3 3 3 M9 18l3 3 3-3 M6 9l-3 3 3 3 M18 9l3 3-3 3",
  spawn: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M12 8v8 M8 12h8",
  start: "M6 21V3 M6 4h11l-3 4 3 4H6",
};
const BRUSH_ICON = { water: "drop", cover: "cover", block: "movement" };
for (const f of FORMATIONS) {
  ICONS["formation_" + f] = formationOffsets(f, 6).map(([a, b]) => {
    const x = (12 + a * 3.3).toFixed(1), y = (12 - b * 3.3).toFixed(1);
    return `M${x} ${y}m-1.3 0a1.3 1.3 0 1 0 2.6 0a1.3 1.3 0 1 0-2.6 0`;
  }).join(" ");
}

function iconTile(button, icon, label) {
  button.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${ICONS[icon] || ICONS.spawn}"/></svg>`;
  button.append(el("span", { textContent: label }));
  return button;
}

function chipOf(label, title, pressed, onClick) {
  const chip = el("button", { type: "button", className: "chip", textContent: label, title: title || "" });
  chip.setAttribute("aria-pressed", String(pressed));
  chip.addEventListener("click", onClick);
  return chip;
}

function brushKind(name) {
  return (DOCK.find(([, brushes]) => brushes && brushes.includes(name)) || ["terrain"])[0];
}

function kindName(kind) {
  const w = mv.words;
  return { terrain: w.dock_terrain, water: w.brush_water, cover: w.brush_cover, movement: w.dock_movement, roads: w.dock_roads,
    scenario: w.scen_show }[kind] || w[`scenery_${kind}`] || kind;
}

// The kind open: the brush's, the place kind's, or the scenario's; null while just looking around.
function dockKind() {
  if (mv.brush.on) return brushKind(mv.brush.name);
  if (road.on) return "roads";
  if (mv.place.on) return mv.place.group;
  return dock.scenario || scen.tool ? "scenario" : null;
}

function openKind(kind) {
  if (dockKind() === kind) { lookAround(); return; }  // the open kind again closes it
  const brushes = (DOCK.find(([k]) => k === kind) || [])[1];
  if (brushes) { pickBrush(dock.last[kind] || brushes[0]); return; }
  if (kind === "roads") { setRoadMode(true); return; }
  if (kind === "scenario") {
    lookAround();
    dock.scenario = true;
    renderDock();
    return;
  }
  mv.place.group = kind;
  mv.place.lineStart = null;
  showPlaceGuide(null);
  placeOptions();
  setPlaceMode(true);
}

// The bar's tiles, again when the words change.
function renderDockBar() {
  const w = mv.words;
  iconTile($("brush-look"), "look", w.brush_look).title = w.tip_look;
  $("dock-kinds").replaceChildren(...DOCK.map(([kind]) => {
    const tile = iconTile(el("button", { type: "button", className: "dock-tile", title: w[`tip_dock_${kind}`] || "" }),
      kind, kindName(kind));
    tile.dataset.kind = kind;
    tile.addEventListener("click", () => openKind(kind));
    return tile;
  }));
  renderDock();
}

function renderDock() {
  const w = mv.words, kind = dockKind();
  $("brush-look").setAttribute("aria-pressed", String(!kind));
  for (const tile of $("dock-kinds").children) tile.setAttribute("aria-pressed", String(tile.dataset.kind === kind));
  $("dock-tray").classList.toggle("hidden", !kind);
  $("tray-brush").classList.toggle("hidden", !(kind && (DOCK.find(([k]) => k === kind) || [])[1]));
  $("tray-place").classList.toggle("hidden", !PLACEABLE.includes(kind));
  $("tray-scen").classList.toggle("hidden", kind !== "scenario");
  $("tray-roads").classList.toggle("hidden", kind !== "roads");
  $("tray-title").textContent = kind ? kindName(kind) : "";
  $("tray-tip").textContent = kind ? w[`tip_dock_${kind}`] || "" : "";
}

// --- new roads, Cities: Skylines style (maps/<map>/roads.toml; StudioApi.road_add, rusemod.roadnet). Straight: click
// where it starts, then where it ends; Curve: the start, the bend, the end; Freeform: click along the way, then
// double-click or Enter (or Finish). An end near a road snaps onto it (a ring shows where) and joins it. New roads
// are drawn as blue ribbons, the way the game draws a supply route. Proven in the game (2026-09-30): supply routes
// follow a road added this way. Not painted on the ground yet (PLAN A6). ---
const ROAD_TOOLS = ["straight", "curve", "free"];
const ROAD_SNAP = 15000;    // map units (about 58 m): an end this near a road snaps onto it
const ROAD_WIDTH = 1800;    // map units drawn (about 7 m)
const ROAD_SAMPLE = 2000;   // map units between the points of a road's saved line
const road = { on: false, tool: "straight", pts: [], mine: [], mod: null, mesh: null, preview: null, snap: null,
  cursor: null };

// Where the map's own roads run, as points (for snapping), from their pieces.
function roadSamples() {
  const P = roads.pieces || [], out = [];
  for (let o = 0; o < P.length; o += 8) {
    for (let s = 0; s <= 4; s++) {
      const t = s / 4, u = 1 - t, a = u * u * u, b = 3 * u * u * t, c = 3 * u * t * t, d = t * t * t;
      out.push(a * P[o] + b * P[o + 2] + c * P[o + 4] + d * P[o + 6], a * P[o + 1] + b * P[o + 3] + c * P[o + 5] + d * P[o + 7]);
    }
  }
  for (const r of road.mine) for (const [x, y] of r.points) out.push(x, y);
  return out;
}

// The point to use for a click at (x, y): on the nearest road within ROAD_SNAP, or where it was clicked.
function roadSnap(x, y) {
  if (!road.samples) road.samples = roadSamples();
  const S = road.samples;
  let best = ROAD_SNAP * ROAD_SNAP, at = -1;
  for (let i = 0; i < S.length; i += 2) {
    const d = (S[i] - x) ** 2 + (S[i + 1] - y) ** 2;
    if (d < best) { best = d; at = i; }
  }
  return at < 0 ? { x, y, snapped: false } : { x: S[at], y: S[at + 1], snapped: true };
}

// A road's line from its clicks (and the pointer, while it's being drawn), as points about ROAD_SAMPLE apart.
function roadLine(tool, pts) {
  if (pts.length < 2) return pts.slice();
  let line;
  if (tool === "curve" && pts.length >= 3) {  // a quadratic curve: the start, the bend it's pulled toward, the end
    const [p0, p1, p2] = pts, n = 24;
    line = [];
    for (let k = 0; k <= n; k++) {
      const t = k / n, u = 1 - t;
      line.push([u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0], u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]]);
    }
  } else if (tool === "free" && pts.length >= 3) {  // a smooth line through every click (Catmull-Rom)
    line = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      for (let k = 0; k < 12; k++) {
        const t = k / 12, t2 = t * t, t3 = t2 * t;
        const f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t2 + (-a + 3 * b - 3 * c + d) * t3);
        line.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
      }
    }
    line.push(pts[pts.length - 1]);
  } else {
    line = pts.slice();
  }
  const out = [line[0]];  // the same points, about ROAD_SAMPLE apart
  for (let i = 1; i < line.length; i++) {
    const [ax, ay] = out[out.length - 1], [bx, by] = line[i], d = Math.hypot(bx - ax, by - ay);
    const n = Math.floor(d / ROAD_SAMPLE);
    for (let k = 1; k <= n; k++) out.push([ax + (bx - ax) * k / (n + 1), ay + (by - ay) * k / (n + 1)]);
    if (d > 1) out.push([bx, by]);
  }
  return out.map(([x, y]) => [Math.round(x), Math.round(y)]);
}

// Blue ribbons on the ground for `lines` (each a list of [x, y]), as one mesh.
function roadRibbon(lines, mesh, color, opacity) {
  const gl = mv.gl, { THREE } = gl, grid = makeGrid(mv.edit), pos = [], half = ROAD_WIDTH / 2;
  for (const line of lines) {
    for (let i = 0; i + 1 < line.length; i++) {
      const [ax, ay] = line[i], [bx, by] = line[i + 1], len = Math.hypot(bx - ax, by - ay) || 1;
      const nx = -(by - ay) / len * half, ny = (bx - ax) / len * half;
      const corner = (x, y) => [x * SCALE, (groundAt(grid, x, y) + ROAD_LIFT) * SCALE, y * SCALE];
      const a1 = corner(ax + nx, ay + ny), a2 = corner(ax - nx, ay - ny), b1 = corner(bx + nx, by + ny), b2 = corner(bx - nx, by - ny);
      pos.push(...a1, ...a2, ...b1, ...b1, ...a2, ...b2);
    }
  }
  if (!mesh) {
    // drawn over the ground like the game's own supply-route line: a strip seated at its points sinks into a bump
    // between them (the owner's screenshot, 2026-09-30), so depth is ignored and the ribbon always shows
    mesh = new THREE.Mesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial({ color, transparent: true, opacity,
      depthWrite: false, depthTest: false, side: THREE.DoubleSide }));
    mesh.renderOrder = 5;
    mesh.frustumCulled = false;
    gl.scene.add(mesh);
  }
  mesh.geometry.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
  mesh.visible = pos.length > 0;
  return mesh;
}

// A length in the game's metres (METRE map units each): "84 m", "1.2 km".
function roadMetres(units) {
  const m = units / METRE;
  return m < 1000 ? `${Math.round(m)} m` : `${(m / 1000).toFixed(1)} km`;
}

function lineLength(line) {
  let n = 0;
  for (let i = 1; i < line.length; i++) n += Math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1]);
  return n;
}

// The road being drawn, measured beside the pointer (Cities: Skylines style): the whole road so far along its line,
// and for a freeform road the straight part from the last click too. Hidden when nothing is being drawn.
function showRoadLength(ev) {
  const tag = $("road-length");
  if (!ev || !road.on || !road.pts.length || !road.cursor) { tag.classList.add("hidden"); return; }
  const total = lineLength(roadLine(road.tool, road.pts.concat([road.cursor])));
  tag.replaceChildren(el("b", {}, roadMetres(total)));
  if (road.tool === "free" && road.pts.length >= 2) {
    const [lx, ly] = road.pts[road.pts.length - 1];
    tag.append(" · " + fill(mv.words.road_part, { len: roadMetres(Math.hypot(road.cursor[0] - lx, road.cursor[1] - ly)) }));
  }
  const box = tag.parentElement.getBoundingClientRect();
  tag.style.left = `${Math.round(ev.clientX - box.left + 16)}px`;
  tag.style.top = `${Math.round(ev.clientY - box.top + 18)}px`;
  tag.classList.remove("hidden");
}

function drawModRoads() {
  if (!mv.gl || !mv.edit) return;
  road.mesh = roadRibbon(road.mine.map((r) => r.points), road.mesh, 0x3f73d8, 0.8);
  drawRoadPreview();
}

function drawRoadPreview() {
  const gl = mv.gl;
  if (!gl || !mv.edit) return;
  const pts = road.on ? road.pts.concat(road.cursor ? [road.cursor] : []) : [];
  road.preview = roadRibbon(pts.length >= 2 ? [roadLine(road.tool, pts)] : [], road.preview, 0x8fb4ff, 0.55);
  const ring = gl.startRing, snap = road.on && road.snap;
  if (ring) {
    ring.visible = Boolean(snap);
    if (snap) {
      const r = ROAD_SNAP * SCALE * 0.35, grid = makeGrid(mv.edit);
      ring.position.set(snap.x * SCALE, (groundAt(grid, snap.x, snap.y) + ROAD_LIFT) * SCALE, snap.y * SCALE);
      ring.scale.set(r, r, r);
    }
  }
  gl.draw();
}

function dropModRoads() {
  for (const k of ["mesh", "preview"]) {
    if (road[k]) { mv.gl.scene.remove(road[k]); road[k].geometry.dispose(); road[k].material.dispose(); }
    road[k] = null;
  }
  Object.assign(road, { mine: [], pts: [], samples: null, snap: null, cursor: null });
}

async function loadModRoads(pack, ask) {
  const res = await mv.api.roads(pack);
  if (ask !== mv.ask || !mv.edit) return;
  road.mine = res.roads;
  road.mod = res.mod;
  road.samples = null;
  drawModRoads();
  renderRoadTray();
}

function roadNote(text, kind) {
  const n = $("road-note");
  n.textContent = text || "";
  n.className = "small" + (kind === "error" ? " error-text" : "");
}

function renderRoadTray() {
  const w = mv.words;
  $("road-tools").replaceChildren(...ROAD_TOOLS.map((t) => {
    const tile = iconTile(el("button", { type: "button", className: "tool-tile", title: w["tip_road_" + t] || "" }), "road_" + t, w["road_" + t] || t);
    tile.setAttribute("aria-pressed", String(road.on && road.tool === t));
    tile.addEventListener("click", () => { road.tool = t; road.pts = []; setRoadMode(true); });
    return tile;
  }));
  $("road-help").textContent = w["road_help_" + road.tool] || "";
  $("road-finish").textContent = w.road_finish;
  $("road-finish").title = w.tip_road_finish;
  $("road-finish").classList.toggle("hidden", road.tool !== "free");
  $("road-finish").disabled = road.pts.length < 2;
  $("road-undo").textContent = w.brush_undo;
  $("road-undo").title = w.tip_road_undo;
  $("road-undo").disabled = !road.mine.length;
  const all = road.mine.reduce((n, r) => n + lineLength(r.points), 0);
  $("road-count").textContent = road.mine.length
    ? fill(w.road_count, { n: road.mine.length }) + " · " + fill(w.road_total, { len: roadMetres(all) }) : "";
  if (!$("road-note").textContent || !$("road-note").classList.contains("error-text")) roadNote(w.road_note);
}

// Road mode off, without redrawing the rest (the other tools turn it off as they turn on).
function stopRoad() {
  if (!road.on && !road.pts.length) return;
  Object.assign(road, { on: false, pts: [], snap: null, cursor: null });
  showRoadLength(null);
  drawRoadPreview();
}

function setRoadMode(on) {
  if (on) {
    if (mv.brush.on) setBrushMode(false);
    if (mv.place.on) setPlaceMode(false);
    if (scen.tool) { scen.tool = null; scen.selected = null; renderScenTools(); drawScenario(); }
    dock.scenario = false;
    road.on = true;
    if (!road.mod) roadNote(mv.words.no_mod, "error");
  } else stopRoad();
  pointerMode();
  renderRoadTray();
  renderDock();
  drawRoads();
  drawRoadPreview();
}

async function finishRoad() {
  const pts = road.pts, pack = mv.current;
  road.pts = [];
  road.cursor = null;
  showRoadLength(null);
  if (pts.length < 2) { drawRoadPreview(); return; }
  const line = roadLine(road.tool, pts);
  drawRoadPreview();
  try {
    await mv.api.road_add(pack, line);
    if (pack !== mv.current) return;
    road.mine.push({ points: line, join: 3000 });
    road.samples = null;  // the new road's points snap too
    drawModRoads();
    renderRoadTray();
    roadNote(mv.words.road_note);
  } catch (err) { roadNote((err && err.message) || String(err), "error"); }
}

async function undoRoad() {
  const pack = mv.current;
  if (!road.mine.length) return;
  try {
    const res = await mv.api.road_undo(pack, 1);
    if (pack !== mv.current) return;
    road.mine.splice(road.mine.length - res.removed, res.removed);
    road.samples = null;
    drawModRoads();
    renderRoadTray();
  } catch (err) { roadNote((err && err.message) || String(err), "error"); }
}

// A click while drawing a road: the next point (snapped); Straight ends at its second, Curve at its third.
function roadPointerDown(ev) {
  if (!road.on || ev.button !== 0 || !mv.gl.ground || !mv.edit) return;
  ev.preventDefault();
  if (!road.mod) { roadNote(mv.words.no_mod, "error"); return; }
  const hit = hitGround(ev);
  if (!hit) return;
  const p = roadSnap(hit.x / SCALE, hit.z / SCALE);
  road.pts.push([p.x, p.y]);
  const need = road.tool === "straight" ? 2 : road.tool === "curve" ? 3 : Infinity;
  if (road.pts.length >= need) finishRoad();
  else { renderRoadTray(); drawRoadPreview(); showRoadLength(ev); }
}

function roadPointerMove(ev) {
  const hit = hitGround(ev);
  if (!hit) { showRoadLength(null); return; }
  const p = roadSnap(hit.x / SCALE, hit.z / SCALE);
  road.snap = p.snapped ? p : null;
  road.cursor = [p.x, p.y];
  drawRoadPreview();
  showRoadLength(ev);
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
  const all = Object.keys(BRUSHES), kind = brushKind(b.name);
  $("brush-list").replaceChildren(...DOCK.find(([k]) => k === kind)[1].map((name) => {
    const i = all.indexOf(name);
    const tile = iconTile(el("button", { type: "button", className: "tool-tile",
      title: (w["tip_brush_" + name] ? w["tip_brush_" + name] + " " : "") + (i < 10 ? fill(w.tip_brush || "", { n: (i + 1) % 10 }) : "") }),
    ICONS[name] ? name : BRUSH_ICON[name] || kind, w["brush_" + name] || name);
    tile.setAttribute("aria-pressed", String(b.on && b.name === name));
    tile.addEventListener("click", () => pickBrush(name));
    return tile;
  }));
  const set = settingsOf(b.name);
  $("brush-size").value = set.size;
  $("brush-strength").value = set.strength;
  $("brush-strength-row").classList.toggle("hidden", ["cover", "town", "block", "open", "forest"].includes(BRUSHES[b.name][0]));
  showOverlays();
  $("map-help").textContent = b.on ? w.brush_help : w.map_help;
  showCount();
}

function pickBrush(name) {
  const b = mv.brush;
  if (b.name !== name) cancelRamp();
  b.name = name;
  dock.last[brushKind(name)] = name;
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
  if (on) { dock.scenario = false; stopRoad(); }
  if (on) { mv.place.on = false; if (scen.tool) { scen.tool = null; scen.selected = null; renderScenTools(); drawScenario(); } }
  if (!on) cancelRamp();
  pointerMode();
  renderBrushes();
  renderPlace();
  renderDock();
}

// Brushing or placing: the left button works on the ground (the middle one turns the view); else it turns the view.
function pointerMode() {
  const gl = mv.gl;
  if (!gl) return;
  const busy = mv.brush.on || mv.place.on || Boolean(scen.tool) || road.on, M = gl.THREE.MOUSE;
  // the middle button turns the view in every mode (the wheel zooms), so the hand never has to change buttons
  gl.controls.mouseButtons = busy ? { LEFT: null, MIDDLE: M.ROTATE, RIGHT: M.PAN }
                                  : { LEFT: M.ROTATE, MIDDLE: M.ROTATE, RIGHT: M.PAN };
  if (!mv.brush.on && gl.ring) { gl.ring.visible = false; gl.draw(); }
  if (busy) $("scenery-hover").textContent = "";
  gl.renderer.domElement.style.cursor = busy ? "crosshair" : "";
}

// The world numbers of a new stroke, from the brush picked and its sliders.
function newStroke(x, y, level, end) {
  const name = mv.brush.name, [kind] = BRUSHES[name], set = settingsOf(name);
  const [, , z0, , , z1] = mv.edit.bounds;
  const s = { brush: kind === "forest" ? "cover" : name, x, y, radius: brushRadius(name) };  // a forest's cover
  if (kind === "add") s.height = lift(set.strength, z0, z1);
  if (kind === "level") { s.level = level; s.weight = name === "plateau" ? 1 : set.strength / 100; }
  if (kind === "smooth") s.weight = set.strength / 100;
  if (kind === "ramp") { s.level = level; s.weight = set.strength / 100; s.x2 = end.x; s.y2 = end.y; s.level2 = end.z; }
  if (kind === "water") s.level = level;
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
  const r = brushRadius(mv.brush.name) * SCALE, lift = r * 0.02;
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
  if (group.forest) {  // the trees in the same circle, scattered as Place's Area scatters them
    scatter(group, x, y, group.forest);
    const p = mv.place, keep = p.objects;
    p.objects = keep.concat(group.objects);
    drawPlaced();
    p.objects = keep;
    return;
  }
  const ed = mv.edit;
  redraw(false, !ed.normalsAt || performance.now() - ed.normalsAt > 150);
}

// The trees a Forest stroke places: the Place panel's tree when a tree is picked there, else the map's most used one
// (a map takes only the types it already uses); null when the map has none.
function forestOf(radius) {
  const p = mv.place, rows = ((mv.scenery.data && mv.scenery.data.palette) || []).filter((r) => r[2] === "vegetation");
  const picked = p.group === "vegetation" && rows.some((r) => r[0] === p.type) ? p.type : null;
  const type = picked || (rows.length ? rows.reduce((a, b) => ((b[4] || 0) > (a[4] || 0) ? b : a))[0] : null);
  if (!type) return null;
  return { type, r: radius, gap: spacingOf("vegetation") * METRE, make: (x, y) => ({ type, x: Math.round(x), y: Math.round(y),
    turn: Math.floor(Math.random() * 360), size: Math.round((picked ? p.size : 1) * (0.85 + Math.random() * 0.3) * 100) / 100,
    solid: true }) };
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
  const pack = mv.current, trees = g.objects || [];
  let placed = false;
  try {
    if (trees.length) {  // a Forest stroke: its trees, then its cover; both or neither
      await mv.api.scenery_add(pack, trees);
      placed = true;
    }
    await mv.api.terrain_add(pack, g.strokes);
    if (pack !== mv.current) return;
    if (g.objects) {
      for (const o of trees) forestTrees.add(o);
      mv.place.objects.push(...trees);
      mv.brush.groups.push({ n: g.strokes.length, objects: trees });
      drawPlaced();
      renderPlace();
    } else {
      mv.brush.groups.push(g.strokes.length);
    }
    showCount();
    brushNote(g.objects ? fill(mv.words.forest_done, { n: trees.length.toLocaleString() }) : mv.words.brush_note);
  } catch (err) {
    if (placed) { try { await mv.api.scenery_undo(pack, trees.length, trees); } catch (_) { /* said below */ } }
    if (pack !== mv.current) return;
    mv.brush.strokes.splice(g.start, g.strokes.length);  // not saved: take it off the view again
    if (g.objects) drawPlaced();
    reapply();
    showCount();
    brushNote((err && err.message) || String(err), "error");
  }
}

// Undo takes back the last stroke or drag; a Forest stroke's trees go with its cover.
async function undoStroke() {
  const b = mv.brush, pack = mv.current;
  if (!b.mod || !b.strokes.length || b.painting) return;
  const last = b.groups.length ? b.groups.pop() : 1, n = typeof last === "number" ? last : last.n;
  try {
    const res = await mv.api.terrain_undo(pack, n);
    if (pack !== mv.current) return;
    b.strokes.splice(b.strokes.length - res.removed, res.removed);
    if (last.objects && last.objects.length) {
      await mv.api.scenery_undo(pack, last.objects.length, last.objects);
      if (pack !== mv.current) return;
      takeOff(last.objects);
      renderPlace();
    }
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
    // a plateau's top and a lake's surface sit Strength above the ground clicked; Level and Flatten take its height
    const level = kind === "water" || name === "plateau" ? z + lift(set.strength, z0, z1) : kind === "level" ? z : 0;
    if (kind === "town") {  // one click: cover circles around the town's buildings, saved as one group
      const strokes = townStrokes(x, y);
      if (!strokes.length) { brushNote(mv.words.town_none, "error"); return; }
      const group = { strokes: [], last: null, stamp: true, start: mv.brush.strokes.length };
      for (const s of strokes) { group.strokes.push(s); mv.brush.strokes.push(s); overlayDab(s); }
      mv.brush.painting = group;
      const saved = mv.brush.groups.length;
      finishStroke().then(() => { if (mv.brush.groups.length > saved) brushNote(fill(mv.words.town_done, { n: strokes.length })); });
      return;
    }
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
    if (kind === "forest") {  // trees and cover from one stroke
      group.forest = forestOf(brushRadius(name));
      if (!group.forest) { brushNote(mv.scenery.data ? mv.words.forest_no_trees : mv.words.scenery_loading, "error"); return; }
      group.objects = [];
    }
    mv.brush.painting = group;
    dab(group, x, y);
    if (stamp) finishStroke();
    else canvas.setPointerCapture(ev.pointerId);
  });
  for (const type of ["pointerup", "pointercancel"]) {
    canvas.addEventListener(type, () => { if (mv.brush.painting) finishStroke(); });
  }
  canvas.addEventListener("pointerdown", scenPointerDown);
  canvas.addEventListener("pointerdown", roadPointerDown);
  let roadMove = null, roadFrame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    if (!road.on) return;
    roadMove = ev;
    if (!roadFrame) roadFrame = requestAnimationFrame(() => { roadFrame = 0; if (road.on && roadMove) roadPointerMove(roadMove); });
  });
  canvas.addEventListener("dblclick", () => {  // Freeform ends with a double-click (its two clicks add one point)
    if (!road.on || road.tool !== "free") return;
    const p = road.pts;
    if (p.length >= 2 && Math.hypot(p[p.length - 1][0] - p[p.length - 2][0], p[p.length - 1][1] - p[p.length - 2][1]) < ROAD_SAMPLE) p.pop();
    finishRoad();
  });
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
  let spawnMove = null, spawnFrame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    if (scen.tool !== "spawn") return;
    spawnMove = ev;
    if (!spawnFrame) spawnFrame = requestAnimationFrame(() => { spawnFrame = 0; showFormation(spawnMove && hitGround(spawnMove)); });
  });
  canvas.addEventListener("pointerleave", () => showFormation(null));
  let hoverEv = null, hoverFrame = 0;
  // Looking around: say what the pointer is on. Only then: the ray is tested against every drawn object (tens of
  // thousands on a real map), which is too slow to run under a painting or placing pointer.
  canvas.addEventListener("pointermove", (ev) => {
    if (mv.brush.on || mv.place.on || (!mv.scenery.data && !scen.group)) return;
    hoverEv = ev;
    if (!hoverFrame) hoverFrame = requestAnimationFrame(() => {
      hoverFrame = 0;
      const s = scenarioAt(hoverEv);
      const t = s ? null : sceneryAt(hoverEv);
      $("scenery-hover").textContent = s || (t ? `${t[0]} · ${t[2] || t[1]}` : "");
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

// The map list's filter: every map, or those the game offers as skirmish maps, Operations, campaign chapters, demos
// or test setups (rusemod.terrain: from its menus; a map can be several). Kept by the Studio (prefs "view").
const MAP_KINDS = ["all", "skirmish", "operation", "campaign", "demo", "test"];

function renderKindPick() {
  const w = mv.words, pick = $("map-kind");
  pick.replaceChildren(...MAP_KINDS.map((k) => {
    const n = k === "all" ? mv.maps.length : mv.maps.filter((m) => (m.kinds || []).includes(k)).length;
    return el("option", { value: k, textContent: `${k === "all" ? w.maps_all : w["scen_kind_" + k] || k} (${n})` });
  }).filter((o) => o.value === "all" || !o.textContent.endsWith("(0)")));
  pick.value = mv.kind || "all";
  pick.title = w.tip_map_kind || "";
}

function renderList() {
  renderKindPick();
  const shown = mv.kind && mv.kind !== "all" ? mv.maps.filter((m) => (m.kinds || []).includes(mv.kind)) : mv.maps;
  $("map-list").replaceChildren(...shown.map((m) => {
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
  $("map-cover-label").textContent = w.cover_show;
  $("map-cover").parentElement.title = w.tip_cover_show;
  $("map-move-label").textContent = w.move_show;
  $("map-roads-label").textContent = w.roads_show;
  $("map-roads").parentElement.title = w.tip_roads_show;
  $("map-move").parentElement.title = w.tip_move_show;
  $("scen-show-label").textContent = w.scen_show;
  $("scen-show").parentElement.title = w.tip_scen_show;
  if (scen.data) renderScenarioPick();
  $("map-water").title = w.tip_water;
  for (const g of ["building", "prop", "vegetation"]) {
    $(`scenery-${g}-label`).textContent = w[`scenery_${g}`];
    $(`scenery-${g}`).title = w.tip_show_group;
  }
  showSceneryStats();
  renderPlace();
  $("map-help").textContent = mv.brush.on ? w.brush_help : w.map_help;
  renderKeys();
  $("brush-size-label").textContent = w.brush_size;
  $("brush-size").title = w.tip_brush_size;
  $("brush-strength-label").textContent = w.brush_strength;
  $("brush-strength").title = w.tip_brush_strength;
  $("brush-undo").textContent = w.brush_undo;
  $("brush-undo").title = w.tip_brush_undo;
  $("brush-clear").textContent = w.brush_clear;
  $("brush-clear").title = w.tip_brush_clear;
  $("brush-clear-yes").textContent = w.remove_all;
  $("brush-clear-yes").title = w.tip_remove_all;
  $("brush-clear-no").textContent = w.cancel;
  $("brush-clear-no").title = w.tip_cancel;
  if (!mv.current) $("map-pick").textContent = w.pick_map;
  foldMaps(Boolean(mv.folded));
  renderBrushes();
  renderScenTools();
  renderRoadTray();
  renderDockBar();
  renderPanelWords();
}

// --- keys, while the map view is open and no text box has the focus ---
// W/S and A/D (or the arrows) slide the camera forward, back, left and right as it looks (turned with Q/E, W still
// goes up the screen); Q/E turn it around the point it looks at; R/F zoom. Held keys move smoothly, frame by frame, at a speed
// scaled to the map (and to the zoom, so a close view doesn't fly), three times as fast with Shift. The tool keys
// do what the buttons do (the tooltips name them).
// The keys can be changed (the Keys panel under the help line, kept in this browser's storage): each action has one
// physical key (e.code, so W A S D are the same places on an AZERTY keyboard); the arrows always move, Esc always
// looks around, Ctrl+Z always undoes, and the digits always pick brushes.
const KEY_DEFAULTS = { forward: "KeyW", back: "KeyS", left: "KeyA", right: "KeyD", turn_left: "KeyQ", turn_right: "KeyE",
  zoom_in: "KeyR", zoom_out: "KeyF", brush: "KeyB", place: "KeyP", size_down: "BracketLeft", size_up: "BracketRight",
  strength_down: "Minus", strength_up: "Equal" };
const ARROWS = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0] };
const MOVES = { forward: [0, -1], back: [0, 1], left: [-1, 0], right: [1, 0] };
const HELD_ACTIONS = ["forward", "back", "left", "right", "turn_left", "turn_right", "zoom_in", "zoom_out"];
const keys = { down: new Set(), shift: false, frame: 0, at: 0, map: loadKeys(), by: {}, arming: null };
let MOVE = {}, HELD = new Set();
rebuildKeys();

function loadKeys() {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem("studio.keys") || "{}") || {}; } catch { saved = {}; }
  const map = { ...KEY_DEFAULTS };
  for (const a of Object.keys(map)) if (a in saved && (saved[a] === null || typeof saved[a] === "string")) map[a] = saved[a];
  return map;
}

function saveKeys() {
  try { localStorage.setItem("studio.keys", JSON.stringify(keys.map)); } catch { /* private window: fine */ }
  if (mv.api && mv.api.set_pref) mv.api.set_pref("keys", keys.map).catch(() => {});  // kept by the Studio too
}

// The keys the Studio kept (settings.json): they outlive a restart, an update and a reinstall, which the window's
// own storage doesn't.
async function loadKeptKeys() {
  if (!mv.api || !mv.api.prefs) return;
  try {
    const kept = (await mv.api.prefs()).keys;
    if (!kept || typeof kept !== "object") return;
    const map = { ...KEY_DEFAULTS };
    for (const a of Object.keys(map)) if (a in kept && (kept[a] === null || typeof kept[a] === "string")) map[a] = kept[a];
    keys.map = map;
    rebuildKeys();
    renderKeys();
  } catch { /* the window's own copy stays */ }
}

// MOVE (code -> direction) and HELD (codes that act while held) from the current keys; `by` finds an action by code.
function rebuildKeys() {
  MOVE = { ...ARROWS };
  HELD = new Set(Object.keys(ARROWS));
  keys.by = {};
  for (const [action, code] of Object.entries(keys.map)) {
    if (!code) continue;
    keys.by[code] = action;
    if (action in MOVES) MOVE[code] = MOVES[action];
    if (HELD_ACTIONS.includes(action)) HELD.add(code);
  }
}

function codeOf(action) { return keys.map[action] || null; }

// A key's name for the screen, from its physical code.
function keyName(code) {
  if (!code) return "\u2014";
  const fixed = { BracketLeft: "[", BracketRight: "]", Minus: "-", Equal: "=", Space: "Space", Comma: ",", Period: ".",
    Slash: "/", Backslash: "\\", Semicolon: ";", Quote: "'", Backquote: "`", Tab: "Tab", Enter: "Enter",
    Backspace: "Backspace", Delete: "Del", Insert: "Ins", Home: "Home", End: "End", PageUp: "PgUp", PageDown: "PgDn",
    ArrowUp: "\u2191", ArrowDown: "\u2193", ArrowLeft: "\u2190", ArrowRight: "\u2192", NumpadAdd: "Num +",
    NumpadSubtract: "Num -", NumpadMultiply: "Num *", NumpadDivide: "Num /", NumpadDecimal: "Num .", NumpadEnter: "Num Enter" };
  if (fixed[code]) return fixed[code];
  let m;
  if ((m = /^Key([A-Z])$/.exec(code))) return m[1];
  if ((m = /^Digit(\d)$/.exec(code))) return m[1];
  if ((m = /^Numpad(\d)$/.exec(code))) return "Num " + m[1];
  return code;
}

// The help line, from the keys as they are.
function keysLine() {
  const w = mv.words, k = (a) => keyName(codeOf(a));
  return [fill(w.keys_move, { k: `${k("forward")} ${k("left")} ${k("back")} ${k("right")}` }),
    fill(w.keys_turn, { k: `${k("turn_left")} ${k("turn_right")}` }), fill(w.keys_zoom, { k: `${k("zoom_in")} ${k("zoom_out")}` }),
    w.keys_fast, w.keys_brushes, fill(w.keys_brush, { k: k("brush") }), fill(w.keys_place, { k: k("place") }), w.keys_look,
    w.keys_undo, fill(w.keys_size, { k: `${k("size_down")} ${k("size_up")}` }),
    fill(w.keys_strength, { k: `${k("strength_down")} ${k("strength_up")}` })].join(" \u00b7 ");
}

// The Keys panel: every action with its key; click a key, press another. A key taken from another action leaves
// that one without a key. Defaults puts them all back.
function renderKeys() {
  const w = mv.words, line = $("map-keys"), panel = $("keys-panel");
  if (!w.keys_head) return;  // the words come with the map view or Settings
  const change = el("button", { type: "button", className: "link", textContent: w.keys_change, title: w.tip_keys_change });
  change.addEventListener("click", () => { keys.arming = null; if (window.openSettings) window.openSettings("keys"); });
  line.replaceChildren(el("span", { textContent: w.keys_head + keysLine() }), " ", change);
  panel.replaceChildren();
  const rows = el("div", { className: "keys-rows" });
  for (const action of Object.keys(KEY_DEFAULTS)) {
    const key = el("button", { type: "button", className: "key" + (keys.arming === action ? " arming" : ""),
      textContent: keys.arming === action ? w.keys_press : keyName(codeOf(action)) });
    key.setAttribute("aria-label", w["key_" + action]);
    key.addEventListener("click", () => { keys.arming = keys.arming === action ? null : action; renderKeys(); });
    rows.append(el("span", { className: "small", textContent: w["key_" + action] }), key);
  }
  const reset = el("button", { type: "button", className: "small ghost", textContent: w.keys_reset });
  reset.addEventListener("click", () => { keys.map = { ...KEY_DEFAULTS }; keys.arming = null; saveKeys(); rebuildKeys(); renderKeys(); });
  panel.append(el("div", { className: "muted small", textContent: w.keys_fixed }), rows, el("div", { className: "actions" }, reset));
}

function armKey(e) {
  const action = keys.arming;
  if (e.type !== "keydown") return;
  e.preventDefault();
  if (e.key === "Escape") { keys.arming = null; renderKeys(); return; }
  if (/^(Shift|Control|Alt|Meta)/.test(e.code) || !e.code) return;  // a modifier alone isn't a key
  const other = keys.by[e.code];
  if (other && other !== action) keys.map[other] = null;
  keys.map[action] = e.code;
  keys.arming = null;
  saveKeys();
  rebuildKeys();
  renderKeys();
}

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
  const has = (a) => keys.down.has(codeOf(a));
  const turn = (has("turn_left") ? 1 : 0) - (has("turn_right") ? 1 : 0);
  if (turn) offset.applyAxisAngle(new THREE.Vector3(0, 1, 0), turn * 1.2 * fast * dt);
  const zoom = (has("zoom_out") ? 1 : 0) - (has("zoom_in") ? 1 : 0);
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
    if (what === "size") {  // fine steps up to 3×, bigger ones above (the build takes up to 50×)
      const step = (dir > 0 ? p.size >= 3 : p.size > 3) ? 0.5 : 0.1;
      p.size = Math.round(Math.min(10, Math.max(0.5, p.size + dir * step)) * 10) / 10;
    }
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
  dock.scenario = false;
  stopRoad();
  if (scen.tool) { scen.tool = null; scen.selected = null; pointerMode(); renderScenTools(); drawScenario(); }
  cancelRamp();
  mv.place.lineStart = null;
  showPlaceGuide(null);
  mv.place.on = false;
  setBrushMode(false);
}

function onKey(e) {
  if (keys.arming) { armKey(e); return; }  // choosing a key (in Settings): any key
  if (!mapViewOpen()) return;
  keys.shift = e.shiftKey;
  const held = HELD.has(e.code);
  if (e.type === "keyup") { if (held) keys.down.delete(e.code); return; }
  const ctrl = e.ctrlKey || e.metaKey;
  if (ctrl && !e.altKey && e.code === "KeyZ") {  // the one shortcut that works with a modifier
    if (fieldFocused(false)) return;              // a text box has its own undo
    e.preventDefault();
    if (mv.brush.on) undoStroke(); else if (mv.place.on) undoPlace(); else if (road.on) undoRoad();
    return;
  }
  if (ctrl || e.altKey) return;
  if (e.key === "Escape") {
    if (fieldFocused(true)) { document.activeElement.blur(); return; }  // first out of the box, then back to Look
    if (road.on && road.pts.length) {  // then the road being drawn
      road.pts = [];
      showRoadLength(null);
      renderRoadTray();
      drawRoadPreview();
      return;
    }
    lookAround();
    return;
  }
  if (e.key === "Enter" && road.on && road.tool === "free" && !fieldFocused(false)) { finishRoad(); return; }
  if (held) {
    if (fieldFocused(e.code.startsWith("Arrow"))) return;  // arrows in a slider are the slider's; letters in a box, the box's
    e.preventDefault();  // the arrows would scroll the page
    keys.down.add(e.code);
    if (!keys.frame) { keys.at = performance.now(); keys.frame = requestAnimationFrame(moveStep); }
    return;
  }
  if (fieldFocused(false)) return;
  const digit = /^Digit([0-9])$/.exec(e.code);
  if (digit) { const b = Object.keys(BRUSHES)[(Number(digit[1]) + 9) % 10]; if (b) pickBrush(b); return; }
  const action = keys.by[e.code];
  if (action === "brush") { if (mv.brush.on) lookAround(); else pickBrush(mv.brush.name); }
  else if (action === "place") setPlaceMode(!mv.place.on);
  else if (action === "size_down") nudge("size", -1);
  else if (action === "size_up") nudge("size", 1);
  else if (action === "strength_down") nudge("strength", -1);
  else if (action === "strength_up") nudge("strength", 1);
}

// --- panels the modder arranges (owner: "move windows around ... or at the very least less bulky"): the map panel
// (top left) and the tools (bottom) move by their grip and fold (the map panel to its title, the tools to their bar).
// Where each is and whether it's folded is kept per viewer (browser storage); a double-click on a grip puts that
// panel back. ---
const PANELS = [["map-hud", "hud"], ["map-dock", "dock"]];
const panels = {};

function panelState(key) {
  try { return JSON.parse(localStorage.getItem("studio.panel." + key)) || {}; } catch { return {}; }
}

function savePanel(key) {
  try { localStorage.setItem("studio.panel." + key, JSON.stringify(panels[key].state)); } catch { /* not kept: fine */ }
}

function placePanel(key) {
  const { el: panel, state: s, fold } = panels[key], st = panel.style;
  if (s.left == null) {
    st.left = st.top = st.right = st.bottom = st.transform = "";
    panel.classList.remove("moved");
  } else {
    panel.classList.add("moved");
    Object.assign(st, { left: s.left + "px", top: s.top + "px", right: "auto", bottom: "auto", transform: "none" });
  }
  panel.classList.toggle("folded", Boolean(s.folded));
  const w = mv.words;
  fold.textContent = s.folded ? "▸" : "▾";
  fold.title = (s.folded ? w.tip_panel_unfold : w.tip_panel_fold) || "";
}

function makePanels() {
  for (const [id, key] of PANELS) {
    const panel = $(id), stage = panel.parentElement;
    const grip = el("span", { className: "grip", textContent: "⠿" });
    const fold = el("button", { type: "button", className: "panel-fold" });
    panel.prepend(el("div", { className: "panel-grip" }, grip, fold));
    panels[key] = { el: panel, grip, fold, state: panelState(key) };
    placePanel(key);
    fold.addEventListener("click", () => {
      panels[key].state.folded = !panels[key].state.folded;
      placePanel(key);
      savePanel(key);
    });
    grip.addEventListener("dblclick", () => {  // back where it started
      panels[key].state = { folded: panels[key].state.folded };
      placePanel(key);
      savePanel(key);
    });
    grip.addEventListener("pointerdown", (ev) => {
      ev.preventDefault();
      try { grip.setPointerCapture(ev.pointerId); } catch { /* the drag still follows the grip without it */ }
      const r = panel.getBoundingClientRect(), sr = stage.getBoundingClientRect(), dx = ev.clientX - r.left, dy = ev.clientY - r.top;
      const move = (e) => {  // kept inside the map, with its grip always reachable
        const s = panels[key].state;
        s.left = Math.round(Math.min(Math.max(0, e.clientX - sr.left - dx), Math.max(0, sr.width - 80)));
        s.top = Math.round(Math.min(Math.max(0, e.clientY - sr.top - dy), Math.max(0, sr.height - 40)));
        placePanel(key);
      };
      const up = () => {
        grip.removeEventListener("pointermove", move);
        grip.removeEventListener("pointerup", up);
        savePanel(key);
      };
      grip.addEventListener("pointermove", move);
      grip.addEventListener("pointerup", up);
    });
  }
}

function renderPanelWords() {
  for (const key of Object.keys(panels)) {
    panels[key].grip.title = mv.words.tip_panel_grip || "";
    placePanel(key);
  }
}

let wired = false;
function wire() {
  if (wired) return;
  wired = true;
  makePanels();
  $("map-detail").addEventListener("click", () => {
    mv.lod = mv.lod === "lowdef" ? "highdef" : "lowdef";
    renderWords();
    if (mv.current) show(mv.current, true);
  });
  $("map-kind").addEventListener("change", (e) => {
    mv.kind = e.target.value;
    renderList();
    saveView();
  });
  $("map-cover").addEventListener("change", (e) => {
    cover.show = e.target.checked;
    showOverlays();
  });
  $("map-roads").addEventListener("change", (e) => {
    roads.show = e.target.checked;
    drawRoads();
  });
  $("map-move").addEventListener("change", (e) => {
    moves.show = e.target.checked;
    showOverlays();
  });
  $("map-water").addEventListener("change", (e) => {
    mv.water = e.target.checked;
    if (mv.gl && mv.gl.water) { mv.gl.water.visible = mv.water; mv.gl.draw(); }
  });
  $("scen-show").addEventListener("change", (e) => {
    scen.show = e.target.checked;
    if (scen.group) { scen.group.visible = scen.show; mv.gl.draw(); }
  });
  $("scen-pick").addEventListener("change", (e) => {
    scen.pick = Number(e.target.value) || 0;
    scen.selected = null;
    renderScenarioPick();
    drawScenario();
    renderScenTools();
  });
  $("scen-move").addEventListener("click", () => setScenTool("move"));
  $("scen-gap").addEventListener("input", (e) => { scen.gap[scen.kind] = Number(e.target.value); renderScenTools(); });
  $("scen-spawn").addEventListener("click", () => setScenTool("spawn"));
  $("scen-start").addEventListener("click", () => setScenTool("start"));
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
  $("brush-look").addEventListener("click", () => lookAround());
  $("place-undo").addEventListener("click", () => undoPlace());
  $("place-search").addEventListener("input", () => { placeOptions(); if (mv.place.on) placeNote(mv.place.type ? "" : whyNoType(), "error"); });
  $("place-type").addEventListener("change", (e) => {  // picking a type starts placing, as picking a brush starts painting
    mv.place.type = e.target.value;
    if (!mv.place.on) setPlaceMode(true); else placeNote("");
  });
  $("place-turn").addEventListener("input", (e) => { mv.place.turn = Number(e.target.value); renderPlace(); });
  $("place-size").addEventListener("input", (e) => { mv.place.size = Number(e.target.value); renderPlace(); });
  $("place-solid").addEventListener("change", (e) => { mv.place.solid = e.target.checked; });
  $("place-spacing").addEventListener("input", (e) => { mv.place.spacing[mv.place.group] = Number(e.target.value); renderPlace(); });
  $("place-area").addEventListener("input", (e) => { mv.place.area = Number(e.target.value); renderPlace(); });
  $("brush-undo").addEventListener("click", () => undoStroke());
  $("road-finish").addEventListener("click", () => finishRoad());
  $("road-undo").addEventListener("click", () => undoRoad());
  $("maps-fold").addEventListener("click", () => { foldMaps(!mv.folded); saveView(); });
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

// The map list folds away to give the map the room (the button at its top, again to unfold).
function foldMaps(folded) {
  mv.folded = folded;
  $("maps-view").classList.toggle("folded", folded);
  $("maps-fold").textContent = folded ? "»" : "«";
  $("maps-fold").title = folded ? mv.words.tip_maps_show : mv.words.tip_maps_hide;
}

function saveView() {
  if (mv.api && mv.api.set_pref) mv.api.set_pref("view", { map_kind: mv.kind, maps_folded: Boolean(mv.folded) }).catch(() => {});
}

// app.js opens the view when its tab is picked, and passes the words and the language on every language change.
window.MapView = {
  async open(api, words, lang) {
    mv.api = api;
    mv.words = words;
    mv.lang = lang || "base";
    wire();
    loadKeptKeys();
    renderWords();
    if (!mv.maps.length) {
      try {
        try {
          const view = (await api.prefs()).view || {};
          mv.kind = view.map_kind || mv.kind;
          foldMaps(Boolean(view.maps_folded));
        } catch { /* kept nothing */ }
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
    if ((lang || "base") !== mv.lang) scen.units = null;  // the Add unit tool's names: loaded again in the new language
    mv.lang = lang || "base";
    renderWords();
    renderScenTools();
    renderList();
    showTitle();
    if (mv.stats) $("map-stats").textContent = fill(words.map_stats, mv.stats);
  },
  // Settings shows the keys panel even before the map view has opened
  renderKeysPanel(api, words) {
    if (!mv.api) mv.api = api;
    mv.words = words;
    wire();
    renderKeys();
    loadKeptKeys();
  },
  // where the camera is and what it looks at, in scene units (for checking the keys from outside; nothing else)
  camera() {
    const gl = mv.gl;
    if (!gl) return null;
    return { position: gl.camera.position.toArray(), target: gl.controls.target.toArray(), placed: mv.place.objects.length,
      scenario: scen.group ? scen.group.children.map((o) => o.userData.label || o.type) : null };
  },
  // another mod was picked: its strokes on this map (or none) replace the ones drawn
  modChanged() {
    if (mv.current && mv.edit) loadStrokes(mv.current, mv.ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
    if (mv.current && mv.edit) loadPlaced(mv.current, mv.ask).catch((err) => placeNote((err && err.message) || String(err), "error"));
    if (mv.current && mv.edit) loadModRoads(mv.current, mv.ask).catch((err) => roadNote((err && err.message) || String(err), "error"));
  },
};
window.dispatchEvent(new Event("mapview-ready"));
