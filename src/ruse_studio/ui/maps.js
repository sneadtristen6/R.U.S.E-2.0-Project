// The Maps view: the game's maps on the left, one map's ground in 3D on the right, and brushes that reshape it.
// The ground is the map's own visual mesh, lit by the game's own normals and draped
// with the map's overview picture (StudioApi.map_view, rusemod/terrain.py). Brush strokes are saved in the current
// mod's maps/<map>/terrain.toml (StudioApi.terrain_add); this view draws them on the game's ground with the same
// maths as the build (rusemod/brush.py), and "Test in game" builds them into all four files that hold the ground.
// three.js is loaded from the internet (see index.html) the first time the view opens.
const $ = (id) => document.getElementById(id);
const SCALE = 1 / 1000;  // world units to scene units: a standard map is about 1,300 scene units wide
const mv = { api: null, words: {}, lang: "base", maps: [], current: null, lod: "lowdef", water: true, gl: null, ask: 0,
  stats: null, groundTex: {}, edit: null, size: 0,  // size: the map's longer side in scene units (the keys' speed)
  mode: "map",  // the tools the bar holds: "map" or "scenario" (setMode); the other side's things are faded and locked
  // brush: the tool picked, its size and strength per brush (slider values), the strokes on this map (as saved),
  // the size of each group of strokes made this session (for Undo; a Forest stroke's: { n, objects: its trees }), the
  // drag being painted, and the mod saved into. The Erase brush's own: its circles on this map (the scenery file's
  // [[erase]] tables), how many each drag made this session (for its Undo), what new circles take, and what all of
  // them take when the mod is built (StudioApi.scenery_erased; "counting" while that's worked out)
  brush: { on: false, name: "hill", settings: {}, strokes: [], groups: [], painting: null, mod: null, rampStart: null,
    erase: [], eraseGroups: [], eraseWhat: { vegetation: true, prop: true, building: false }, takes: null, takesAsk: 0 },
  // scenery: which groups are shown, the map's scenery (StudioApi.map_scenery) and its drawn shapes per group
  scenery: { show: { building: true, prop: true, vegetation: true }, data: null, meshes: {}, models: {} },
  // placing: on or not, the group and type picked, the next object's turn and size, what the mod places on this map
  place: { on: false, group: "building", type: null, turn: 0, size: 1, solid: true, objects: [], meshes: {}, mod: null,
    // how: one, area, line, grid, box or select; area: the area brush's radius and spacing: per kind, in metres; groups:
    // the objects each click, area, line, grid or box placed this session (for Undo); lineStart: a line's or a grid's
    // first click; grid: a grid's first row once its end is clicked ({ b }); box: a box being dragged ({ a, b });
    // painting: an area being dragged; rows: a grid's or a box's gap between rows, per kind, in metres; roads: Face the
    // roads (kept with the view); seed: the variety of the line, grid or box being made, so its preview is what's placed
    // path: a path being clicked ({ pts }); lastPath: the last one placed (its clicks); width: a path's width per kind
    // (metres; 0 one line); cover: a path of trees hides units (pathCover)
    how: "one", area: 40, spacing: {}, groups: [], lineStart: null, painting: null, grid: null, box: null, rows: {},
    roads: true, seed: 1, path: null, lastPath: null, width: {}, cover: true } };

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
  erase: ["erase", "flat", 1, false, 3, 0],  // the map's own trees and props taken away: scenery.toml [[erase]] circles
  // Map Paint: the ground's picture, not its shape; strength is the opacity (rusemod.groundpaint)
  paint: ["paint", "soft", 1, false, 7, 60],  // a colour from the wheel, the map's own colours or the eyedropper
  stamp: ["stamp", "soft", 1, false, 7, 100],  // the Texture brush: a texture picked, or this map's own ground from a spot
  texture: ["texture", "soft", 1, false, 7, 100],  // (its strokes with a texture picked: never a brush of the dock)
  // one click: the ground the other brushes moved, inside it, painted by its new shape (rusemod.repaint)
  repaint: ["repaint", "soft", 1, true, 3, 0],
};
const WATER = new Set(["water", "drain"]);
const PAINT_KINDS = new Set(["paint", "stamp", "texture"]);  // their sizes grow on a curve (brushRadius)
// finer sizes than the ground brushes' (share of 1%)
const SIZE_UNIT = { cover: 0.25, uncover: 0.25, town: 0.1, block: 0.25, block_infantry: 0.25, block_vehicles: 0.25,
  open: 0.25, open_infantry: 0.25, open_vehicles: 0.25, forest: 0.25, erase: 0.25 };
const ERASE_DEFAULT = ["vegetation", "prop"];  // what a circle takes unless it says (rusemod.scenery.ERASE_DEFAULT)
const ERASE_MAX = 4000000;  // map units a circle's radius may reach (rusemod.scenery.ERASE_MAX)

// A brush's radius in map units: its Size slider as a share of the map's width. Map Paint's grows on a curve instead,
// from a fine line (about 15 m across on a standard map) to a ginormous patch (about 1.3 km across): the owner,
// 2026-10-03, "make like a ginormous patch red, not just a tiny little" one.
const PAINT_SIZE = [0.0015, 1.38];  // the smallest radius as a share of the map's width, and each step's growth
function brushRadius(name) {
  const [x0, , , x1] = mv.edit.bounds, size = settingsOf(name).size;
  if (PAINT_KINDS.has(name)) return (x1 - x0) * PAINT_SIZE[0] * Math.pow(PAINT_SIZE[1], size - 1);
  return size / 100 * (x1 - x0) * (SIZE_UNIT[name] || 1);
}
// A number box beside a tool's slider (the owner, 2026-10-10, "all of them": past the slider's ends, up to what the
// Studio takes): `get` and `set` are the tool's own value, which the slider shows within its range. A paint brush's
// size grows on a curve (brushRadius): 20 already covers a whole map, so its box stops there.
const TYPED = { size: [1, 50], paint: [1, 20], place: [0.05, 50], spacing: [0.5, 1000], area: [5, 5000], gap: [1, 1000] };
function typedBeside(sliderId, [least, most], get, set, tip) {
  const slider = $(sliderId);
  let box = slider.parentElement.querySelector(".typed-number");
  if (!box) {
    box = el("input", { type: "number", className: "typed-number", step: "any" });
    slider.after(box);
    box.addEventListener("change", () => {
      const n = Number(box.value);
      const ok = box.value.trim() !== "" && Number.isFinite(n) && n >= Number(box.min) && n <= Number(box.max);
      box.setAttribute("aria-invalid", String(!ok));
      if (ok) box._set(n); else box.value = String(box._get());
    });
    slider.addEventListener("input", () => { box.value = slider.value; box.setAttribute("aria-invalid", "false"); });
  }
  box._get = get;
  box._set = set;
  box.min = String(least);
  box.max = String(most);
  box.title = fill(mv.words.tip_typed_number || "", { least, most }) + (tip ? " " + tip : "");
  if (document.activeElement !== box) box.value = String(get());
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

// --- brush types (the owner, 2026-10-03: "a couple of different Brush types. In every tool that has a brush"): a stroke
// (or an Erase area) is round, a square whose sides run along (dx, dy), or a line to (x2, y2), with a soft edge (the
// brush's own fall-off) or a hard one; the same rules as rusemod/brush.py's Footprint and edge_weight ---
const HARD_EDGE = 0.85;
function footShape(s) {
  if (s.brush === "ramp" || s.shape === "line") return "line";
  return s.square || s.shape === "square" ? "square" : "round";
}

// (how far out / radius)²: 0 in the middle (on a line), 1 on the edge.
function footT2(s, x, y) {
  const ox = x - s.x, oy = y - s.y, shape = footShape(s);
  if (shape === "square") {
    const dx = s.dx === undefined ? 1 : s.dx, dy = s.dy === undefined ? 0 : s.dy, n = Math.hypot(dx, dy) || 1;
    if (s.length) {  // a rectangle: `length` along dx, dy, `radius` across (brush.Footprint.t2's sums)
      const a = Math.abs(ox * dx + oy * dy) / n / s.length, b = Math.abs(oy * dx - ox * dy) / n / s.radius;
      const m = a > b ? a : b;
      return m * m;
    }
    const m = Math.max(Math.abs(ox * dx + oy * dy), Math.abs(oy * dx - ox * dy)) / n / s.radius;
    return m * m;
  }
  if (shape === "line") return along(s, x, y)[1] / (s.radius * s.radius);
  return (ox * ox + oy * oy) / (s.radius * s.radius);
}

function edgeWeight(edge, shape, t2) {
  if (edge !== "hard" || shape === "crater") return shapeWeight(shape, t2);
  const t = Math.sqrt(t2);
  if (t <= HARD_EDGE) return 1;
  const k = (t - HARD_EDGE) / (1 - HARD_EDGE);
  return 1 - k * k * (3 - 2 * k);
}

function heightAt(s, x, y, z, average) {
  const [kind, shape, sign] = BRUSHES[s.brush], t2 = footT2(s, x, y);
  if (t2 >= 1) return z;
  const p = edgeWeight(s.edge, shape, t2);
  if (kind === "ramp") return z + (s.level + (s.level2 - s.level) * along(s, x, y)[0] - z) * (s.weight * p);
  if (kind === "add") return z + sign * s.height * p;
  if (kind === "level") return z + (s.level - z) * (s.weight * p);
  return z + (average(x, y) - z) * (s.weight * p);
}

// The box round everything a stroke (or Erase area) covers: x min, x max, y min, y max.
function boxOf(s) {
  const shape = footShape(s), r = s.radius;
  if (shape === "line") return [Math.min(s.x, s.x2) - r, Math.max(s.x, s.x2) + r, Math.min(s.y, s.y2) - r, Math.max(s.y, s.y2) + r];
  if (shape === "square") {
    const dx = s.dx === undefined ? 1 : s.dx, dy = s.dy === undefined ? 0 : s.dy, n = Math.hypot(dx, dy) || 1;
    if (s.length) {  // a rectangle: `length` along, `radius` across
      const ex = (Math.abs(dx) * s.length + Math.abs(dy) * r) / n, ey = (Math.abs(dy) * s.length + Math.abs(dx) * r) / n;
      return [s.x - ex, s.x + ex, s.y - ey, s.y + ey];
    }
    const ex = (Math.abs(dx) + Math.abs(dy)) / n * r;  // a square turned any way: its corners' reach on either axis
    return [s.x - ex, s.x + ex, s.y - ex, s.y + ex];
  }
  return [s.x - r, s.x + r, s.y - r, s.y + r];
}

function covers(s, x, y) {
  return footT2(s, x, y) < 1;
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
  const draw = () => { fadeLayers(); fitIcons(); fitSectorTags(); renderer.render(scene, camera); };
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
  // a square brush's outline: four sides (corners 1 out), turned by the brush's angle (showRing)
  const squareRing = new THREE.Mesh(new THREE.RingGeometry(0.955, 1, 4, 1, Math.PI / 4), ring.material);
  squareRing.renderOrder = 10;
  squareRing.visible = false;
  scene.add(squareRing);
  // a ramp being made: a ring where it starts and a line from there to the pointer
  const startRing = ring.clone();
  const guide = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), new THREE.Vector3()]),
    new THREE.LineBasicMaterial({ color: 0xc8a64b, transparent: true, opacity: 0.9, depthTest: false }));
  guide.renderOrder = 10;
  guide.visible = false;
  scene.add(startRing, guide);
  // Map Paint's dab under the pointer, shaded as the build lays it (showShade): a flat square SHADE_SPAN radii across
  const shadeCanvas = el("canvas", { width: SHADE_N, height: SHADE_N });
  const shadeTex = new THREE.CanvasTexture(shadeCanvas);
  shadeTex.colorSpace = THREE.SRGBColorSpace;
  const shade = new THREE.Mesh(new THREE.PlaneGeometry(SHADE_SPAN, SHADE_SPAN),
    new THREE.MeshBasicMaterial({ map: shadeTex, transparent: true, depthTest: false, depthWrite: false }));
  shade.rotation.x = -Math.PI / 2;
  shade.renderOrder = 9;
  shade.visible = false;
  shade.userData = { canvas: shadeCanvas, tex: shadeTex };
  scene.add(shade);
  mv.gl = { THREE, renderer, scene, camera, controls, draw, ground: null, water: null, ring, squareRing, startRing, guide, shade,
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
    // the map's edge: the ground brushes move it (its curtain follows, rusemod.tms); the water brushes leave it
    fixed[i] = qx === 0 || qx === Q || qy === 0 || qy === Q ? 1 : 0;
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
  if (s.brush === "repaint") { repaintSoon(); return; }  // the build paints what moved: asked for (repaintSoon)
  if (!PAINT_KINDS.has(s.brush) && paint.repainted.length) repaintSoon();  // the ground changed under it
  if (PAINTS[s.brush]) { overlayDab(s); return; }  // the cover grid or where units go, not the ground
  if (PAINT_KINDS.has(s.brush)) {  // the ground's picture (Map Paint), not its shape
    if (!(paint.batch && paint.coats.has(s))) paintDab(s);  // (a coat: laid already, under repainted: paintBegin)
    return;
  }
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
    if (!covers(s, ed.wx[i], ed.wy[i])) return;
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
  paintBegin();
  for (const s of mv.brush.strokes) applyStroke(ed, s);
  for (const a of mv.brush.erase) eraseDab(a);
  for (const o of OVERLAYS) {
    o.batch = false;
    overlayDraw(o, 0, o.size - 1, 0, o.size - 1);
  }
  paintEnd();
  redraw(true, true);
  placeScenery();
  if (paint.repainted.length) repaintSoon();  // (an Undo may have taken its Paint by shape stroke off)
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
//   Proven in the game: units plan around a blocked pit (2026-09-30).
// erased, the Erase brush's circles (the scenery file's [[erase]] tables), in red while it's picked: what's in them
//   goes when the mod is built (tinted red, tintScenery). A circle that takes trees also opens its ground to every
//   unit and takes its cover away, after the mod's strokes, as the build does (rusemod.build.cleared_woods).
//   Proven in the game: tanks drive into a cleared wood and infantry there are seen (2026-10-01). ---
// cover's cells: bit 1 the map's own, bit 2 the Town tool's, bit 4 painted (Cover brush, Forest), bit 8 taken away
// (Uncover, or a wood an Erase circle clears); one colour each (COVER_COLOURS, the legend's too), the Town tool's over a
// painted one over the map's own. moves' cells: bits 1 and 2 as above, bit 4 changed by a Block or Open brush.
// What a brush changed is striped (STRIPE), so every stroke shows where it went, even on ground it changed nothing
// on: Uncover where there was no cover, Open where units could already go (the owner, 2026-10-15, painting on
// Kasserine Pass's desert, which has almost no cover: "they literally do nothing ... there's no indicator that it's
// working").
const COVER_COLOURS = { own: [60, 210, 90, 125], painted: [170, 240, 70, 150], town: [240, 150, 50, 160],
  taken: [240, 236, 222, 165] };
const MOVE_COLOURS = { none: [220, 50, 40, 120], infantry: [235, 200, 40, 115], vehicles: [170, 90, 220, 120],
  opened: [60, 150, 250, 165] };
const ERASE_COLOUR = [235, 70, 45, 120];
const STRIPE = 2600;  // map units (10 m) each stripe is wide, at least two cells
// A colour drawn in stripes: `a` on one, `b` (or nothing) on the next; `paler` lifts a colour towards white for the
// stripes between a changed cell's own colour
const striped = (a, b = null) => ({ stripe: [a, b] });
const paler = (c) => [c[0] + (255 - c[0]) * 0.5, c[1] + (255 - c[1]) * 0.5, c[2] + (255 - c[2]) * 0.5, c[3] + 30];
const cover = { kinds: ["cover", "town", "forest"], colors: [null, COVER_COLOURS.own, COVER_COLOURS.town, COVER_COLOURS.town,
  COVER_COLOURS.painted, COVER_COLOURS.painted, COVER_COLOURS.town, COVER_COLOURS.town, striped(COVER_COLOURS.taken)] };
const moves = { kinds: ["block", "open"], colors: [null, MOVE_COLOURS.vehicles, MOVE_COLOURS.infantry, MOVE_COLOURS.none,
  striped(MOVE_COLOURS.opened), ...[MOVE_COLOURS.vehicles, MOVE_COLOURS.infantry, MOVE_COLOURS.none].map((c) => striped(c, paler(c)))] };
const erased = { kinds: ["erase"], colors: [null, ERASE_COLOUR] };
const OVERLAYS = [cover, moves, erased];
const ERASE_CELLS = 1024;  // the erased overlay's cells across the map (about 12 m each on the biggest maps)
for (const o of OVERLAYS) {
  Object.assign(o, { base: null, cells: null, size: 0, box: null, canvas: null, ctx: null, img: null, tex: null,
    mesh: null, show: false, batch: false, stripe: 2 });
}
// what a brush does to an overlay's cells: [overlay, bits it sets, bits it clears]
const PAINTS = { cover: [cover, 4, 8], town: [cover, 2, 8], uncover: [cover, 8, 7], block: [moves, 7, 0], block_infantry: [moves, 5, 0],
  block_vehicles: [moves, 6, 0], open: [moves, 4, 3], open_infantry: [moves, 4, 1], open_vehicles: [moves, 4, 2],
  erase: [erased, 1, 0] };
// What a cell means for units, without the marks of what changed it: hidden or not (cover), closed to whom (moves)
const MEANS = new Map([[cover, (v) => (v & 7 ? 1 : 0)], [moves, (v) => v & 3]]);
// a zone brush's ring is drawn in the colour it paints (Block infantry leaves ground for vehicles only, and so on)
const ZONE_RING = { cover: COVER_COLOURS.painted, uncover: COVER_COLOURS.taken, town: COVER_COLOURS.town,
  forest: COVER_COLOURS.painted, block: MOVE_COLOURS.none, block_infantry: MOVE_COLOURS.vehicles,
  block_vehicles: MOVE_COLOURS.infantry, open: MOVE_COLOURS.opened, open_infantry: MOVE_COLOURS.opened,
  open_vehicles: MOVE_COLOURS.opened };

function overlayShown(o) {
  return o.show || (mv.brush.on && o.kinds.includes(BRUSHES[mv.brush.name][0]));
}

function showOverlays() {
  for (const o of OVERLAYS) if (o.mesh) o.mesh.visible = overlayShown(o);
  renderLegend();
  if (mv.gl) mv.gl.draw();
}

// What each colour on the ground means, for the overlays shown (the Cover box, Where units go, a brush of theirs)
function renderLegend() {
  const w = mv.words, box = $("map-legend");
  if (!box || !w.legend_title) return;
  const rgb = (c) => `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
  const rows = [];
  if (overlayShown(cover)) {
    rows.push([COVER_COLOURS.own, w.legend_cover_own], [COVER_COLOURS.painted, w.legend_cover_painted],
      [COVER_COLOURS.town, w.legend_cover_town], [striped(COVER_COLOURS.taken), w.legend_cover_taken]);
  }
  if (overlayShown(moves)) {
    rows.push([MOVE_COLOURS.none, w.legend_move_none], [MOVE_COLOURS.infantry, w.legend_move_infantry],
      [MOVE_COLOURS.vehicles, w.legend_move_vehicles], [striped(MOVE_COLOURS.opened), w.legend_move_opened],
      [striped(MOVE_COLOURS.none, paler(MOVE_COLOURS.none)), w.legend_move_changed]);
  }
  if (overlayShown(erased)) rows.push([ERASE_COLOUR, w.legend_erase]);
  if (scen.show && scen.group) {  // the scenario: starting points (pillars), spawns (icons), their sides' colours
    const hexRgb = (h) => [(h >> 16) & 255, (h >> 8) & 255, h & 255];
    rows.push([hexRgb(ALLIANCE[0]), w.legend_start], [null, w.legend_spawn_icons], [hexRgb(NEUTRAL_COLOUR), w.legend_neutral]);
  }
  box.replaceChildren(...(rows.length ? [el("div", { className: "legend-title", textContent: w.legend_title })] : []),
    ...rows.map(([c, text]) => el("div", { className: "legend-row" },
      !c ? el("span", { className: "swatch none" })
        : c.stripe ? el("span", { className: "swatch", style: "background: repeating-linear-gradient(135deg, "
          + `${rgb(c.stripe[0])} 0 3px, ${c.stripe[1] ? rgb(c.stripe[1]) : "transparent"} 3px 6px)` })
          : el("span", { className: "swatch", style: `background: ${rgb(c)}` }),
      el("span", { textContent: text }))));
  box.classList.toggle("hidden", !rows.length);
}

// --- see-through layers: a slider per layer, 0 to 100 %, times each part's own opacity; kept in this window ---
const LAYERS = ["water", "cover", "moves", "roads", "building", "prop", "vegetation", "scenario"];
const alpha = Object.fromEntries(LAYERS.map((k) => [k, 1]));
try { Object.assign(alpha, JSON.parse(localStorage.getItem("studio.alpha") || "{}")); } catch { /* not kept: fine */ }
// The scenario's zones (sectors) as borders on the ground, like Stellaris' (the owner, 2026-10-03: the coloured sheets
// floating over the map covered its textures and the icons, "it needs to change"; "like Stellaris borders ... the
// inside's kind of translucent, but the borders are clear"): a clear line along each border, a glow just inside it
// fading inwards, and a faint fill, all in the zone's own soft colour. The slider sets the inside, 0 to 1 of
// ZONE_FILL_MOST (0: the borders alone); the borders always show. Kept by the Studio (prefs "view": saveView).
const ZONE_FILL_MOST = 0.3, ZONE_GLOW = 2.2;  // the fill's opacity at 100 %, and the glow's at the border against it
let zoneFill = 0.35;
const zoneColour = (k) => new mv.gl.THREE.Color().setHSL((k * 0.137) % 1, 0.8, 0.5);

// The zones' inside (fill and glow) at the slider's value, and the see-through slider's on top
function fillZones() {
  if (!scen.zones) return;
  for (const o of scen.zones.children) {
    const part = o.userData.zonePart;
    if (!part) continue;
    const m = o.material, base = part === "glow" ? Math.min(1, ZONE_FILL_MOST * ZONE_GLOW * zoneFill) : ZONE_FILL_MOST * zoneFill;
    Object.assign(m.userData, { baseOpacity: base, baseTransparent: true, baseDepthWrite: false, alpha: undefined });  // fade's
    m.opacity = base * alpha.scenario;
    m.needsUpdate = true;
    o.visible = zoneFill > 0;
  }
}

function layerObjects(k) {
  switch (k) {
    case "water": return [mv.gl && mv.gl.water];
    case "cover": return [cover.mesh];
    case "moves": return [moves.mesh, erased.mesh];
    case "roads": return [roads.line, road.mesh, road.preview, bridge.mesh];
    case "scenario": return scen.group ? scen.group.children.filter((o) => o !== scen.zones && o !== scen.names) : [];
    default: return [mv.scenery.meshes[k], ...((mv.scenery.models || {})[k] || []), ...(mv.place.meshes[k] || [])];
  }
}

// --- Map and Scenario (the owner, 2026-10-09): the bar holds one side's tools, and the other side's things show
// faded and can't be picked: in Map mode the scenario's units, HQs and spots ("no dragging a unit while painting
// ground"), "and vice versa. So in the scenario mode, you can't accidentally move a building". The sectors are on the
// Map side (his sorting, the same day). The ground and the water are the map itself: never faded. ---
// A locked thing is a pale ghost of itself: see-through, and lit things lifted towards white, because see-through alone
// lost the HQs' pillars (lit, their dark red is the fields' brown: at 45 % a pillar was 109,68,34 on ground 101,82,34)
const LOCKED_ALPHA = 0.4, GHOST_LIFT = 0.3;
// The towns' and hills' names are the Map side's too, though they're the scenario's items (the owner, 2026-10-10: "you
// should be able to name towns ... on the map editor when you're making the actual town"): the Names tile places them,
// and they move there; on the Scenario side they're a ghost like the buildings.
const MAP_SIDE = new Set(["cover", "moves", "roads", "building", "prop", "vegetation", "zones", "names"]);
const NAME_KINDS = new Set(["LabelVille", "LabelMontagne"]);
const locked = (k) => (k === "scenario" ? mv.mode !== "scenario" : MAP_SIDE.has(k) && mv.mode !== "map");
const shownAlpha = (k) => alpha[k] * (locked(k) ? LOCKED_ALPHA : 1);

// A part's materials at `a` of their own opacity, a ghost when `ghost`. The game's models cut their leaves and windows
// out at alphaTest 0.5, which the opacity counts in: the cut-out is scaled too, or a model under half would vanish
// instead of fading.
function fade(obj, a, ghost = false) {
  if (!obj) return;
  obj.traverse((o) => {
    for (const m of o.material ? [].concat(o.material) : []) {
      const u = m.userData;
      if (u.alpha === a && Boolean(u.ghost) === ghost) continue;
      if (u.baseOpacity === undefined) Object.assign(u, { baseOpacity: m.opacity, baseTransparent: m.transparent,
        baseDepthWrite: m.depthWrite });
      if (u.baseAlphaTest === undefined) u.baseAlphaTest = m.alphaTest || 0;
      if (u.baseAlphaTest) m.alphaTest = u.baseAlphaTest * a;
      m.opacity = u.baseOpacity * a;
      m.transparent = u.baseTransparent || a < 1;
      m.depthWrite = a < 1 ? false : u.baseDepthWrite;
      if (m.emissive) {  // lit materials only; icons, labels and lines are drawn in their own colours already
        if (u.baseEmissive === undefined) u.baseEmissive = m.emissive.getHex();
        m.emissive.setHex(u.baseEmissive);
        if (ghost) m.emissive.addScalar(GHOST_LIFT);
      }
      m.needsUpdate = true;
      u.alpha = a;
      u.ghost = ghost;
    }
  });
}

// Before every frame (new parts, a redrawn road say, take their layer's value too): the slider's value, times the
// locked side's fade. The scenario's zones (sectors) take the Scenario slider and the Map side's fade.
function fadeLayers() {
  for (const k of LAYERS) for (const o of layerObjects(k)) fade(o, shownAlpha(k), locked(k));
  fade(scen.zones, alpha.scenario * (locked("zones") ? LOCKED_ALPHA : 1), locked("zones"));
  fade(scen.names, alpha.scenario * (locked("names") ? LOCKED_ALPHA : 1), locked("names"));
}

function renderLayers() {
  const w = mv.words, rows = $("map-layers-rows");
  if (!rows) return;
  $("map-layers-label").textContent = w.layers_title;
  $("map-layers-label").title = w.tip_layers || "";
  const name = { water: w.water, cover: w.cover_show, moves: w.move_show, roads: w.roads_show,
    building: w.scenery_building, prop: w.scenery_prop, vegetation: w.scenery_vegetation, scenario: w.scen_show };
  rows.replaceChildren(...LAYERS.map((k) => {
    const value = el("span", { className: "muted", textContent: `${Math.round(alpha[k] * 100)} %` });
    const range = el("input", { type: "range", min: "0", max: "100", step: "5", value: String(Math.round(alpha[k] * 100)),
      title: w.tip_layer_alpha });
    range.dataset.stepper = "buttons";   // (its % is said beside it)
    range.setAttribute("aria-label", name[k] || k);
    range.addEventListener("input", () => {
      alpha[k] = Number(range.value) / 100;
      value.textContent = `${range.value} %`;
      try { localStorage.setItem("studio.alpha", JSON.stringify(alpha)); } catch { /* not kept: fine */ }
      if (mv.gl) mv.gl.draw();
    });
    return el("label", { className: "layer-row" }, el("span", { textContent: name[k] || k }), range, value);
  }), zoneFillRow());
}

// How much of the zones' inside shows (fillZones): a slider under the see-through ones
function zoneFillRow() {
  const w = mv.words, value = el("span", { className: "muted", textContent: `${Math.round(zoneFill * 100)} %` });
  const range = el("input", { type: "range", min: "0", max: "100", step: "5", value: String(Math.round(zoneFill * 100)),
    title: w.tip_zone_fill || "" });
  range.dataset.stepper = "buttons";   // (its % is said beside it)
  range.setAttribute("aria-label", w.zone_fill || "Zones' fill");
  range.addEventListener("input", () => {
    zoneFill = Number(range.value) / 100;
    value.textContent = `${range.value} %`;
    fillZones();
    if (mv.gl) mv.gl.draw();
  });
  range.addEventListener("change", () => saveView());
  return el("label", { className: "layer-row", title: w.tip_zone_fill || "" }, el("span", { textContent: w.zone_fill || "Zones' fill" }),
    range, value);
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
  Object.assign(o, { base, cells: base.slice(), size: res.size, box: res.box,
    stripe: Math.max(2, Math.round(STRIPE / (res.box[2] / res.size))) });  // (one cell would be a chequerboard)
  overlayMesh(o);
  o.batch = true;
  for (const s of mv.brush.strokes) if (PAINTS[s.brush] && PAINTS[s.brush][0] === o) overlayDab(s);
  for (const a of mv.brush.erase) eraseDab(a, o);  // after the strokes, as the build clears woods
  o.batch = false;
  overlayDraw(o, 0, o.size - 1, 0, o.size - 1);
}

// The erased overlay of the map shown: a grid over the map's own box, empty until the circles are painted on it.
function startErased() {
  const [x0, y0, , x1, y1] = mv.edit.bounds, n = ERASE_CELLS;
  startOverlay(erased, new Uint8Array(n * n), { size: n, box: [x0, y0, x1 - x0, y1 - y0] });
}

// Whether an Erase circle takes trees: then the build opens its ground and takes its cover away too.
function clearsWood(a) {
  return (a.what || ERASE_DEFAULT).includes("vegetation");
}

// One Erase circle on the overlays (only `only`, when given): red on the erased one; a wood cleared on the others.
function eraseDab(a, only) {
  for (const brush of clearsWood(a) ? ["erase", "open", "uncover"] : ["erase"]) {
    if (!only || PAINTS[brush][0] === only) {
      overlayDab({ brush, x: a.x, y: a.y, radius: a.radius, shape: a.shape, dx: a.dx, dy: a.dy, x2: a.x2, y2: a.y2 });
    }
  }
}

// The Erase circles changed (loaded, taken back, not saved): every overlay again from the map's own cells, then the
// strokes, then the circles (reapply's order, without touching the ground), and the objects they take tinted again.
function refreshErased() {
  const live = OVERLAYS.filter((o) => o.cells);
  for (const o of live) { o.cells.set(o.base); o.batch = true; }
  for (const s of mv.brush.strokes) if (PAINTS[s.brush]) overlayDab(s);
  for (const a of mv.brush.erase) eraseDab(a);
  for (const o of live) { o.batch = false; overlayDraw(o, 0, o.size - 1, 0, o.size - 1); }
  tintScenery();
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

// One brush stroke on the cells whose centres are inside it (rusemod.cover.paint's rule; rusemod.nav closes the
// graphs' circles that reach into it): a circle, a square turned any way (square = true, written by hand in
// terrain.toml, MOD_FORMAT §8, is one along the map's axes), or a line, as the build paints it (footT2).
function overlayDab(s) {
  const [o, on, off] = PAINTS[s.brush];
  if (!o.cells) return;
  const n = o.size, [bx, by, bw, bh] = o.box, cw = bw / n, ch = bh / n, [x0, x1, y0, y1] = boxOf(s);
  const c0 = Math.max(0, Math.floor((x0 - bx) / cw)), c1 = Math.min(n - 1, Math.ceil((x1 - bx) / cw));
  const r0 = Math.max(0, Math.floor((y0 - by) / ch)), r1 = Math.min(n - 1, Math.ceil((y1 - by) / ch));
  if (c0 > c1 || r0 > r1) return;
  const count = zoneCount && zoneCount.o === o && !o.batch ? zoneCount : null;  // (not the strokes drawn again)
  for (let r = r0; r <= r1; r++) {
    const y = by + (r + 0.5) * ch;
    for (let c = c0; c <= c1; c++) {
      const i = r * n + c;
      if (footT2(s, bx + (c + 0.5) * cw, y) <= 1) {
        if (count && !count.seen[i]) { count.seen[i] = 1; count.cells.push(i); count.was.push(o.cells[i]); }
        o.cells[i] = (o.cells[i] & ~off) | on;
      }
    }
  }
  if (!o.batch) overlayDraw(o, r0, r1, c0, c1);
}

// A zone stroke being painted (Cover, Uncover, Town, Forest's cover, Block, Open): its overlay, the cells it reached
// and what each held before it, so its end can say what it changed for units (zoneSaid).
let zoneCount = null;
function countZone(brush) {
  const o = PAINTS[brush] && PAINTS[brush][0];
  zoneCount = o && o.cells && MEANS.has(o) ? { o, brush, seen: new Uint8Array(o.size * o.size), cells: [], was: [] } : null;
}

// What the zone stroke just painted did, in square metres: on the ground it reached, how much now hides units or is
// closed to them that wasn't, and the other way round. "Nothing changed" is said too, so a stroke always answers.
function zoneSaid(count) {
  if (!count || !count.cells.length) return "";
  const w = mv.words, o = count.o, means = MEANS.get(o), [, , bw, bh] = o.box;
  const closed = (v) => (o === moves ? (v & 1) + ((v >> 1) & 1) : v);
  let more = 0, less = 0;
  count.cells.forEach((i, k) => {
    const a = closed(means(count.was[k])), b = closed(means(o.cells[i]));
    if (b > a) more++; else if (b < a) less++;
  });
  const cell = (bw / o.size) * (bh / o.size) / (METRE * METRE);
  const m2 = (n) => (Math.round(n * cell / 100) * 100 || Math.round(n * cell)).toLocaleString();
  const all = m2(count.cells.length), kind = BRUSHES[count.brush][0];
  if (count.brush === "uncover") return less ? fill(w.zone_uncover_done, { m2: m2(less) }) : fill(w.zone_uncover_none, { m2: all });
  if (kind === "block") return more ? fill(w.zone_block_done, { m2: m2(more) }) : fill(w.zone_block_none, { m2: all });
  if (kind === "open") return less ? fill(w.zone_open_done, { m2: m2(less) }) : fill(w.zone_open_none, { m2: all });
  return more ? fill(w.zone_cover_done, { m2: m2(more) }) : fill(w.zone_cover_none, { m2: all });
}

function overlayDraw(o, r0, r1, c0, c1) {
  if (!o.cells || !o.img) return;
  const n = o.size, px = o.img.data, wide = o.stripe;
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      const i = r * n + c, k = 4 * i;
      let rgba = o.colors[o.cells[i]];
      if (rgba && rgba.stripe) rgba = rgba.stripe[Math.floor((r + c) / wide) & 1];  // diagonal stripes
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
// follow the brushes. (Drawing new roads comes next.) ---
const roads = { pieces: null, line: null, show: false };
const ROAD_STEP = 8000;  // map units per line (about 30 m): a long piece gets more, so it follows hills
const ROAD_LIFT = 600;   // map units above the ground (about 2 m), so the ground doesn't hide them

async function loadRoads(pack, ask) {
  dropRoads();
  const res = blankMap(pack) ? { pieces: [] } : await mv.api.map_roads(pack);  // a blank map's roads are all taken out
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

// The buildings' spots in squares of `cell` map units, made again when the map's or the mod's buildings change.
let townGrid = null;
function buildingGrid(cell) {
  const d = mv.scenery.data, placed = mv.place.objects;
  if (townGrid && townGrid.data === d && townGrid.placed === placed && townGrid.n === placed.length && townGrid.cell === cell) {
    return townGrid;
  }
  const grid = new Map();
  for (const p of buildingSpots()) {
    const k = `${Math.floor(p[0] / cell)},${Math.floor(p[1] / cell)}`;
    (grid.get(k) || grid.set(k, []).get(k)).push(p);
  }
  return (townGrid = { data: d, placed, n: placed.length, cell, grid });
}

// The town at a spot: the building nearest it, within `near` map units (at least 150 m: the pointer's reach on the
// screen, so a click at any zoom finds the town under it), and every building linked to that one by a chain of
// neighbours no further apart than twice the margin (at least 60 m), within 800 m of the spot. Each gets a cover circle.
const TOWN_PICK = 150, TOWN_LINK = 60, TOWN_REACH = 800, TOWN_MOST = 3000;  // metres, and buildings at most
function townAt(x, y, near = 0) {
  const r = brushRadius("town"), link = Math.max(2 * r, TOWN_LINK * METRE), reach = TOWN_REACH * METRE;
  const g = buildingGrid(link), at = (cx, cy) => g.grid.get(`${cx},${cy}`) || [];
  const pick = Math.max(near, TOWN_PICK * METRE), span = Math.ceil(pick / link);
  const cx = Math.floor(x / link), cy = Math.floor(y / link);
  let seed = null, best = pick * pick;
  for (let i = -span; i <= span; i++) {
    for (let j = -span; j <= span; j++) {
      for (const p of at(cx + i, cy + j)) {
        const d = (p[0] - x) ** 2 + (p[1] - y) ** 2;
        if (d < best) { best = d; seed = p; }
      }
    }
  }
  if (!seed) return [];
  const town = new Set([seed]), queue = [seed];
  for (let q = 0; q < queue.length && town.size < TOWN_MOST; q++) {
    const [qx, qy] = queue[q], qcx = Math.floor(qx / link), qcy = Math.floor(qy / link);
    for (let i = -1; i <= 1; i++) {
      for (let j = -1; j <= 1; j++) {
        for (const p of at(qcx + i, qcy + j)) {
          if (town.has(p) || (p[0] - qx) ** 2 + (p[1] - qy) ** 2 > link * link || (p[0] - x) ** 2 + (p[1] - y) ** 2 > reach * reach) continue;
          town.add(p);
          queue.push(p);
        }
      }
    }
  }
  return [...town];
}

function townStrokes(x, y, near) {
  const r = brushRadius("town");
  return townAt(x, y, near).map(([px, py]) => ({ brush: "town", x: Math.round(px), y: Math.round(py), radius: r }));
}

// How many map units `px` pixels of the screen span at a point of the scene (a pick that's as easy at any zoom).
function pixelsAt(p, px) {
  const gl = mv.gl, h = gl.renderer.domElement.clientHeight || 1;
  return gl.camera.position.distanceTo(p) * 2 * Math.tan(gl.camera.fov * Math.PI / 360) / h * px / SCALE;
}

// With Town picked, before the click: a ring on each building the click would give cover (yellow, over the orange of
// cover a town already has) and the count at the pointer (the owner, 2026-10-15: "the town button doesn't do
// anything").
const TOWN_POINTER = 40;  // pixels: how near the pointer a town's building is found
const TOWN_QUIET = 24;    // pixels the pointer moves after a click before the rings show again
const TOWN_RING = [255, 232, 90];
function showTownPreview(p, ev) {
  const gl = mv.gl, { THREE } = gl;
  if (!gl.townRings) {
    const geo = new THREE.RingGeometry(0.86, 1, 32);
    geo.rotateX(-Math.PI / 2);
    gl.townRings = new THREE.InstancedMesh(geo, new THREE.MeshBasicMaterial({ color: new THREE.Color().setRGB(
      ...TOWN_RING.map((v) => v / 255), THREE.SRGBColorSpace), transparent: true, opacity: 0.9, depthTest: false }), TOWN_MOST);
    gl.townRings.renderOrder = 10;
    gl.townRings.frustumCulled = false;
    gl.scene.add(gl.townRings);
  }
  const rings = gl.townRings, quiet = mv.brush.townClicked;
  // after a click the cover it made shows, with its count, until the pointer moves on
  if (quiet && ev && Math.hypot(ev.clientX - quiet.clientX, ev.clientY - quiet.clientY) < TOWN_QUIET) return;
  mv.brush.townClicked = null;
  const town = p && mv.brush.on && mv.brush.name === "town" && mv.edit ? townAt(p.x / SCALE, p.z / SCALE,
    pixelsAt(p, TOWN_POINTER)) : [];
  rings.visible = town.length > 0;
  if (town.length) {
    const grid = heightGrid(), m = new THREE.Matrix4(), r = brushRadius("town") * SCALE;
    town.forEach(([x, y], k) => {
      m.makeScale(r, r, r);
      m.setPosition(x * SCALE, (groundAt(grid, x, y) + 300) * SCALE, y * SCALE);
      rings.setMatrixAt(k, m);
    });
    rings.count = town.length;
    rings.instanceMatrix.needsUpdate = true;
  }
  if (p && ev && mv.brush.on && mv.brush.name === "town") {
    pointerTag(ev, town.length ? fill(mv.words.town_preview, { n: town.length.toLocaleString() }) : mv.words.town_point);
  }
  gl.draw();
}

// The ground's heights on a coarse grid (makeGrid), kept until a stroke changes the ground
let heightKept = null;
function heightGrid() {
  const ed = mv.edit, n = mv.brush.strokes.length;
  if (!heightKept || heightKept.ed !== ed || heightKept.n !== n) heightKept = { ed, n, grid: makeGrid(ed) };
  return heightKept.grid;
}

// A word beside the pointer, over the map (a brush's count, what a click would do); `bad` in the error colour. Shown
// at the pointer `ev` (or where the pointer last was), for a few seconds when `stay` is given.
let tagTimer = 0;
function pointerTag(ev, text, bad = false, stay = 0) {
  const tag = $("brush-tag");
  clearTimeout(tagTimer);
  if (!text) { tag.classList.add("hidden"); return; }
  const at = ev || mv.brush.lastPointer;
  tag.textContent = text;
  tag.classList.toggle("bad", bad);
  if (at) {
    const box = tag.parentElement.getBoundingClientRect();
    tag.style.left = `${Math.round(at.clientX - box.left + 16)}px`;
    tag.style.top = `${Math.round(at.clientY - box.top + 18)}px`;
  }
  tag.classList.remove("hidden");
  if (stay) tagTimer = setTimeout(() => tag.classList.add("hidden"), stay);
}

function forget(mesh) {
  if (!mesh) return;
  mv.gl.scene.remove(mesh);
  if (!mesh.geometry.userData.keep) mesh.geometry.dispose();  // (a model's parts are shared: modelLibrary)
  if (mesh.material.map && !mesh.material.map.userData.keep) mesh.material.map.dispose();
  mesh.material.dispose();
}

// --- Map Paint (rusemod.groundpaint.paint_strokes): the Colour and Texture brushes paint the ground's
// picture. The Studio shows them on its own copy of the map's picture (a canvas laid on the ground), with the build's
// rules: each stroke at its opacity times its brush's fall-off, in order; a Texture stroke lays the texture picked,
// repeating (rusemod.groundtex: the game's own, a square of any map's ground, the mod's own picture), or copies the
// map's own picture from where it was told (sx, sy), as the map was before any paint. The build paints every level of
// the game's tiles the same way; what the game shows of the textures is not tested yet. ---
const paint = {
  canvas: null, ctx: null, data: null, base: null, tex: null, material: null, original: null, batch: false,
  colour: "#8a7a4e", recent: [], palette: null,  // the colour painted, the last ones used, the map's own colours
  picking: null,  // "colour": the next click takes the ground's colour; "source": it picks where Texture copies from
  source: null,   // where Texture copies from: { x, y } picked, until the next stroke turns it into the offset
  offset: null,   // Texture's offset from each point it paints to where it copies from: { sx, sy }, kept stroke to stroke
  clear: true,    // the strokes take off what hides them up close (the build: groundpaint.paint_clearing; T21)
  decals: true,   // a game texture's strokes get the game's own decals of it up close (groundtex.decal_grid)
  // the Texture brush's library (the owner, 2026-10-09: "On a blank map, there is no spot to copy from ... add all of
  // the game textures ... make it very easy to be able to add cool textures to your map")
  from: "palette",  // where Texture takes from: "palette" (ground materials measured on the game's maps), "game"
                  // (the game's textures), "map" (any map's ground), "own" (the mod's own pictures), "online" (free
                  // pictures from the internet) or "spot" (a spot of this map, copied)
  texture: null,  // the texture picked (its ref, rusemod.groundtex) and how big it's laid: 2^texScale times its own
  texScale: 0,
  texTurn: 0,     // degrees the texture is turned on the ground (a stroke's turn: a field's rows run this way)
  mask: "",       // the brush's pattern (rusemod.brushmask; "" plain), for Colour and Texture alike
  dither: false,  // a speckled edge instead of a blend (brushmask.dither_at: up close only, the finest level)
  beach: false,   // Paint by shape: sand round the new lakes (off: grass to the water, as D-Day's inland water)
  masks: null,    // the masks themselves (StudioApi.brush_masks), once read: maskSampler
  repainted: [],  // what the build lays for the map's Paint by shape strokes (StudioApi.repaint_preview): repaintSoon
  coats: new Set(),  // the map's paint strokes, from the first, that coat it all (coatStrokes): laid under repainted
  repaintFor: "", repaintTimer: 0,
  materials: null, matLoading: false,  // the palette (StudioApi.ground_palette), once read
  textures: null, // the game's textures (StudioApi.ground_textures), once read; texGroup and texSearch filter them
  texGroup: "all", texSearch: "", texLoading: false,
  own: null,      // the mod's own pictures (StudioApi.ground_pictures)
  // Online (free): Poly Haven, ambientCG or US aerial photos (StudioApi.online_textures): each one's list once read,
  // what's typed to find in each (ambientCG's site is asked for `asked` once typing stops), the US photos' size and a
  // typed place, and the one picture being downloaded (`busy`: one at a time)
  online: { from: "polyhaven", lists: {}, loading: "", error: "", errorFor: "", search: { polyhaven: "",
    ambientcg: "", usgs: "" }, asked: "", timer: 0, metres: 320, where: "", busy: "", busyName: "" },
  mapPick: null,  // From a map: { pack, picture, bounds } of the map being picked from
  swatches: {},   // ref -> { period, n, mips: [Uint8ClampedArray], name, thumb } once its picture is in, or { loading }
  used: [],       // the textures painted with lately, newest first
};

// The canvas the paint is shown on: the ground's picture as the map has it, made again when the picture changes (a
// new map, or the real tiles in place of the small overview). null while the map has no picture.
function paintSurface() {
  const gl = mv.gl;
  if (!gl || !gl.ground || !mv.edit) return null;
  const mat = gl.ground.material;
  if (paint.canvas && paint.material === mat && mat.map === paint.tex) return paint;
  const shown = mat.map && mat.map !== paint.tex ? mat.map : paint.material === mat ? paint.original : null;
  const image = shown && shown.image;
  if (!image || !image.width) return null;
  const c = paint.canvas && paint.canvas.width === image.width && paint.canvas.height === image.height
    ? paint.canvas : el("canvas", { width: image.width, height: image.height });
  const ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.clearRect(0, 0, c.width, c.height);
  ctx.drawImage(image, 0, 0);
  if (paint.tex) paint.tex.dispose();
  Object.assign(paint, { canvas: c, ctx, material: mat, original: shown, palette: null,
    base: ctx.getImageData(0, 0, c.width, c.height) });
  paint.data = new ImageData(new Uint8ClampedArray(paint.base.data), c.width, c.height);
  const tex = new gl.THREE.CanvasTexture(c);
  tex.colorSpace = shown.colorSpace;
  tex.anisotropy = shown.anisotropy;
  paint.tex = tex;
  mat.map = tex;
  mat.color.set(0xffffff);
  mat.needsUpdate = true;
  return paint;
}

// Where a map point falls on the picture: column and row (the picture is north up, row 0 at the map's y min).
function paintPixel(x, y) {
  const [x0, y0, , x1, y1] = mv.edit.bounds, c = paint.canvas;
  return [(x - x0) / (x1 - x0) * c.width, (y - y0) / (y1 - y0) * c.height];
}

function paintBegin() {
  const gl = mv.gl, mat = gl && gl.ground && gl.ground.material;
  // a map with no paint keeps its own picture (one painted earlier this session is put back to it)
  if (!mv.brush.strokes.some((s) => PAINT_KINDS.has(s.brush)) && !paint.repainted.length
      && !(paint.canvas && paint.material === mat)) return;
  if (!paintSurface()) return;
  paint.data.data.set(paint.base.data);
  paint.batch = true;
  paint.coats = paint.repainted.length ? coatStrokes() : new Set();
  for (const s of paint.coats) paintDab(s);  // a blank map's one-colour coat first (repaint.coats)
  for (const s of paint.repainted) paintDab(s);  // what moved, by its new shape (repaintSoon): under the mod's paint
}

// The map's paint strokes, from the first, that coat the whole map at full strength (Blank Terrain's one colour):
// Paint by shape goes over them and under the rest (rusemod.repaint.coats' test).
function coatStrokes() {
  const [x0, y0, , x1, y1] = mv.edit.bounds, out = new Set();
  const corners = [[x0, y0], [x0, y1], [x1, y0], [x1, y1]];
  for (const s of mv.brush.strokes) {
    if (!PAINT_KINDS.has(s.brush)) continue;
    if (!(s.brush === "paint" && s.edge === "hard" && (s.weight === undefined || s.weight >= 1) && !s.mask
          && !s.dither && corners.every(([x, y]) => footT2(s, x, y) <= HARD_EDGE * HARD_EDGE))) break;
    out.add(s);
  }
  return out;
}

function paintEnd() {
  if (!paint.batch) return;
  paint.batch = false;
  paint.ctx.putImageData(paint.data, 0, 0);
  paint.tex.needsUpdate = true;
}

// The picture changed under the paint (the real tiles arrived): the paint again on the new one.
function paintRefresh() {
  if (!mv.brush.strokes.some((s) => PAINT_KINDS.has(s.brush)) && !paint.repainted.length) return;
  if (!paintSurface()) return;
  paintBegin();
  for (const s of mv.brush.strokes) if (PAINT_KINDS.has(s.brush) && !paint.coats.has(s)) paintDab(s);
  paintEnd();
}

// One Colour or Texture stroke on the picture, as rusemod.groundpaint.paint_strokes lays it on the game's tiles.
function paintDab(s) {
  if (!paintSurface()) return;
  const c = paint.canvas, W = c.width, H = c.height, px = paint.data.data, base = paint.base.data;
  const [xlo, xhi, ylo, yhi] = boxOf(s);
  const [c0, r0] = paintPixel(xlo, ylo), [c1, r1] = paintPixel(xhi, yhi);
  const ca = Math.max(0, Math.floor(c0)), cb = Math.min(W - 1, Math.ceil(c1));
  const ra = Math.max(0, Math.floor(r0)), rb = Math.min(H - 1, Math.ceil(r1));
  if (ca > cb || ra > rb) return;
  const [x0, y0, , x1, y1] = mv.edit.bounds, pw = (x1 - x0) / W, ph = (y1 - y0) / H;
  const rgb = s.brush === "paint" ? hexRgb(s.colour) : null, weight = s.weight === undefined ? 1 : s.weight;
  const ox = s.brush === "stamp" ? s.sx / pw : 0, oy = s.brush === "stamp" ? s.sy / ph : 0;
  const tex = s.brush === "texture" ? textureSampler(s, Math.max(pw, ph)) : null;
  if (s.brush === "texture" && !tex) return;  // its picture is on its way: the paint is laid again when it's in
  const mask = maskSampler(s);
  if (mask === undefined) return;  // the masks are on their way: the same
  const speckle = s.dither && Math.max(pw, ph) <= DITHER_MOST;  // (as the build: only on pixels as fine as the finest)
  for (let r = ra; r <= rb; r++) {
    const y = y0 + (r + 0.5) * ph;
    for (let col = ca; col <= cb; col++) {
      const xm = x0 + (col + 0.5) * pw;
      let a = dabCoverage(s, mask, speckle, xm, y, pw, ph) * weight;
      if (a <= 0) continue;
      const k = 4 * (r * W + col);
      let cr, cg, cbl;
      if (rgb) [cr, cg, cbl] = rgb;
      else if (tex) {  // a texture picked: its colour here, as much as it shows (its alpha)
        const t = tex(x0 + (col + 0.5) * pw, y);
        a *= t[3] / 255;
        if (a <= 0) continue;
        [cr, cg, cbl] = t;
      } else {  // Texture: the map's own picture where it copies from, as the map was before any paint
        const sc = Math.floor(col + 0.5 + ox), sr = Math.floor(r + 0.5 + oy);
        if (sc < 0 || sr < 0 || sc >= W || sr >= H) continue;
        const j = 4 * (sr * W + sc);
        cr = base[j]; cg = base[j + 1]; cbl = base[j + 2];
      }
      px[k] += (cr - px[k]) * a;
      px[k + 1] += (cg - px[k + 1]) * a;
      px[k + 2] += (cbl - px[k + 2]) * a;
    }
  }
  if (paint.batch) return;
  paint.ctx.putImageData(paint.data, 0, 0, ca, ra, cb - ca + 1, rb - ra + 1);
  paint.tex.needsUpdate = true;
}

// How much of a Colour or Texture stroke reaches the pixel centred at (x, y), pw x ph map units, before its opacity:
// rusemod.groundpaint._coverage's sums (its fall-off; a mask's (maskSampler) reach or share; a speckled edge's all or
// nothing where `speckle`).
function dabCoverage(s, mask, speckle, x, y, pw, ph) {
  let t2 = footT2(s, x, y);
  if (t2 >= 1) return 0;
  const m = mask ? mask(x, y) : 1;
  if (mask && mask.edge) t2 *= mask.reach(m);  // an edge mask: how far it reaches here (brushmask.reach_scale)
  if (t2 >= 1) return 0;
  let cov = edgeWeight(s.edge, "soft", t2);
  if (mask && !mask.edge) cov *= m;  // any other: as much as it shows
  if (speckle && cov > 0) cov = ditherAt(s, x, y, pw, ph) < cov ? 1 : 0;  // a speckled edge: all or nothing
  return cov;
}

// The dab the pointer would lay, shaded on the ground as the build lays it (Map Paint plan step 7): its colour (or
// its texture, turned and mirrored as laid) as strongly as its opacity and fall-off, its pattern and speckles in it,
// over a square SHADE_SPAN radii across. Colour and Texture only; a line's ends aren't known until it's drawn.
const SHADE_N = 96, SHADE_SPAN = 2.2, SHADE_ALPHA = 0.85, HOLD_STILL = 3;
function showShade(p) {
  const gl = mv.gl, shade = gl && gl.shade;
  if (!shade) return;
  const name = mv.brush.name, kind = BRUSHES[name] && BRUSHES[name][0];
  const on = Boolean(p) && mv.brush.on && (kind === "paint" || kind === "stamp") && mv.edit && !mv.brush.painting
    && !(kind === "stamp" && paint.from !== "spot" && !paint.texture)
    && !(kind === "stamp" && paint.from === "spot" && !paint.offset) && settingsOf(name).shape !== "line";
  if (!on) {
    if (shade.visible) { shade.visible = false; gl.draw(); }
    return;
  }
  const s = newStroke(p.x / SCALE, p.z / SCALE, 0, null);
  const tex = s.brush === "texture" ? textureSampler(s, (SHADE_SPAN * s.radius) / SHADE_N) : null;
  const mask = maskSampler(s);
  if ((s.brush === "texture" && !tex) || mask === undefined) { shade.visible = false; return; }  // on their way
  const { canvas, tex: ctex } = shade.userData, ctx = canvas.getContext("2d"), img = ctx.createImageData(SHADE_N, SHADE_N);
  const step = (SHADE_SPAN * s.radius) / SHADE_N, x0 = s.x - SHADE_SPAN * s.radius / 2, y0 = s.y - SHADE_SPAN * s.radius / 2;
  const speckle = s.dither && step <= DITHER_MOST, rgb = s.brush === "paint" ? hexRgb(s.colour) : [235, 235, 235];
  const weight = s.weight === undefined ? 1 : s.weight;
  for (let j = 0; j < SHADE_N; j++) {
    const y = y0 + (j + 0.5) * step;
    for (let i = 0; i < SHADE_N; i++) {
      const x = x0 + (i + 0.5) * step;
      let a = dabCoverage(s, mask, speckle, x, y, step, step) * weight;
      if (a <= 0) continue;
      let c = rgb;
      if (tex) { const t = tex(x, y); a *= t[3] / 255; c = t; }
      img.data.set([c[0], c[1], c[2], Math.round(255 * SHADE_ALPHA * a)], 4 * (j * SHADE_N + i));
    }
  }
  ctx.putImageData(img, 0, 0);
  ctex.needsUpdate = true;
  const r = s.radius * SCALE;
  shade.position.set(p.x, p.y + r * 0.02, p.z);
  shade.scale.set(r, r, 1);
  shade.visible = true;
}

// Paint by shape (Map Paint plan step 8): the build's own answer for the map's repaint strokes (the mod's ground
// brushes applied as the build does, then rusemod.repaint's rules), asked for a moment after they or the ground change
// (the Studio keeps it: a second time is quick), laid on the picture under the mod's own paint.
function repaintSoon() {
  clearTimeout(paint.repaintTimer);
  paint.repaintTimer = setTimeout(askRepaint, 600);
}

async function askRepaint() {
  const pack = mv.current, w = mv.words;
  if (!mv.api || !pack) return;
  if (mv.brush.painting) { repaintSoon(); return; }  // (a drag going on: its strokes aren't saved yet)
  if (paint.repainted.length && !paint.repaintFor.startsWith(`${pack}|`)) {  // another map: not its answer
    paint.repainted = [];
    reapply();
  }
  const shape = mv.brush.strokes.filter((s) => !PAINT_KINDS.has(s.brush));
  const key = `${pack}|${JSON.stringify(shape)}`;
  if (key === paint.repaintFor) return;  // (the answer for these strokes is on already: a redraw asks again)
  paint.repaintFor = key;
  if (!shape.some((s) => s.brush === "repaint")) {
    if (paint.repainted.length) { paint.repainted = []; reapply(); if (mv.gl) mv.gl.draw(); }
    return;
  }
  try {
    let res = await mv.api.repaint_preview(pack);
    while (res && res.job) {
      let view, since = 0;
      do {
        await wait(700);
        view = await mv.api.job(res.job, since);
        since = view.count;
        brushNote(fill(w.repaint_working, { progress: view.lines.length ? view.lines[view.lines.length - 1] : "" }));
      } while (view.state === "running");
      if (view.state !== "done") throw new Error(view.message);
      res = await mv.api.repaint_preview(pack);
    }
    if (pack !== mv.current || key !== paint.repaintFor) return;  // (another map, or newer strokes asked for)
    paint.repainted = res.strokes;
    for (const s of paint.repainted) loadSwatch(s.texture);
    reapply();
    if (mv.gl) mv.gl.draw();
    if (res.said) brushNote(fill(w.repaint_done, { said: res.said }));
  } catch (e) {
    paint.repaintFor = "";
    brushNote(fill(w.repaint_cant, { error: String((e && e.message) || e) }), "error");
  }
}

// Holding still while painting builds the dab under the pointer up (Map Paint plan step 7): every HOLD_STEP ms with
// the pointer still for HOLD_WAIT ms, its opacity rises by HOLD_MORE, up to all of it; it is saved as one dab with
// its final amount.
const HOLD_WAIT = 300, HOLD_STEP = 120, HOLD_MORE = 0.04;
function holdBuildUp(group) {
  const timer = setInterval(() => {
    if (mv.brush.painting !== group) { clearInterval(timer); return; }
    const s = group.strokes[group.strokes.length - 1];
    if (!s || performance.now() - (mv.brush.movedAt || 0) < HOLD_WAIT || (s.weight === undefined ? 1 : s.weight) >= 1) return;
    s.weight = Math.min(1, Math.round(((s.weight === undefined ? 1 : s.weight) + HOLD_MORE) * 100) / 100);
    paintRefresh();
    if (mv.gl) mv.gl.draw();
    brushNote(fill(mv.words.paint_building, { pct: Math.round(s.weight * 100) }));
  }, HOLD_STEP);
}

// The ground's colour at a map point as the picture shows it now (the paint too), or null off it.
function paintColourAt(x, y) {
  if (!paintSurface()) return null;
  const [col, row] = paintPixel(x, y), c = paint.canvas;
  const i = Math.floor(col), j = Math.floor(row);
  if (i < 0 || j < 0 || i >= c.width || j >= c.height) return null;
  const k = 4 * (j * c.width + i), d = paint.data.data;
  return rgbHex([d[k], d[k + 1], d[k + 2]]);
}

function hexRgb(hex) {
  return [1, 3, 5].map((i) => parseInt(String(hex || "#000000").slice(i, i + 2), 16) || 0);
}

function rgbHex(rgb) {
  return "#" + rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
}

// --- the Texture brush's textures (rusemod.groundtex; StudioApi's GroundTextureCalls): the picture the build lays
// (made seamless), sampled the build's way: from the map's corner, `size` map units a repeat, each pixel the mip
// whose pixels are nearest its size, nearest pixel, as much as it shows (its alpha) ---
const NEAREST_MIP = Math.SQRT2;  // groundtex.NEAREST_MIP
const TEX_SCALES = [-2, 4];      // the Size slider: 2^n times the texture's own size, a quarter to 16 times
const TEX_USED = 8;              // textures kept in "Used lately"
// a group's own word, not said again in a texture's name ("Grass · light green", not "Grass · light green, grass")
const GROUP_WORD = { grass: "grass", earth: "earth", sand: "sand", rock: "rock", snow: "snow", town: "town" };

function halveRgba(n, px) {  // groundtex.halve: each pixel the mean of the four under it, rounded half up
  const h = n >> 1, out = new Uint8ClampedArray(h * h * 4);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < h; i++) {
      const a = 4 * (2 * j * n + 2 * i), b = a + 4 * n, o = 4 * (j * h + i);
      for (let c = 0; c < 4; c++) out[o + c] = (px[a + c] + px[a + 4 + c] + px[b + c] + px[b + 4 + c] + 2) >> 2;
    }
  }
  return out;
}

// A texture stroke's sampler for pixels `pixel` map units across: (x, y) -> [r, g, b, a], or null while its picture
// is on its way (asked for once; the paint is laid again when it's in).
function textureSampler(s, pixel) {
  const sw = paint.swatches[s.texture];
  if (!sw || !sw.mips) { loadSwatch(s.texture); return null; }
  const rep = s.size > 0 ? s.size : sw.period;
  let m = 0;
  while (m + 1 < sw.mips.length && rep / (sw.n >> (m + 1)) <= pixel * NEAREST_MIP) m++;
  const n = sw.n >> m, data = sw.mips[m], last = n - 1;
  const turn = s.turn || 0, c = Math.cos(turn * Math.PI / 180), sn = Math.sin(turn * Math.PI / 180);
  // a palette swatch's grain (rusemod.groundtex.Swatch.grain_sampler's sums): unturned, unmirrored, its own repeat
  let g = null, gn = 0, grep = 0;
  if (sw.grain) {
    grep = sw.grainPeriod * rep / sw.period;
    let gm = 0;
    while (gm + 1 < sw.grain.length && grep / (sw.grainN >> (gm + 1)) <= pixel * NEAREST_MIP) gm++;
    g = sw.grain[gm]; gn = sw.grainN >> gm;
  }
  return (x, y) => {
    let f = 1;
    if (g) {
      const gu = x / grep, gv = y / grep;
      const gi = Math.min(gn - 1, Math.floor((gu - Math.floor(gu)) * gn));
      const gj = Math.min(gn - 1, Math.floor((gv - Math.floor(gv)) * gn));
      f = g[gj * gn + gi] / sw.grainUnit;
    }
    if (turn) { const tx = x * c + y * sn; y = y * c - x * sn; x = tx; }  // turned back by the turn round (0, 0)
    const u = x / rep, v = y / rep, cu = Math.floor(u), cv = Math.floor(v);
    let i = Math.min(last, Math.floor((u - cu) * n)), j = Math.min(last, Math.floor((v - cv) * n));
    if (sw.mirrored) {  // a palette swatch: each column of repeats mirrored or not along, each row across
      if (coin(cu, 7)) i = last - i;
      if (coin(cv, 68917)) j = last - j;
    }
    const k = 4 * (j * n + i);
    if (f === 1) return [data[k], data[k + 1], data[k + 2], data[k + 3]];
    return [Math.min(255, Math.floor(data[k] * f + 0.5)), Math.min(255, Math.floor(data[k + 1] * f + 0.5)),
      Math.min(255, Math.floor(data[k + 2] * f + 0.5)), data[k + 3]];
  };
}

// A one-byte-a-pixel square at half its size (groundtex._halve_plane's sums: the mean of four, rounded half up).
function halvePlane(n, p) {
  const h = n >> 1, out = new Uint8Array(h * h);
  for (let j = 0; j < h; j++) {
    for (let i = 0; i < h; i++) {
      out[j * h + i] = (p[2 * j * n + 2 * i] + p[2 * j * n + 2 * i + 1] + p[(2 * j + 1) * n + 2 * i]
        + p[(2 * j + 1) * n + 2 * i + 1] + 2) >> 2;
    }
  }
  return out;
}

// A brush that is a picture (rusemod.brushmask): (x, y) -> how much its mask lets through there (0..1), read in the
// stroke's own frame with the build's own sums; `edge` when the mask sets how far it reaches instead (`reach`: what
// the point's distance out is multiplied by). null without a mask; undefined while the masks are on their way.
function maskSampler(s) {
  if (!s.mask) return null;
  const mk = paint.masks;
  if (!mk || !mk.data) { loadMasks(); return undefined; }
  const data = mk.data[s.mask];
  if (!data) return null;
  const N = mk.size, shape = s.square ? "square" : s.shape || "round";
  let x = s.x, y = s.y, ax, ay;
  if (shape === "square") {
    const dx = s.dx === undefined ? 1 : s.dx, dy = s.dy === undefined ? 0 : s.dy, n = Math.sqrt(dx * dx + dy * dy) || 1;
    ax = dx / n; ay = dy / n;
  } else if (shape === "line" && (s.x2 !== s.x || s.y2 !== s.y)) {
    const sx = s.x2 - s.x, sy = s.y2 - s.y, n = Math.sqrt(sx * sx + sy * sy);
    ax = sx / n; ay = sy / n; x = s.x + sx / 2; y = s.y + sy / 2;
  } else {  // a round dab: one of the turnings, picked by where it is
    let h = ((Math.floor(s.x) * 92821 + Math.floor(s.y) * 68917 + 29) % MIX + MIX) % MIX;
    h = (h * h + 12345) % MIX;
    [ax, ay] = mk.turns[Math.floor(h * mk.turns.length / MIX)];
  }
  const span = 2 * s.radius, wrap = (k) => ((k % N) + N) % N;
  const f = (px, py) => {
    const ox = px - x, oy = py - y;
    const fu = ((ox * ax + oy * ay) / span + 0.5) * N - 0.5, fv = ((oy * ax - ox * ay) / span + 0.5) * N - 0.5;
    const gu = Math.floor(fu), gv = Math.floor(fv), tu = fu - gu, tv = fv - gv;
    const i0 = wrap(gu), i1 = wrap(gu + 1), j0 = wrap(gv) * N, j1 = wrap(gv + 1) * N;
    return ((data[j0 + i0] * (1 - tu) + data[j0 + i1] * tu) * (1 - tv)
      + (data[j1 + i0] * (1 - tu) + data[j1 + i1] * tu) * tv) / 255;
  };
  f.edge = mk.edge.includes(s.mask);
  f.reach = (m) => { const r = mk.ragIn + (1 - mk.ragIn) * m; return 1 / (r * r); };
  return f;
}

async function loadMasks() {
  if (paint.masks || !mv.api) return;
  paint.masks = { loading: true };
  try {
    const res = await mv.api.brush_masks();
    const data = {};
    for (const [name, b64] of Object.entries(res.masks)) data[name] = Uint8Array.from(atob(b64), (ch) => ch.charCodeAt(0));
    paint.masks = { size: res.size, turns: res.turns, edge: res.edge, ragIn: res.rag_in, names: Object.keys(res.masks),
      data };
  } catch (e) {
    paint.masks = { size: 0, turns: [], edge: [], ragIn: 1, names: [], data: {} };
  }
  paintRefresh();
  if (mv.gl) mv.gl.draw();
  renderPaintPanel();
}

const DITHER_MOST = 1.5 * 160;  // brushmask.DITHER_MOST: a speckled edge only on pixels this small at most
function ditherAt(s, px, py, pw, ph) {  // brushmask.dither_at: the same whole-number sums
  const i = Math.floor(px / pw), j = Math.floor(py / ph);
  const seed = ((Math.floor(s.x) * 31 + Math.floor(s.y) * 17) % MIX + MIX) % MIX;
  let h = ((i * 92821 + j * 68917 + seed) % MIX + MIX) % MIX;
  h = (h * h + 12345) % MIX;
  h = (h * h + 54321) % MIX;
  return (h + 0.5) / MIX;
}

const MIX = 65521;  // groundtex.MIX
function coin(k, salt) {  // groundtex.coin: the same whole-number sums, so the page mirrors the repeats the build does
  let h = ((k * 92821 + salt) % MIX + MIX) % MIX;
  h = (h * h + 12345) % MIX;
  h = (h * h + 54321) % MIX;
  return Math.floor(h * 2 / MIX);
}

async function loadSwatch(ref) {
  if (!ref || paint.swatches[ref]) return;
  const sw = paint.swatches[ref] = { loading: true };
  try {
    const res = await mv.api.ground_texture(ref);
    const img = new Image();
    img.src = res.png;
    await img.decode();
    const c = el("canvas", { width: res.n, height: res.n }), ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, 0, 0);
    const mips = [ctx.getImageData(0, 0, res.n, res.n).data];
    for (let n = res.n; n > 1; n >>= 1) mips.push(halveRgba(n, mips[mips.length - 1]));
    let grain = null;
    if (res.grain) {  // a palette swatch's grain: one byte a pixel (kept as grey), laid by itself over the colour
      const gi = new Image();
      gi.src = res.grain;
      await gi.decode();
      const gc = el("canvas", { width: res.grain_n, height: res.grain_n });
      const gctx = gc.getContext("2d", { willReadFrequently: true });
      gctx.drawImage(gi, 0, 0);
      const rgba = gctx.getImageData(0, 0, res.grain_n, res.grain_n).data, top = new Uint8Array(res.grain_n * res.grain_n);
      for (let q = 0; q < top.length; q++) top[q] = rgba[4 * q];
      grain = [top];
      for (let n = res.grain_n; n > 1; n >>= 1) grain.push(halvePlane(n, grain[grain.length - 1]));
    }
    Object.assign(sw, { loading: false, period: res.period, n: res.n, mips, png: res.png, mirrored: Boolean(res.mirrored),
      grain, grainN: res.grain_n || 0, grainPeriod: res.grain_period || 0, grainUnit: res.grain_unit || 100 });
  } catch (e) {
    Object.assign(sw, { loading: false, error: String((e && e.message) || e) });
    brushNote(fill(mv.words.tex_cant_read, { error: sw.error }), "error");
  }
  paintRefresh();
  if (mv.gl) mv.gl.draw();
  renderPaintPanel();
}

function gameTexture(ref) {
  return paint.textures ? paint.textures.byRef[ref] || null : null;
}

// What a texture is called: a game texture by its group and the words its name says (gtex_*), a map's square by its
// map, the mod's own picture by its file's name.
function textureName(ref) {
  const w = mv.words;
  if (!ref) return "";
  if (ref.startsWith("game:")) {
    const t = gameTexture(ref);
    if (!t) return ref.split("/").pop().replace(/_/g, " ");
    const group = w[`gtex_group_${t.group}`] || t.group;
    const said = t.words.filter((k) => k !== GROUP_WORD[t.group]).map((k) => w[`gtex_${k}`] || k.replace(/_/g, " "));
    return said.length ? `${group} · ${said.join(", ")}` : group;
  }
  if (ref.startsWith("map:")) return fill(w.tex_from_map_name, { map: mapName(ref.split(":")[1]) });
  if (ref.startsWith("swatch:")) {
    const p = paletteSwatch(ref), name = ref.split(":")[2];
    const said = w[`pal_${name}`] || (p ? p.label : name.replace(/_/g, " "));
    return p ? `${mapName(p.map)} · ${said}` : said;
  }
  return ref.slice(5).replace(/\.png$/i, "");
}

function paletteSwatch(ref) {  // the palette's row for it (StudioApi.ground_palette), once read
  return paint.materials ? paint.materials.find((p) => p.ref === ref) || null : null;
}

function textureWhere(t) {  // the decor sets a game texture is in, as the game's theatres
  return t.theatres.map((th) => mv.words[`gtex_theatre_${th}`] || th).join(", ");
}

function texturePeriod(ref) {  // map units it repeats every at its own size, when known
  const t = gameTexture(ref), sw = paint.swatches[ref], own = ownPicture(ref), p = paletteSwatch(ref);
  return t ? t.period : p ? p.period : sw && sw.period ? sw.period : own && own.period ? own.period
    : ref && ref.startsWith("map:") ? 81920 : ref ? 8192 : 0;
}

function ownPicture(ref) {  // the mod's own picture's row (StudioApi.ground_pictures: its period, metres, credit)
  return ref && ref.startsWith("file:") && paint.own ? paint.own.find((p) => p.ref === ref) || null : null;
}

function metresText(m) {  // metres said: whole ones from 10 m, else to a tenth
  return (m >= 10 ? Math.round(m) : Math.round(m * 10) / 10).toLocaleString();
}

function textureThumb(ref) {  // a small picture of it: the game's list's, or its own picture once in
  const t = gameTexture(ref), sw = paint.swatches[ref], p = paletteSwatch(ref);
  if (t) return paint.textures.base + t.thumb;
  if (p) return p.thumb;
  if (ref && ref.startsWith("file:") && paint.own) {
    const o = paint.own.find((p) => p.ref === ref);
    if (o) return o.thumb;
  }
  return sw && sw.png ? sw.png : "";
}

function pickTexture(ref) {
  if (ref !== paint.texture) paint.texScale = 0;  // a new texture starts at its own size
  paint.texture = ref;
  paint.picking = null;
  if (paint.from === "spot") paint.from = ref.startsWith("map:") ? "map" : ref.startsWith("file:") ? "own"
    : ref.startsWith("swatch:") ? "palette" : "game";
  loadSwatch(ref);
  renderPaintPanel();
  brushNote(fill(mv.words.tex_picked_note, { name: textureName(ref) }));
}

function textureUsed(ref) {
  if (paint.used[0] === ref) return;
  paint.used = [ref, ...paint.used.filter((r) => r !== ref)].slice(0, TEX_USED);
  renderTexturesUsed();
}

function renderTexturesUsed() {
  const w = mv.words, used = paint.used.filter((r) => r !== paint.texture || paint.from === "spot");
  $("tex-used-label").textContent = used.length ? w.tex_used : "";
  $("tex-used-label").title = w.tip_tex_used;
  $("tex-used").replaceChildren(...used.map((r) => textureButton(r, textureThumb(r), textureName(r))));
}

async function loadGameTextures() {
  if (paint.textures || paint.texLoading || !mv.api) return;
  paint.texLoading = true;
  const w = mv.words;
  try {
    let res = await mv.api.ground_textures();
    while (res && res.job) {
      let view, since = 0;
      do {
        await wait(700);
        view = await mv.api.job(res.job, since);
        since = view.count;
        if (view.lines.length) $("tex-state").textContent = fill(w.tex_loading, { progress: view.lines[view.lines.length - 1] });
      } while (view.state === "running");
      if (view.state !== "done") throw new Error(view.message);
      res = await mv.api.ground_textures();
    }
    const byRef = {};
    for (const t of res.textures) byRef[t.ref] = t;
    paint.textures = { base: res.base, list: res.textures, groups: res.groups, byRef };
  } catch (e) {
    $("tex-state").textContent = fill(w.tex_cant_read, { error: String((e && e.message) || e) });
  } finally {
    paint.texLoading = false;
  }
  renderPaintPanel();
}

async function loadPalette() {
  if (paint.materials || paint.matLoading || !mv.api) return;
  paint.matLoading = true;
  const w = mv.words;
  try {
    let res = await mv.api.ground_palette();
    while (res && res.job) {
      let view, since = 0;
      do {
        await wait(500);
        view = await mv.api.job(res.job, since);
        since = view.count;
        if (view.lines.length) $("tex-state").textContent = fill(w.tex_palette_loading, { progress: view.lines[view.lines.length - 1] });
      } while (view.state === "running");
      if (view.state !== "done") throw new Error(view.message);
      res = await mv.api.ground_palette();
    }
    if (res.error) throw new Error(res.error);
    paint.materials = res.swatches;
  } catch (e) {
    $("tex-state").textContent = fill(w.tex_cant_read, { error: String((e && e.message) || e) });
  } finally {
    paint.matLoading = false;
  }
  renderPaintPanel();
}

// The palette: each map's materials under its name (a field's rows laid the way Turn says).
function renderPalette() {
  const w = mv.words, list = paint.materials;
  if (!list) {
    $("tex-palette-grid").replaceChildren();
    if (!paint.matLoading) $("tex-state").textContent = fill(w.tex_palette_loading, { progress: "" });
    loadPalette();
    return;
  }
  const out = [];
  for (const map of [...new Set(list.map((p) => p.map))]) {
    out.push(el("div", { className: "muted small tex-theme", textContent: mapName(map) }));
    const grid = el("div", { className: "tex-grid", role: "group" });
    grid.append(...list.filter((p) => p.map === map).map((p) => textureButton(p.ref, p.thumb,
      fill(p.kind === "rows" ? w.tip_tex_palette_rows : w.tip_tex_palette, { name: textureName(p.ref),
        m: Math.round(p.period / METRE) }))));
    out.push(grid);
  }
  $("tex-palette-grid").replaceChildren(...out);
  $("tex-state").textContent = list.length ? "" : w.tex_none_found;
}

async function loadOwnPictures() {
  if (!mv.api) return;
  try {
    paint.own = (await mv.api.ground_pictures()).pictures;
  } catch (e) {
    paint.own = [];
  }
  renderPaintPanel();
}

// A picture button for the lists: its small picture over a checker (so see-through shows), its name as its tooltip.
function textureButton(ref, thumb, title) {
  const b = el("button", { type: "button", className: "tex-item", title });
  b.setAttribute("aria-pressed", String(paint.texture === ref && paint.from !== "spot"));
  b.setAttribute("aria-label", title);
  if (thumb) b.append(el("img", { src: thumb, alt: "", loading: "lazy", draggable: false }));
  b.addEventListener("click", () => pickTexture(ref));
  return b;
}

function renderGameTextures() {
  const w = mv.words, cat = paint.textures;
  if (!cat) {
    $("tex-groups").replaceChildren();
    $("tex-grid").replaceChildren();
    if (!paint.texLoading) $("tex-state").textContent = fill(w.tex_loading, { progress: "" });
    loadGameTextures();
    return;
  }
  const have = new Set(cat.list.map((t) => t.group));
  const chip = (g) => {
    const label = g === "all" ? w.tex_group_all : w[`gtex_group_${g}`] || g;
    const b = el("button", { type: "button", className: "chip", textContent: label,
      title: g === "all" ? w.tip_tex_group_all : fill(w.tip_tex_group, { group: label }) });
    b.setAttribute("aria-pressed", String(paint.texGroup === g));
    b.addEventListener("click", () => { paint.texGroup = g; renderPaintPanel(); });
    return b;
  };
  $("tex-groups").replaceChildren(...["all", ...cat.groups.filter((g) => have.has(g))].map(chip));
  const find = paint.texSearch.trim().toLowerCase();
  const shown = cat.list.filter((t) => (paint.texGroup === "all" || t.group === paint.texGroup)
    && (!find || `${textureName(t.ref)} ${textureWhere(t)}`.toLowerCase().includes(find)));
  $("tex-grid").replaceChildren(...shown.map((t) => textureButton(t.ref, cat.base + t.thumb,
    fill(t.see_through ? w.tip_tex_item_see : w.tip_tex_item, { name: textureName(t.ref), where: textureWhere(t),
      m: Math.round(t.period / METRE) }))));
  $("tex-state").textContent = shown.length ? "" : w.tex_none_found;
}

function renderOwnPictures() {
  const w = mv.words;
  if (paint.own === null || paint.ownFor !== mv.brush.mod) {  // (another mod picked: its own pictures)
    paint.own = [];
    paint.ownFor = mv.brush.mod;
    loadOwnPictures();
  }
  $("tex-own-grid").replaceChildren(...paint.own.map((p) => textureButton(p.ref, p.thumb, p.credit  // (online ones)
    ? fill(w.tip_tex_own_item_credit, { name: p.name, m: metresText((p.period || 8192) / METRE),
      source: p.credit.source || "", author: p.credit.author || "", licence: p.credit.licence || "" })
    : fill(w.tip_tex_own_item, { name: p.name }))));
  $("tex-state").textContent = paint.own.length ? "" : w.tex_own_none;
}

function renderMapPick() {
  const w = mv.words, list = $("tex-map-list");
  if (list.options.length !== mv.maps.length) {
    list.replaceChildren(el("option", { value: "", textContent: w.tex_map_choose }),
      ...mv.maps.map((m) => el("option", { value: m.pack, textContent: mapName(m.pack) })));
  }
  list.value = paint.mapPick ? paint.mapPick.pack : "";
  const pic = $("tex-map-pic");
  pic.classList.toggle("hidden", !paint.mapPick || !paint.mapPick.picture);
  if (paint.mapPick && paint.mapPick.picture && pic.src !== paint.mapPick.picture) pic.src = paint.mapPick.picture;
  pic.title = w.tip_tex_map_pic;
  $("tex-state").textContent = !paint.mapPick ? w.tex_map_first : paint.mapPick.picture ? w.tex_map_click : "";
}

async function chooseMapToPick(pack) {
  paint.mapPick = pack ? { pack, picture: null, bounds: null } : null;
  renderPaintPanel();
  if (!pack) return;
  try {
    const res = await mv.api.map_overview(pack);
    if (paint.mapPick && paint.mapPick.pack === pack) Object.assign(paint.mapPick, res);
  } catch (e) {
    brushNote(fill(mv.words.tex_cant_read, { error: String((e && e.message) || e) }), "error");
  }
  renderPaintPanel();
}

async function takeMapSquare(ev) {  // a click on the map's overview: the square of its ground there
  const p = paint.mapPick, img = $("tex-map-pic");
  if (!p || !p.bounds) return;
  const r = img.getBoundingClientRect(), [x0, y0, x1, y1] = p.bounds;
  const x = x0 + (ev.clientX - r.left) / r.width * (x1 - x0), y = y0 + (ev.clientY - r.top) / r.height * (y1 - y0);
  $("tex-state").textContent = mv.words.tex_map_taking;
  try {
    const res = await mv.api.map_texture(p.pack, x, y);
    pickTexture(res.ref);
    brushNote(fill(mv.words.tex_map_taken, { map: mapName(p.pack) }));
  } catch (e) {
    brushNote(fill(mv.words.tex_cant_read, { error: String((e && e.message) || e) }), "error");
    renderPaintPanel();
  }
}

// A picture's middle square as a PNG data URL, n pixels across, n the largest power of two no more than its side or
// 1,024 (groundtex.square's sizes): any picture the browser can show (the app has no JPG reader of its own).
async function squarePng(src) {
  const img = new Image();
  img.src = src;
  await img.decode();
  const side = Math.min(img.naturalWidth, img.naturalHeight);
  let n = 1;
  while (n * 2 <= Math.min(side, 1024)) n *= 2;
  const c = el("canvas", { width: n, height: n }), ctx = c.getContext("2d");
  ctx.imageSmoothingQuality = "high";
  ctx.drawImage(img, (img.naturalWidth - side) / 2, (img.naturalHeight - side) / 2, side, side, 0, 0, n, n);
  return c.toDataURL("image/png");
}

// Your own picture: any picture the browser can show, its middle square (1,024 pixels at most) made a PNG here and
// kept in the mod (files/ground), then picked.
async function addOwnPicture(file) {
  const w = mv.words;
  if (!file) return;
  if (!mv.brush.mod) { brushNote(w.no_mod, "error"); return; }
  try {
    const url = URL.createObjectURL(file);
    let png;
    try {
      png = await squarePng(url);
    } finally {
      URL.revokeObjectURL(url);
    }
    const res = await mv.api.add_ground_picture(file.name, png);
    paint.own = res.pictures;
    pickTexture(res.ref);
    brushNote(fill(w.tex_own_added, { name: textureName(res.ref) }));
  } catch (e) {
    brushNote(fill(w.tex_cant_read, { error: String((e && e.message) || e) }), "error");
  }
}

// Online (free) (StudioApi.online_textures, online_texture): Poly Haven's and ambientCG's textures (CC0), shown by
// their own small pictures, and US aerial photos (public domain) of the places named or of a typed latitude and
// longitude. A click downloads only that one picture; it's kept in the mod like your own (with its real size and
// credit, files/ground/<name>.toml) and picked. The owner, 2026-10-09: "the more, the merrier".
function onlineLabel(src) {
  const w = mv.words;
  return src === "polyhaven" ? w.tex_online_polyhaven : src === "ambientcg" ? w.tex_online_ambientcg : w.tex_online_usgs;
}

async function loadOnline(src, words) {
  const o = paint.online, key = `${src}:${words}`;
  if (o.loading === key || !mv.api) return;
  o.loading = key;
  try {
    const res = await mv.api.online_textures(src, words);
    o.lists[src] = Object.assign(res, { asked: words });
    o.error = "";
  } catch (e) {
    o.error = String((e && e.message) || e);
    o.errorFor = key;
  } finally {
    if (o.loading === key) o.loading = "";
  }
  renderPaintPanel();
}

function onlineButton(src, t, licence) {  // a Poly Haven or ambientCG texture: its site's small picture
  const w = mv.words, o = paint.online;
  const title = fill(t.metres ? w.tip_tex_online_item : w.tip_tex_online_item_nosize,
    { name: t.name, m: t.metres ? metresText(t.metres) : "", author: t.author || "", licence });
  const b = el("button", { type: "button", className: "tex-item", title });
  b.setAttribute("aria-label", title);
  if (o.busy === `${src}:${t.id}`) b.setAttribute("aria-busy", "true");
  if (t.thumb) b.append(el("img", { src: t.thumb, alt: "", loading: "lazy", draggable: false, referrerPolicy: "no-referrer" }));
  b.addEventListener("click", () => takeOnline(src, t.id, t.name));
  return b;
}

function placeChip(p) {  // a US place to photograph, by its name in the Studio's language
  const w = mv.words, o = paint.online, name = w[`tex_place_${p.id}`] || p.name;
  const title = fill(w.tip_tex_place, { place: name, lat: p.lat, lon: p.lon, m: metresText(o.metres) });
  const b = el("button", { type: "button", className: "chip", textContent: name, title });
  if (o.busy === `usgs:${p.id}`) b.setAttribute("aria-busy", "true");
  b.addEventListener("click", () => takeOnline("usgs", p.id, name));
  return b;
}

function renderOnline() {
  const w = mv.words, o = paint.online, src = o.from;
  const subs = [["polyhaven", w.tex_online_polyhaven, w.tip_tex_online_polyhaven],
    ["ambientcg", w.tex_online_ambientcg, w.tip_tex_online_ambientcg], ["usgs", w.tex_online_usgs, w.tip_tex_online_usgs]];
  $("tex-online-from").replaceChildren(...subs.map(([key, label, tip]) => {
    const b = el("button", { type: "button", className: "chip", textContent: label, title: tip });
    b.setAttribute("aria-pressed", String(src === key));
    b.addEventListener("click", () => { o.from = key; o.error = ""; renderPaintPanel(); });
    return b;
  }));
  const search = $("tex-online-search"), usgs = src === "usgs";
  search.placeholder = usgs ? w.tex_online_find_place : w.tex_online_search;
  search.title = usgs ? w.tip_tex_online_find_place : src === "ambientcg" ? w.tip_tex_online_search_site
    : w.tip_tex_online_search;
  search.setAttribute("aria-label", search.title);
  if (search.value !== o.search[src]) search.value = o.search[src];
  $("tex-online-place").classList.toggle("hidden", !usgs);
  $("tex-online-note").textContent = usgs ? w.tex_online_note_usgs : src === "ambientcg" ? w.tex_online_note_ambientcg
    : w.tex_online_note_polyhaven;
  const grid = $("tex-online-grid");
  grid.classList.toggle("tex-places", usgs);
  const want = src === "ambientcg" ? o.asked : "", list = o.lists[src];
  const state = (text) => { $("tex-state").textContent = o.busy ? fill(w.tex_online_getting, { name: o.busyName }) : text; };
  if (!list || list.asked !== want) {
    grid.replaceChildren();
    if (o.error && o.errorFor === `${src}:${want}`) {
      state(fill(w.tex_online_cant_list, { source: onlineLabel(src), error: o.error }));
    } else {
      state(fill(w.tex_online_listing, { source: onlineLabel(src) }));
      loadOnline(src, want);
    }
    return;
  }
  const find = o.search[src].trim().toLowerCase();
  let shown;
  if (usgs) {
    const metres = $("tex-online-metres");
    if (metres.options.length !== list.metres.length) {
      metres.replaceChildren(...list.metres.map((m) => el("option", { value: String(m),
        textContent: fill(w.tex_online_m, { m: metresText(m) }) })));
    }
    metres.value = String(o.metres);
    metres.title = w.tip_tex_online_metres;
    $("tex-online-metres-label").textContent = w.tex_online_metres;
    const where = $("tex-online-where");
    where.placeholder = w.tex_online_where;
    where.title = w.tip_tex_online_where;
    where.setAttribute("aria-label", w.tip_tex_online_where);
    if (where.value !== o.where) where.value = o.where;
    $("tex-online-take").textContent = w.tex_online_take;
    $("tex-online-take").title = w.tip_tex_online_take;
    shown = list.items.filter((p) => !find || `${w[`tex_place_${p.id}`] || ""} ${p.name}`.toLowerCase().includes(find));
    grid.replaceChildren(...shown.map((p) => placeChip(p)));
  } else {
    shown = src === "ambientcg" ? list.items  // (its site found them by the words typed)
      : list.items.filter((t) => !find || `${t.name} ${t.tags.join(" ")}`.toLowerCase().includes(find));
    grid.replaceChildren(...shown.map((t) => onlineButton(src, t, list.licence)));
  }
  state(shown.length ? "" : w.tex_online_none);
}

async function takeOnline(src, id, name) {  // download one picture and keep it in the mod: `id` "" for a typed place
  const w = mv.words, o = paint.online;
  if (!mv.brush.mod) { brushNote(w.no_mod, "error"); return; }
  if (o.busy) return;  // one at a time
  if (src === "usgs" && !id && !o.where.trim()) { brushNote(w.tex_online_where_first, "error"); return; }
  o.busy = `${src}:${id}`;
  o.busyName = name || o.where.trim();
  renderPaintPanel();
  try {
    const got = await mv.api.online_texture(src, id, src === "usgs" ? o.metres : 0, id ? "" : o.where);
    const png = await squarePng(got.picture);
    const res = await mv.api.add_ground_picture(got.name, png, got.metres, got.credit);
    paint.own = res.pictures;
    paint.ownFor = mv.brush.mod;
    o.busy = "";
    pickTexture(res.ref);
    brushNote(fill(w.tex_online_added, { name: textureName(res.ref), source: got.credit.source }));
  } catch (e) {
    o.busy = "";
    brushNote(fill(w.tex_online_cant, { error: String((e && e.message) || e) }), "error");
    renderPaintPanel();
  }
}

function renderTexturePanel() {
  const w = mv.words, from = paint.from;
  const sources = [["palette", w.tex_from_palette, w.tip_tex_from_palette], ["game", w.tex_from_game,
    w.tip_tex_from_game], ["map", w.tex_from_map, w.tip_tex_from_map], ["own", w.tex_from_own, w.tip_tex_from_own],
    ["online", w.tex_from_online, w.tip_tex_from_online], ["spot", w.tex_from_spot, w.tip_tex_from_spot]];
  $("tex-from").replaceChildren(...sources.map(([key, label, tip]) => {
    const b = el("button", { type: "button", className: "chip", textContent: label, title: tip });
    b.setAttribute("aria-pressed", String(from === key));
    b.addEventListener("click", () => { paint.from = key; paint.picking = null; renderPaintPanel(); brushNote(""); });
    return b;
  }));
  for (const key of ["palette", "game", "map", "own", "online", "spot"]) {
    $(`tex-${key}`).classList.toggle("hidden", from !== key);
  }
  const search = $("tex-search");
  search.placeholder = w.tex_search;
  search.title = w.tip_tex_search;
  search.setAttribute("aria-label", w.tip_tex_search);
  $("tex-map-list").title = w.tip_tex_map_list;
  $("tex-add").textContent = w.tex_own_add;
  $("tex-add").title = w.tip_tex_own_add;
  if (from === "palette") renderPalette();
  else if (from === "game") renderGameTextures();
  else if (from === "map") renderMapPick();
  else if (from === "own") renderOwnPictures();
  else if (from === "online") renderOnline();
  else $("tex-state").textContent = "";
  const picked = from !== "spot" && paint.texture;
  $("tex-now").classList.toggle("hidden", !picked);
  $("tex-size-row").classList.toggle("hidden", !picked);
  $("tex-turn-row").classList.toggle("hidden", !picked);
  if (picked) {
    const turn = $("tex-turn"), rows = paletteSwatch(paint.texture);
    turn.value = String(paint.texTurn);
    turn.title = w.tip_tex_turn;
    $("tex-turn-label").textContent = fill(rows && rows.kind === "rows" ? w.tex_turn_rows : w.tex_turn,
      { deg: paint.texTurn });
    const thumb = textureThumb(paint.texture), now = $("tex-now-pic");
    now.style.backgroundImage = thumb ? `url("${thumb}")` : "";
    $("tex-now-name").textContent = textureName(paint.texture);
    const own = ownPicture(paint.texture), credit = own && own.credit;  // (an online one says whose it is)
    $("tex-now").title = credit ? fill(w.tip_tex_now_credit, { source: credit.source || "", author: credit.author || "",
      licence: credit.licence || "" }) : w.tip_tex_now;
    const rep = texturePeriod(paint.texture) * Math.pow(2, paint.texScale), size = $("tex-size");
    size.min = String(TEX_SCALES[0]);
    size.max = String(TEX_SCALES[1]);
    size.value = String(paint.texScale);
    size.title = w.tip_tex_size;
    $("tex-size-label").textContent = fill(w.tex_size, { m: (rep >= 10 * METRE ? Math.round(rep / METRE)
      : Math.round(rep / METRE * 10) / 10).toLocaleString() });
  }
  renderTexturesUsed();
}

function rgbHsv([r, g, b]) {
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
  let h = 0;
  if (d) h = max === r ? ((g - b) / d) % 6 : max === g ? (b - r) / d + 2 : (r - g) / d + 4;
  return [(h * 60 + 360) % 360, max ? d / max : 0, max];
}

function hsvRgb(h, s, v) {
  const f = (n) => { const k = (n + h / 60) % 6; return v - v * s * Math.max(0, Math.min(k, 4 - k, 1)); };
  return [f(5) * 255, f(3) * 255, f(1) * 255];
}

// The map's own ground colours, for the palette: its picture sampled on a grid, gathered into the colours it holds
// most (near ones as one), the commonest first.
function mapColours(most = 10) {
  if (!paintSurface()) return [];
  if (paint.palette) return paint.palette;
  const c = paint.canvas, d = paint.base.data, bins = new Map(), N = 64;
  for (let j = 0; j < N; j++) {
    for (let i = 0; i < N; i++) {
      const k = 4 * (Math.floor((j + 0.5) / N * c.height) * c.width + Math.floor((i + 0.5) / N * c.width));
      const key = (d[k] >> 4) << 8 | (d[k + 1] >> 4) << 4 | (d[k + 2] >> 4);
      const b = bins.get(key) || [0, 0, 0, 0];
      b[0] += d[k]; b[1] += d[k + 1]; b[2] += d[k + 2]; b[3] += 1;
      bins.set(key, b);
    }
  }
  const out = [];
  for (const b of [...bins.values()].sort((p, q) => q[3] - p[3])) {
    const rgb = [b[0] / b[3], b[1] / b[3], b[2] / b[3]];
    if (out.some((o) => Math.hypot(o[0] - rgb[0], o[1] - rgb[1], o[2] - rgb[2]) < 28)) continue;
    out.push(rgb);
    if (out.length >= most) break;
  }
  paint.palette = out.map(rgbHex);
  return paint.palette;
}

// The colour picked: from the wheel, the box, a swatch or the eyedropper.
function setPaintColour(hex, keep) {
  paint.colour = hex.toLowerCase();
  if (keep) rememberColour(paint.colour);
  renderPaintPanel();
  const gl = mv.gl;
  if (gl && gl.ring && mv.brush.on && mv.brush.name === "paint") { gl.ring.material.color.set(paint.colour); gl.draw(); }
}

function rememberColour(hex) {
  paint.recent = [hex, ...paint.recent.filter((c) => c !== hex)].slice(0, 8);
}

// The colour wheel: hue round the ring, how strong and how light in the square inside it.
const WHEEL = 150, WHEEL_OUT = 74, WHEEL_IN = 60, WHEEL_HALF = (WHEEL_IN - 5) / Math.SQRT2;
function drawWheel() {
  const canvas = $("paint-wheel");
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  if (canvas.width !== WHEEL * dpr) { canvas.width = canvas.height = WHEEL * dpr; }
  const ctx = canvas.getContext("2d"), c = WHEEL / 2;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, WHEEL, WHEEL);
  const ring = ctx.createConicGradient(0, c, c);
  for (let h = 0; h <= 360; h += 30) ring.addColorStop(h / 360, `hsl(${h} 100% 50%)`);
  ctx.beginPath();
  ctx.arc(c, c, WHEEL_OUT, 0, 2 * Math.PI);
  ctx.arc(c, c, WHEEL_IN, 0, 2 * Math.PI, true);
  ctx.fillStyle = ring;
  ctx.fill("evenodd");
  const [h, s, v] = rgbHsv(hexRgb(paint.colour)), a = c - WHEEL_HALF, side = 2 * WHEEL_HALF;
  ctx.fillStyle = `hsl(${h} 100% 50%)`;
  ctx.fillRect(a, a, side, side);
  const white = ctx.createLinearGradient(a, 0, a + side, 0);
  white.addColorStop(0, "#fff");
  white.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = white;
  ctx.fillRect(a, a, side, side);
  const black = ctx.createLinearGradient(0, a, 0, a + side);
  black.addColorStop(0, "rgba(0,0,0,0)");
  black.addColorStop(1, "#000");
  ctx.fillStyle = black;
  ctx.fillRect(a, a, side, side);
  const mark = (x, y) => {
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, 2 * Math.PI);
    ctx.lineWidth = 2;
    ctx.strokeStyle = "#fff";
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(x, y, 6.5, 0, 2 * Math.PI);
    ctx.lineWidth = 1;
    ctx.strokeStyle = "#000";
    ctx.stroke();
  };
  const t = h * Math.PI / 180, mid = (WHEEL_IN + WHEEL_OUT) / 2;
  mark(c + Math.cos(t) * mid, c + Math.sin(t) * mid);
  mark(a + s * side, a + (1 - v) * side);
}

function wheelPick(ev, part) {
  const rect = $("paint-wheel").getBoundingClientRect(), c = WHEEL / 2;
  const x = (ev.clientX - rect.left) * WHEEL / rect.width - c, y = (ev.clientY - rect.top) * WHEEL / rect.height - c;
  let [h, s, v] = rgbHsv(hexRgb(paint.colour));
  if (part === "hue") h = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
  else {
    s = Math.min(1, Math.max(0, (x + WHEEL_HALF) / (2 * WHEEL_HALF)));
    v = Math.min(1, Math.max(0, 1 - (y + WHEEL_HALF) / (2 * WHEEL_HALF)));
  }
  if (part === "hue" && s === 0) s = 1;  // a grey turned on the ring takes the colour, not stays grey
  setPaintColour(rgbHex(hsvRgb(h, s, v)));
}

// The Colour and Texture panels under the brushes: what's picked, and the ways to pick it.
function renderPaintPanel() {
  const w = mv.words, name = mv.brush.name, on = mv.brush.on && PAINT_KINDS.has(BRUSHES[name][0]);
  $("brush-paint").classList.toggle("hidden", !on);
  if (!on) return;
  const colour = name === "paint";
  $("paint-colour").classList.toggle("hidden", !colour);
  $("paint-stamp").classList.toggle("hidden", colour);
  if (colour) {
    $("paint-swatch").style.background = paint.colour;
    $("paint-swatch").title = w.tip_paint_swatch_now;
    const hex = $("paint-hex");
    if (document.activeElement !== hex) hex.value = paint.colour;
    hex.title = w.tip_paint_hex;
    hex.setAttribute("aria-label", w.tip_paint_hex);
    $("paint-wheel").title = w.tip_paint_wheel;
    $("paint-wheel").setAttribute("aria-label", w.tip_paint_wheel);
    const dropper = $("paint-dropper");
    dropper.textContent = w.paint_eyedropper;
    dropper.title = w.tip_paint_eyedropper;
    dropper.setAttribute("aria-pressed", String(paint.picking === "colour"));
    const swatch = (hex) => {
      const b = el("button", { type: "button", className: "swatch", title: `${w.tip_paint_swatch} (${hex})` });
      b.style.background = hex;
      b.setAttribute("aria-pressed", String(hex === paint.colour));
      b.setAttribute("aria-label", hex);
      b.addEventListener("click", () => setPaintColour(hex, true));
      return b;
    };
    $("paint-map-label").textContent = w.paint_map_colours;
    $("paint-map-label").title = w.tip_paint_map_colours;
    $("paint-map").replaceChildren(...mapColours().map(swatch));
    $("paint-recent-label").textContent = w.paint_recent;
    $("paint-recent-label").classList.toggle("hidden", !paint.recent.length);
    $("paint-recent").replaceChildren(...paint.recent.map(swatch));
    drawWheel();
  } else {
    renderTexturePanel();
    const pick = $("stamp-pick");
    pick.textContent = w.stamp_pick;
    pick.title = w.tip_stamp_pick;
    pick.setAttribute("aria-pressed", String(paint.picking === "source"));
    $("stamp-state").textContent = paint.from !== "spot" ? ""
      : paint.picking === "source" ? w.stamp_pick_help : paint.source || paint.offset ? w.stamp_from : w.stamp_from_none;
  }
  renderMaskPicker();
  const dither = $("paint-dither");  // a speckled edge (brushmask.dither_at), on the finest level only
  dither.textContent = w.paint_dither;
  dither.title = w.tip_paint_dither;
  dither.setAttribute("aria-pressed", String(paint.dither));
  const clear = $("paint-clear");
  clear.textContent = w.paint_clear;
  clear.title = w.tip_paint_clear;
  clear.setAttribute("aria-pressed", String(paint.clear));
  const decals = $("paint-decals");  // the game's own decals up close: for the game's textures only
  decals.classList.toggle("hidden", colour || paint.from === "spot" || !String(paint.texture || "").startsWith("game:"));
  decals.textContent = w.paint_decals;
  decals.title = w.tip_paint_decals;
  decals.setAttribute("aria-pressed", String(paint.decals));
  $("paint-note").textContent = !colour && paint.from !== "spot" ? w.tex_note : w.paint_note;
}

// The brush's pattern (rusemod.brushmask): plain, or one of the masks, each shown as a small picture of itself.
const maskThumbs = {};
function maskThumb(name) {
  const mk = paint.masks;
  if (maskThumbs[name] || !mk || !mk.data || !mk.data[name]) return maskThumbs[name] || "";
  const N = mk.size, c = el("canvas", { width: N, height: N }), ctx = c.getContext("2d"), img = ctx.createImageData(N, N);
  for (let k = 0; k < N * N; k++) {
    const v = mk.data[name][k];
    img.data.set([v, v, v, 255], 4 * k);
  }
  ctx.putImageData(img, 0, 0);
  maskThumbs[name] = c.toDataURL();
  return maskThumbs[name];
}

function renderMaskPicker() {
  const w = mv.words, mk = paint.masks;
  $("paint-mask-label").textContent = w.paint_mask;
  $("paint-mask-label").title = w.tip_paint_mask;
  if (!mk || !mk.names) { loadMasks(); $("paint-mask").replaceChildren(); return; }
  $("paint-mask").replaceChildren(...["", ...mk.names].map((name) => {
    const label = w[`mask_${name || "none"}`] || name;
    const b = el("button", { type: "button", className: "chip mask-chip", title: fill(w.tip_paint_mask_one,
      { name: label }) });
    const thumb = name ? maskThumb(name) : "";
    if (thumb) b.append(el("img", { src: thumb, alt: "", draggable: false }));
    b.append(document.createTextNode(label));
    b.setAttribute("aria-pressed", String(paint.mask === name));
    b.addEventListener("click", () => { paint.mask = name; renderPaintPanel(); });
    return b;
  }));
}

// The colour of the object under the pointer (a building, a prop, a tree drawn with its real model), for matching the
// ground to it (the owner, 2026-10-03: "a paint matcher so you can match the colors of certain objects"): the texel of
// its own picture where the ray meets it, so its colour without the light, as the ground's picture is.
// { hex, name } or null when no model is there (or the ground is in front of it, or that spot of it is see-through).
const texels = new WeakMap();  // a model's picture -> its pixels, read once
function objectColourAt(ev) {
  const gl = mv.gl, d = mv.scenery.data;
  const meshes = Object.values(mv.scenery.models || {}).flat().filter((m) => m.visible && m.userData.real);
  if (!meshes.length) return null;
  const rect = gl.renderer.domElement.getBoundingClientRect();
  gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  gl.raycaster.setFromCamera(gl.ndc, gl.camera);
  const hit = gl.raycaster.intersectObjects(meshes, false)[0];
  if (!hit || !hit.uv || hit.instanceId === undefined) return null;
  const ground = gl.raycaster.intersectObject(gl.ground, false)[0];
  if (ground && ground.distance < hit.distance) return null;
  const map = hit.object.material.map, img = map && map.image;
  if (!img || !img.width) return null;
  let px = texels.get(img);
  if (!px) {
    const c = el("canvas", { width: img.width, height: img.height }), ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, 0, 0);
    px = ctx.getImageData(0, 0, img.width, img.height);
    texels.set(img, px);
  }
  const u = hit.uv.x - Math.floor(hit.uv.x), v = hit.uv.y - Math.floor(hit.uv.y);
  const col = Math.min(px.width - 1, Math.floor(u * px.width));
  const row = Math.min(px.height - 1, Math.floor((map.flipY ? 1 - v : v) * px.height));
  const k = 4 * (row * px.width + col);
  if (hit.object.material.alphaTest && px.data[k + 3] < 128) return null;  // a see-through bit (between a tree's leaves)
  const { flat, rows } = hit.object.userData, t = d && d.types[flat[5 * rows[hit.instanceId]]];
  return { hex: rgbHex([px.data[k], px.data[k + 1], px.data[k + 2]]), name: t ? t[0] : "" };
}

// A click while picking: the colour there (the eyedropper, or Alt+click with Colour: an object's own colour when one
// is clicked, else the ground's), or where Texture copies from (its button, or Alt+click with Texture). True when the
// click was taken.
function paintPick(x, y, alt, ev) {
  const name = mv.brush.name;
  if (!PAINT_KINDS.has(name) || !(paint.picking || alt)) return false;
  if (name === "paint") {
    const obj = ev ? objectColourAt(ev) : null, hex = obj ? obj.hex : paintColourAt(x, y);
    paint.picking = null;
    if (hex) setPaintColour(hex, true);
    else renderPaintPanel();
    brushNote(!hex ? "" : obj ? fill(mv.words.paint_took_object, { name: obj.name || "?", hex })
      : fill(mv.words.paint_took, { hex }));
    return true;
  }
  paint.source = { x, y };
  paint.offset = null;
  paint.picking = null;
  paint.from = "spot";  // (Alt+click with a texture picked: this map's own ground from here instead)
  renderPaintPanel();
  brushNote(mv.words.stamp_picked);
  return true;
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
  paintRefresh();  // the paint again, on the sharper picture
  mv.gl.draw();
  note.textContent = "";
}

// --- the real 3D models (StudioApi.map_models: the game's .spk models and their atlases, made once per map and
// kept in the cache; from DomesticNukes and his Claude's notes). Until they're in, and for a type without a model,
// the simple shapes below stand in. Each type is one instanced mesh per part (a part: one atlas), drawn where the
// shapes stand; the shapes stay, unseen, for pointing at things (sceneryAt). ---
// `blank`: a map started blank has none of the map's models to load, only the mod's own (ownModels).
async function loadModels(pack, ask, blank) {
  const w = mv.words, note = $("map-ground");
  let res = blank ? null : await mv.api.map_models(pack);
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
  if ((!blank && (!res || !res.index)) || ask !== mv.ask || !mv.scenery.data) return;
  note.textContent = fill(w.models_loading, { progress: "" });
  const sources = [], kept = mv.scenery.mapSource;  // (the map's, kept: the mod's own are loaded again on a change)
  if (!blank) {
    const url = res.base + res.index.bin;
    const buf = kept && kept.url === url ? kept.buf : await (await fetch(url)).arrayBuffer();
    sources.push(mv.scenery.mapSource = { url, base: res.base, index: res.index, buf });
  }
  const mine = await ownModels(ask);
  if (ask !== mv.ask) return;
  if (mine) sources.push(mine);
  if (!sources.length) { note.textContent = ""; return; }  // a blank map, and the mod has no models of its own
  const lib = modelLibrary(sources);
  clearModels();
  mv.scenery.lib = lib;
  const { THREE } = mv.gl, models = {};
  for (const [group, mesh] of Object.entries(mv.scenery.meshes)) {
    const flat = mesh.userData.flat, byType = new Map();
    for (let k = 0; k < flat.length / 5; k++) {
      const t = flat[5 * k];
      if (lib.has(t)) (byType.get(t) || byType.set(t, []).get(t)).push(k);
    }
    const list = [], rest = [];
    for (let k = 0; k < flat.length / 5; k++) if (!byType.has(flat[5 * k])) rest.push(k);
    for (const [t, rows] of byType) {
      for (const part of lib.parts(t)) {
        const inst = new THREE.InstancedMesh(part.geo, lib.material(group, part), rows.length);
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
  placeScenery();  // (draws what the mod places with its models too)
  placeOptions();  // the place list's pictures
  note.textContent = "";
}

function clearModels() {
  for (const list of Object.values(mv.scenery.models || {})) for (const m of list) forget(m);
  mv.scenery.models = {};
  if (mv.scenery.lib) {
    const lib = mv.scenery.lib;
    mv.scenery.lib = null;
    drawPlaced();         // what the mod places goes back to its shapes, off the library's models
    showPlaceGhost(null);
    lib.dispose();
  }
}

// The models once in, for everything that draws a type: the map's own objects, what the mod places, the ghost at the
// pointer and the place list's pictures. `sources`: [{ base, index, buf }], map_models' and the mod's own (ownModels:
// numbered after the map's types), an index's models by type number. parts(t): a type's parts ({ geo, texture, src }),
// made once; material(group, part): a new material on the part's shared picture; ready(t): its pictures loaded.
function modelLibrary(sources) {
  const { THREE } = mv.gl, types = mv.scenery.data.types, textures = new Map(), geometries = {};
  const sourceOf = (t) => sources.find((s) => s.index.models[t] && s.index.models[t].length) || null;
  const textureOf = (key, src) => {
    if (!key || !src || !src.index.textures[key]) return null;
    if (!textures.has(src)) textures.set(src, {});
    const mine = textures.get(src);
    if (!mine[key]) {
      const tex = new THREE.Texture();
      tex.flipY = false;  // the game's UVs start at the picture's top
      tex.colorSpace = THREE.SRGBColorSpace;
      tex.userData.keep = true;  // shared by many meshes: forget() leaves it, the library's dispose() frees it
      const ready = new Promise((done) => {
        const img = new Image();
        img.onload = () => { tex.image = bleed(img); tex.needsUpdate = true; if (mv.gl) mv.gl.draw(); done(); };
        img.onerror = () => done();
        img.src = src.base + src.index.textures[key];
      });
      mine[key] = { tex, ready };
    }
    return mine[key];
  };
  const has = (t) => sourceOf(t) !== null;
  const parts = (t) => {
    if (geometries[t]) return geometries[t];
    // a tree's leaves are cards whose normals point out of the crown, lit the same from either side: each gets a face
    // both ways round (drawn front side only), as one face seen from behind turned its normal away from the light and
    // the leaves came out black (the owner, 2026-10-15: the trees were flat "sprites")
    const twoWay = (types[t] || [])[1] === "vegetation", src = sourceOf(t), buf = src && src.buf;
    return (geometries[t] = ((src && src.index.models[t]) || []).map((p) => {
      const n = p.vertices;
      const src = new Float32Array(buf, p.positions, 3 * n), pos = new Float32Array(3 * n);
      for (let i = 0; i < n; i++) {  // map units, x east, y south, z up -> the scene's x east, y up, z south
        pos[3 * i] = src[3 * i]; pos[3 * i + 1] = src[3 * i + 2]; pos[3 * i + 2] = src[3 * i + 1];
      }
      const nsrc = new Int8Array(buf, p.normals, 4 * n), nrm = new Float32Array(3 * n);
      for (let i = 0; i < n; i++) {
        nrm[3 * i] = nsrc[4 * i] / 127; nrm[3 * i + 1] = nsrc[4 * i + 2] / 127; nrm[3 * i + 2] = nsrc[4 * i + 1] / 127;
      }
      const tri = new Uint32Array(buf, p.indices, 3 * p.triangles), index = new Uint32Array((twoWay ? 2 : 1) * tri.length);
      index.set(tri);
      if (twoWay) {
        for (let i = 0; i < tri.length; i += 3) {
          index[tri.length + i] = tri[i]; index[tri.length + i + 1] = tri[i + 2]; index[tri.length + i + 2] = tri[i + 1];
        }
      }
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      geo.setAttribute("normal", new THREE.BufferAttribute(nrm, 3));
      geo.setAttribute("uv", new THREE.BufferAttribute(new Float32Array(buf, p.uvs, 2 * n).slice(), 2));
      geo.setIndex(new THREE.BufferAttribute(index, 1));
      geo.computeBoundingBox();
      geo.userData.keep = true;  // shared: forget() leaves it, the library's dispose() frees it
      return { geo, texture: p.texture, twoWay, src };
    }));
  };
  // A "CombinedDS" picture's alpha isn't see-through: on Kasserine Pass's map most of it is under half (89 % of one
  // atlas) while its models (baskets, barrels, fences, cushions) are solid, and cutting at half left them all but
  // invisible, in the view and in the place list. Those are drawn solid; the others cut their leaves and windows out.
  const material = (group, part) => {
    const t = textureOf(part.texture, part.src), side = part.twoWay ? THREE.FrontSide : THREE.DoubleSide;
    const cut = /CombinedDSTexture/i.test(part.texture || "") ? 0 : 0.5;
    return new THREE.MeshLambertMaterial(t ? { map: t.tex, alphaTest: cut, side } : { color: SCENERY_LOOK[group][3], side });
  };
  const ready = (t) => Promise.all(parts(t).map((p) => (textureOf(p.texture, p.src) || {}).ready));
  const dispose = () => {
    for (const mine of textures.values()) for (const { tex } of Object.values(mine)) tex.dispose();
    for (const list of Object.values(geometries)) for (const p of list) p.geo.dispose();
  };
  return { has, parts, material, ready, dispose };
}

// A model's picture with its see-through pixels coloured like the leaf or edge beside them (up to BLEED pixels out):
// the game's pictures leave them black, which darkened every leaf's edge where the picture is drawn smaller or between
// its pixels. The see-through stays see-through; a picture without any is left as it is.
const BLEED = 8;
function bleed(img) {
  const w = img.naturalWidth || img.width, h = img.naturalHeight || img.height, n = w * h;
  const c = el("canvas", { width: w, height: h }), ctx = c.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0);
  const data = ctx.getImageData(0, 0, w, h), p = data.data, done = new Uint8Array(n), queued = new Uint8Array(n);
  for (let i = 0; i < n; i++) if (p[4 * i + 3]) done[i] = 1;
  const around = (i) => {
    const x = i % w, out = [];
    if (x > 0) out.push(i - 1);
    if (x < w - 1) out.push(i + 1);
    if (i >= w) out.push(i - w);
    if (i < n - w) out.push(i + w);
    return out;
  };
  let front = [];
  for (let i = 0; i < n; i++) if (!done[i] && around(i).some((j) => done[j])) { front.push(i); queued[i] = 1; }
  if (!front.length) return img;
  for (let pass = 0; pass < BLEED && front.length; pass++) {
    for (const i of front) {
      let r = 0, g = 0, b = 0, k = 0;
      for (const j of around(i)) if (done[j]) { r += p[4 * j]; g += p[4 * j + 1]; b += p[4 * j + 2]; k++; }
      p[4 * i] = r / k; p[4 * i + 1] = g / k; p[4 * i + 2] = b / k;
    }
    for (const i of front) done[i] = 1;
    const next = [];
    for (const i of front) for (const j of around(i)) if (!done[j] && !queued[j]) { queued[j] = 1; next.push(j); }
    front = next;
  }
  ctx.putImageData(data, 0, 0);
  return c;
}

// A type's number in the map's types (the models' numbers) by its name, as the palette gives it; null without one
function typeNumber(type) {
  const d = mv.scenery.data;
  if (!d) return null;
  if (!d.numbers) {
    d.numbers = new Map();
    const short = new Map((d.types || []).map((t, i) => [t[0], i]));  // a palette made before it said its number
    for (const r of d.palette || []) {
      const t = r[7] ?? short.get(r[1]);
      if (t !== undefined) d.numbers.set(r[0], t);
    }
  }
  return d.numbers.get(type) ?? null;
}

// A type's group (building, prop, vegetation) by its name, as the palette gives it
function groupOfType(type) {
  const r = ((mv.scenery.data && mv.scenery.data.palette) || []).find((x) => x[0] === type);
  return r ? r[2] : "building";
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
  // the map's own objects this mod moved or took away (Select's [[own]] rows) aren't drawn where they were
  const hidden = ownHidden(), types = mv.scenery.data ? mv.scenery.data.types : [];
  for (const mesh of shapes.concat(models)) {
    const { group, flat, rows, real } = mesh.userData, [, width, height] = SCENERY_LOOK[group];
    const n = rows ? rows.length : flat.length / 5;
    for (let j = 0; j < n; j++) {
      const k = rows ? rows[j] : j;
      const x = flat[5 * k + 1], y = flat[5 * k + 2], size = Math.max(0.3, Math.min(flat[5 * k + 4], 4));
      const gone = hidden.size > 0 && types[flat[5 * k]] && hidden.has(`${types[flat[5 * k]][0]}|${x}|${y}`);
      p.set(x * SCALE, groundAt(grid, x, y) * SCALE, y * SCALE);
      q.setFromAxisAngle(up, -flat[5 * k + 3]);  // the game turns from east toward south; the scene's Y turns the other way
      if (gone) s.set(0, 0, 0);
      else if (real) s.set(size * SCALE, size * SCALE, size * SCALE);
      else s.set(width * size * SCALE, height * size * SCALE, width * size * SCALE);
      mesh.setMatrixAt(j, m.compose(p, q, s));
    }
    mesh.instanceMatrix.needsUpdate = true;
    mesh.computeBoundingSphere();
  }
  drawPlaced();
  tintScenery();
}

// The map's own objects the Erase circles take, tinted red; the rest as they are. An object goes when its place is in
// a circle that takes its group (never a bridge) or names its type (rusemod.scenery.erase_plan). Only the objects
// drawn are tinted (every building, a sample of props and trees): the brush's note counts all of them.
const ERASED_TINT = [1.6, 0.35, 0.25];
function erasedTest() {
  const areas = mv.brush.erase, C = 20000, cells = new Map();
  if (!areas.length) return null;
  for (const a of areas) {
    const [x0, x1, y0, y1] = boxOf(a);
    for (let cx = Math.floor(x0 / C); cx <= Math.floor(x1 / C); cx++) {
      for (let cy = Math.floor(y0 / C); cy <= Math.floor(y1 / C); cy++) {
        const key = `${cx},${cy}`;
        (cells.get(key) || cells.set(key, []).get(key)).push(a);
      }
    }
  }
  // t: the object's type in the view ([short name, group, category, model, models, bridge])
  const takes = (a, group, t) => ((a.what || ERASE_DEFAULT).includes(group) && !(t && t[5]))
    || Boolean(t && a.types && a.types.some((n) => n.slice(n.indexOf("/") + 1) === t[0]));
  return (group, t, x, y) => (cells.get(`${Math.floor(x / C)},${Math.floor(y / C)}`) || [])
    .some((a) => footT2(a, x, y) <= 1 && takes(a, group, t));
}

function tintScenery() {
  const gl = mv.gl, d = mv.scenery.data;
  if (!gl || !d) return;
  const test = erasedTest(), c = new gl.THREE.Color();
  for (const mesh of Object.values(mv.scenery.meshes).concat(Object.values(mv.scenery.models || {}).flat())) {
    if (!test && !mesh.instanceColor) continue;  // never tinted: nothing to put back
    const { group, flat, rows } = mesh.userData, n = rows ? rows.length : flat.length / 5, fresh = !mesh.instanceColor;
    for (let j = 0; j < n; j++) {
      const k = rows ? rows[j] : j;
      if (test && test(group, d.types[flat[5 * k]], flat[5 * k + 1], flat[5 * k + 2])) c.setRGB(...ERASED_TINT);
      else c.setRGB(1, 1, 1);
      mesh.setColorAt(j, c);
    }
    if (!mesh.instanceColor) continue;
    mesh.instanceColor.needsUpdate = true;
    if (fresh) mesh.material.needsUpdate = true;  // its shader takes the colours from now on
  }
  gl.draw();
}

let tintFrame = 0;
function tintSoon() {  // once a frame at most, while a drag adds circles
  if (!tintFrame) tintFrame = requestAnimationFrame(() => { tintFrame = 0; tintScenery(); });
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
// kind, type: the Spawn tool's first two dropdowns (the third is the unit, by nation); sel: the spawns selected (their
// item numbers: renderSelection shows them as the game shows a selection); box: a selection box being dragged
const scen = { data: null, pick: 0, show: true, group: null, tool: null, selected: null, units: null, kind: "ground",
  type: null, camp: "-1", count: 1, formation: "line", gap: {}, team: 1, players: null, sel: new Set(), box: null,
  unitByAddress: null, unitsLoading: null, markKind: "LabelVille", trucks: 25 };
// What the Names tab (Map side: towns and hills) and Add a spot or zone (Scenario side: points and zones) add
// (StudioApi.scenario_place; LittleGroove's + Placement): a town's or a hill's name on the map, a named point or a round
// or square zone the mission scripts use
const MARK_KINDS = ["LabelVille", "LabelMontagne", "Name", "CircularZone", "RectangleZone"];
const MARK_WORD = { LabelVille: "scen_mark_town", LabelMontagne: "scen_mark_hill", Name: "scen_mark_point",
  CircularZone: "scen_mark_circle", RectangleZone: "scen_mark_rect" };
const POINT_COLOUR = 0x7fe0f0;  // named points and trigger zones
const SPAWN_KINDS = ["buildings", "ground", "infantry", "air"];

// --- What the scenario shows, kind by kind, and how big its icons are. The owner, 2026-10-03: "why can't you just
// disable the units and the supply depots? But keep the scenario areas or the camera spots", icons "not so bulky on the
// map" when zoomed out, all of it "CUSTOMIZABLE", and nothing more in the top left: switches and a size slider in the
// Scenario tray, kept by the Studio (prefs "view": saveView; the window's own storage is only a fallback, it's lost
// every start). Only the view changes, never the mod. ---
// "points": the named points and trigger zones the mission scripts use (a campaign chapter has hundreds): off until
// asked for, and shown while Names or Add a spot or zone is picked
const SCEN_LAYERS = ["starts", "cams", "depots", "buildings", "units", "zones", "towns", "points"];
const ICON_BASE = 0.042;  // an icon's height as a share of the view's, at size 100 %, close up
const GONE_OPACITY = 0.35;  // a map item the mod takes out: still drawn, faded, so it can be put back
scen.layers = Object.fromEntries(SCEN_LAYERS.map((k) => [k, k !== "points"]));
scen.iconSize = 1;
try {
  const kept = JSON.parse(localStorage.getItem("studio.scenview") || "{}");
  Object.assign(scen.layers, kept.layers || {});
  if (kept.size) scen.iconSize = kept.size;
} catch { /* not kept: the defaults */ }

function saveScenView() {
  try { localStorage.setItem("studio.scenview", JSON.stringify({ layers: scen.layers, size: scen.iconSize })); } catch { /* fine */ }
  saveView();
}

function keptScenView(view) {
  if (view.scen_layers && typeof view.scen_layers === "object") {
    for (const k of SCEN_LAYERS) if (typeof view.scen_layers[k] === "boolean") scen.layers[k] = view.scen_layers[k];
  }
  if (typeof view.icon_size === "number" && view.icon_size > 0) scen.iconSize = view.icon_size;
  if (typeof view.zone_fill === "number" && view.zone_fill >= 0 && view.zone_fill <= 1) zoneFill = view.zone_fill;
  if (typeof view.stick_roads === "boolean") snapRoads = view.stick_roads;  // the Scenario tray's "Stick to roads"
  if (typeof view.road_snap === "boolean") road.snapOn = view.road_snap;     // the Roads tray's "Snap ends"
  if (typeof view.road_trees === "boolean") road.keepTrees = view.road_trees;  // and its "Keep the trees"
  if (typeof view.place_roads === "boolean") mv.place.roads = view.place_roads;  // the place trays' "Face the roads"
  if (view.map_mode === "map" || view.map_mode === "scenario") mv.mode = view.map_mode;  // the side the bar was on
}

// the icons' size now: the slider's, and smaller as the camera pulls back (down to 40 % with the whole map in view)
function iconScale() {
  const gl = mv.gl;
  if (!gl) return ICON_BASE * scen.iconSize;
  const d = gl.camera.position.distanceTo(gl.controls.target), far = Math.min(1, Math.max(0, (d / (mv.size || 1000) - 0.3) / 1.2));
  return ICON_BASE * scen.iconSize * (1 - 0.6 * far);
}

function fitIcon(sprite, k = iconScale()) {
  sprite.scale.set(k * 0.8, k, 1);
}

function fitIcons() {
  if (!scen.group) return;
  const k = iconScale();
  for (const o of scen.group.children) {
    if (o.userData.icon) fitIcon(o, k);
    else if (o.userData.marker) o.scale.setScalar(scen.iconSize);   // a named point's or a zone's diamond (the owner,
  }                                                                  // 2026-10-10: the slider didn't size them)
}

// which switch a spawn goes by
function spawnLayer(it) {
  return it.icon === "depot" || it.group === "depot" ? "depots" : it.unit_kind === "buildings" ? "buildings" : "units";
}
// Several at once: how many one click adds, in which shape, how far apart (metres, per kind to start with). The shape
// faces up the screen (away from the camera), its middle on the click; each unit is turned that way too.
const SPAWN_MOST = 50;  // the "how many" slider's top: as many as one click may add (StudioApi.SPAWN_MOST; it was 10)
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

// Adding units (Add unit)
const spawningNow = () => scen.tool === "spawn";

// A ring where each unit will stand, under the pointer, while adding units.
function showFormation(hit) {
  const gl = mv.gl;
  if (!gl || !gl.ring) return;
  gl.ghosts = gl.ghosts || [];
  const pts = hit && spawningNow() ? formationPoints(hit.x / SCALE, hit.z / SCALE) : [];
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
  scen.sel.clear();
  renderScenarioPick();
  drawScenario();
  renderScenTools();
  loadPlayers(pack, ask);
}

// --- how many players the map takes (StudioApi.map_players / set_players, the mod's maps/<map>/map.toml):
// the map's online entry, a count from 2 to 8, and the starting points a count still needs (Add HQ start) ---
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
  renderDock();  // the scenario tools' tiles: locked while there's no scenario to edit
  // where this setup plays in the game: its menu, its title, and the players it's made for
  $("scen-where").textContent = s && (s.entries || []).length ? fill(w.scen_where, { where: s.entries.map((e) =>
    `${w["scen_kind_" + e.kind] || e.kind} › ${(e.titles || {})[mv.lang] || (e.titles || {}).us || e.name}`
    + ((/^\((\d+)\)/.exec(e.name || "") || [])[1] ? ` (${fill(w.scen_players, { n: /^\((\d+)\)/.exec(e.name)[1] })})` : "")).join(" · ") }) : "";
  $("scen-where").title = w.tip_scen_where;
  $("scen-mission").classList.toggle("hidden", !s);  // its menu entry, files and texts (openMission)
  $("scen-mission").textContent = w.mission_open;
  $("scen-mission").title = w.tip_mission_open;
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

// A spawn's icon, always facing the camera: what it is, on a badge in its side's colour (grey: neutral), its country's
// roundel in the corner. The owner, 2026-10-03: "the stick figure looks atrocious ... it should look like a soldier",
// a depot a truck, an HQ clearly an HQ, tanks like tanks, an armor base and an airfield visibly different, and "the
// bunkers need to have a difference between the bunkers". Filled silhouettes on a 24 x 24 grid: `fill` white, `cut`
// knocked out of it in the badge's colour, `text` a word instead of a picture, `tag` a word knocked out of the picture
// (each kind of bunker). Which icon: StudioApi.icon_of. A building's badge is square, a unit's round; a decoy's dashed.
const NATION_CODES = ["US", "GER", "UK", "FR", "ITA", "USSR", "JAP"];
const ART = {
  soldier: { fill: "M8.4 6.4a3.6 3.6 0 0 1 7.2 0z M7.6 6.2h8.8v1.2H7.6z M10.3 9a1.7 1.7 0 1 0 3.4 0a1.7 1.7 0 1 0-3.4 0z"
    + " M8.8 11h6.4l1 5.6h-1.9l-.6 5.6h-1.8l-.4-4.2-.4 4.2H9.3l-.6-5.6H6.8z M15.8 6.6l1.1-.5 2.6 12.6-1.2.3z" },
  tank: { fill: "M2.5 15h19l-1.8 4.6H4.3z M4.5 12h14.5v3H4.5z M7.5 8.5h7.5l1.6 3.5H6.4z M15.6 9.6h6.6v1.4h-6.6z",
    cut: "M6 17.2a1 1 0 1 0 2 0a1 1 0 1 0-2 0z M9.6 17.2a1 1 0 1 0 2 0a1 1 0 1 0-2 0z M13.2 17.2a1 1 0 1 0 2 0a1 1 0 1 0-2 0z"
      + " M16.8 17.2a1 1 0 1 0 2 0a1 1 0 1 0-2 0z" },
  truck: { fill: "M1.5 6.5h12.6v9.5H1.5z M14.6 9.2h4.3l3.4 3.9V16h-7.7z M1.5 16h20.8v1.5H1.5z"
    + " M2.9 18.4a2.1 2.1 0 1 0 4.2 0a2.1 2.1 0 1 0-4.2 0z M15.6 18.4a2.1 2.1 0 1 0 4.2 0a2.1 2.1 0 1 0-4.2 0z",
    cut: "M15.7 10.4h2.7l2.2 2.5h-4.9z M4.3 18.4a.7.7 0 1 0 1.4 0a.7.7 0 1 0-1.4 0z M17 18.4a.7.7 0 1 0 1.4 0a.7.7 0 1 0-1.4 0z" },
  plane: { fill: "M12 1.8c.9 0 1.3.9 1.3 2.2v4.8l8.2 4.3v2.1l-8.2-2.4v4.6l2.6 2v1.6L12 20.2l-3.9 1v-1.6l2.6-2v-4.6l-8.2 2.4"
    + "v-2.1l8.2-4.3V4c0-1.3.4-2.2 1.3-2.2z" },
  at_gun: { fill: "M5.8 9.4h4.8v7.2H5.8z M10.2 12.1h10.6v1.7H10.2z M20.2 11.2h2.1v3.5h-2.1z"
    + " M4.9 18.3a2.7 2.7 0 1 0 5.4 0a2.7 2.7 0 1 0-5.4 0z M1.8 21.6l5.2-4.4.9 1.1-5.2 4.4z",
    cut: "M6.9 18.3a.7.7 0 1 0 1.4 0a.7.7 0 1 0-1.4 0z" },
  howitzer: { fill: "M8.6 13.8l11-9.6 1.1 1.3-11 9.6z M6.2 11.6h5.4v4.8H6.2z"
    + " M5.8 18.6a2.9 2.9 0 1 0 5.8 0a2.9 2.9 0 1 0-5.8 0z M1.6 22.1l5.5-3.9.8 1.1-5.5 3.9z M11.4 19l7.6 2.4-.4 1.2-7.6-2.4z",
    cut: "M8 18.6a.7.7 0 1 0 1.4 0a.7.7 0 1 0-1.4 0z" },
  aa_gun: { fill: "M9.6 14.4l4.2-11.6 1.3.5-4.2 11.6z M12.2 14.8l4.2-11.6 1.3.5-4.2 11.6z M4.5 14.8h13v2.8h-13z"
    + " M5.6 19.6a1.7 1.7 0 1 0 3.4 0a1.7 1.7 0 1 0-3.4 0z M13 19.6a1.7 1.7 0 1 0 3.4 0a1.7 1.7 0 1 0-3.4 0z" },
  bolt: { fill: "M13.4 1.5L4 13.6h6.6L9 22.5l10.4-12.6h-6.8z" },
  bunker: { fill: "M2.2 19.2v-4.4C2.2 9.4 6.6 5.8 12 5.8s9.8 3.6 9.8 9v4.4z M1.2 19.2h21.6v1.7H1.2z" },
  factory: { fill: "M2 21V11.2l6 3.3v-3.3l6 3.3V6.5h2.6V3h3v18z", cut: "M5 17h2v2H5z M9.5 17h2v2h-2z M14 17h2v2h-2z" },
  house: { fill: "M2.5 11.5L12 3.5l9.5 8v9.8h-19z", cut: "M10 15h4v6.3h-4z" },
  dot: { fill: "M7.5 12a4.5 4.5 0 1 0 9 0a4.5 4.5 0 1 0-9 0z" },
};
const MAP_ICONS = {
  hq: { text: "HQ" }, hq2: { text: "HQ", sub: "2" }, admin: { text: "$" }, depot: ART.truck,
  barracks: ART.soldier, armor_base: ART.tank, at_base: ART.at_gun, art_base: ART.howitzer, airfield: ART.plane,
  proto_base: ART.bolt, atomic: { atom: true }, building: ART.house,
  bunker_at: { ...ART.bunker, tag: "AT" }, bunker_mg: { ...ART.bunker, tag: "MG" }, bunker_aa: { ...ART.bunker, tag: "AA" },
  bunker_art: { ...ART.bunker, tag: "ART" }, bunker_fort: { ...ART.bunker, tag: "FORT" }, bunker_op: { ...ART.bunker, tag: "OP" },
  soldier: ART.soldier, tank: ART.tank, truck: ART.truck, plane: ART.plane, at_gun: ART.at_gun, howitzer: ART.howitzer,
  aa_gun: ART.aa_gun, unit: ART.dot,
};
// a spawn the game data doesn't name (a mod's new unit): by its kind
const KIND_ICON = { buildings: "building", infantry: "soldier", ground: "tank", air: "plane" };

function drawIconArt(g, art, badge) {
  if (art.text) {  // a word, as large as the badge takes
    g.fillStyle = "#ffffff";
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.font = `900 ${art.text.length > 1 ? 38 : 50}px "Segoe UI", Arial, sans-serif`;
    g.fillText(art.text, 48, art.sub ? 44 : 50);
    if (art.sub) { g.font = '900 22px "Segoe UI", Arial, sans-serif'; g.fillText(art.sub, 48, 74); }
    return;
  }
  if (art.atom) {  // the atomic center: the radiation sign
    g.fillStyle = "#ffffff";
    for (let k = 0; k < 3; k++) {
      const a = -Math.PI / 2 + k * 2 * Math.PI / 3;
      g.beginPath(); g.moveTo(48, 48); g.arc(48, 48, 30, a - Math.PI / 6, a + Math.PI / 6); g.closePath(); g.fill();
    }
    g.fillStyle = badge; g.beginPath(); g.arc(48, 48, 11, 0, Math.PI * 2); g.fill();
    g.fillStyle = "#ffffff"; g.beginPath(); g.arc(48, 48, 7, 0, Math.PI * 2); g.fill();
    return;
  }
  g.save();
  g.translate(16, 16);
  g.scale(64 / 24, 64 / 24);
  g.fillStyle = "#ffffff";
  g.fill(new Path2D(art.fill));
  if (art.cut) { g.fillStyle = badge; g.fill(new Path2D(art.cut)); }
  if (art.tag) {  // the bunker's kind, knocked out of it
    g.fillStyle = badge;
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.font = `900 ${art.tag.length <= 2 ? 7.6 : art.tag.length === 3 ? 6.2 : 5.1}px "Segoe UI", Arial, sans-serif`;
    g.fillText(art.tag, 12, 14.6);
  }
  g.restore();
}

// A country's roundel, drawn in the icon's corner (radius r at cx, cy): US star, German cross, the British, French
// and Italian rings, the Soviet star, the Japanese disc. Recognisable shapes, not the game's own art.
function drawRoundel(g, nation, cx, cy, r) {
  const ring = (cols) => cols.forEach((c, k) => { g.fillStyle = c; g.beginPath(); g.arc(cx, cy, r * (1 - k / cols.length), 0, Math.PI * 2); g.fill(); });
  const star = (fill, rr) => {
    g.fillStyle = fill; g.beginPath();
    for (let k = 0; k < 10; k++) {
      const a = -Math.PI / 2 + k * Math.PI / 5, q = k % 2 ? rr * 0.42 : rr;
      g.lineTo(cx + q * Math.cos(a), cy + q * Math.sin(a));
    }
    g.closePath(); g.fill();
  };
  g.save();
  g.lineWidth = 3; g.strokeStyle = "rgba(0,0,0,0.85)";
  g.beginPath(); g.arc(cx, cy, r + 1.5, 0, Math.PI * 2); g.stroke();
  switch (nation) {
    case 0: ring(["#1f3f8f"]); star("#ffffff", r * 0.8); break;                       // US
    case 1: ring(["#ffffff"]); g.fillStyle = "#111";                                   // Germany: the cross
      g.fillRect(cx - r * 0.75, cy - r * 0.2, r * 1.5, r * 0.4); g.fillRect(cx - r * 0.2, cy - r * 0.75, r * 0.4, r * 1.5); break;
    case 2: ring(["#1f3f8f", "#ffffff", "#c8102e"]); break;                            // UK
    case 3: ring(["#c8102e", "#ffffff", "#1f3f8f"]); break;                            // France
    case 4: ring(["#1e7b3c", "#ffffff", "#c8102e"]); break;                            // Italy
    case 5: ring(["#ffffff"]); star("#c8102e", r * 0.85); break;                       // USSR
    case 6: ring(["#ffffff"]); g.fillStyle = "#c8102e"; g.beginPath(); g.arc(cx, cy, r * 0.6, 0, Math.PI * 2); g.fill(); break;  // Japan
    default: ring(["#9aa7b2"]);
  }
  g.restore();
}
const NEUTRAL_COLOUR = 0x9aa7b2;

function sideColour(camp) {
  return camp === undefined || camp === null || camp < 1 ? NEUTRAL_COLOUR : ALLIANCE[(camp - 1) % ALLIANCE.length];
}

function spawnIcon(it, size, selected) {
  const { THREE } = mv.gl, c = spawnIconCanvas(it, selected);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, depthTest: false, transparent: true,
    sizeAttenuation: false }));  // its size on screen is set by fitIcons: the icon-size slider and the zoom
  sprite.center.set(0.5, 0);  // standing on its spot
  sprite.renderOrder = 11;
  sprite.userData.icon = true;
  fitIcon(sprite);
  return sprite;
}

// A spawn's icon as the map draws it (the selection strip shows the same one): its side's colour, round for a unit and
// square for a building, its role's picture and its country's roundel.
function spawnIconCanvas(it, selected) {
  const c = document.createElement("canvas"), g = c.getContext("2d");
  c.width = 96; c.height = 120;
  const hex = "#" + sideColour(it.camp).toString(16).padStart(6, "0");
  const building = it.unit_kind === "buildings";
  g.fillStyle = hex;
  g.strokeStyle = selected ? "#ffd34d" : it.mine ? "#e8c14f" : "rgba(0,0,0,0.85)";
  g.lineWidth = selected || it.mine ? 8 : 4;
  if (it.decoy) g.setLineDash([10, 7]);  // a decoy: dashed
  g.beginPath();
  if (building) g.roundRect(8, 8, 80, 80, 10);  // a building: square
  else g.arc(48, 48, 40, 0, Math.PI * 2);       // a unit: round
  g.fill();
  g.stroke();
  g.setLineDash([]);
  drawIconArt(g, MAP_ICONS[it.icon] || MAP_ICONS[KIND_ICON[it.unit_kind]] || MAP_ICONS.unit, hex);
  // its country: a roundel on the badge's corner (a depot spot and an unknown unit have none); an HQ start has no
  // country (the player picks it) but its player's number there
  if (it.nation !== undefined && it.nation !== null && it.group !== "depot") drawRoundel(g, it.nation, 80, 18, 14);
  if (it.tag) {
    g.fillStyle = "#ffffff";
    g.strokeStyle = "rgba(0,0,0,0.85)";
    g.lineWidth = 3;
    g.beginPath();
    g.arc(80, 18, 15, 0, Math.PI * 2);
    g.fill();
    g.stroke();
    g.fillStyle = "#111111";
    g.font = "700 22px system-ui, sans-serif";
    g.textAlign = "center";
    g.textBaseline = "middle";
    g.fillText(it.tag, 80, 19);
  }
  return c;
}

// A zone's triangles split until no edge is longer than `step`, each new corner a point the caller sets on the
// ground. Drawn from its outline alone, a zone was a flat sheet between its corners: a hill painted inside it poked
// through the sheet, and corners on its slope tilted the sheet like a tent (the owner's D-Day hill, 2026-10-01).
// Returns {xy: the points (x, y pairs: the outline's first, then the new ones), tris: their triangles}.
function drapeZone(points, triangles, step) {
  const xy = Array.from(points), tris = [], mid = new Map();
  const half = (a, b) => {  // an edge's middle, made once, so the two triangles along it share it
    const key = a < b ? `${a},${b}` : `${b},${a}`;
    let m = mid.get(key);
    if (m === undefined) {
      m = xy.length / 2;
      xy.push((xy[2 * a] + xy[2 * b]) / 2, (xy[2 * a + 1] + xy[2 * b + 1]) / 2);
      mid.set(key, m);
    }
    return m;
  };
  const long = (a, b) => Math.hypot(xy[2 * a] - xy[2 * b], xy[2 * a + 1] - xy[2 * b + 1]) > step;
  const split = (a, b, c, depth) => {
    if (depth >= 8 || !(long(a, b) || long(b, c) || long(c, a))) { tris.push(a, b, c); return; }
    const ab = half(a, b), bc = half(b, c), ca = half(c, a);
    split(a, ab, ca, depth + 1); split(ab, b, bc, depth + 1); split(ca, bc, c, depth + 1); split(ab, bc, ca, depth + 1);
  };
  for (let i = 0; i + 2 < triangles.length; i += 3) split(triangles[i], triangles[i + 1], triangles[i + 2], 0);
  return { xy, tris };
}

// A starting point's opening camera (its warm-up path, StudioApi.map_scenarios "cam"; LittleGroove's map editor shows
// it the same way): the flight the match opens with (a dotted line through its keyframes), a camera where it comes to
// rest, a line to what it looks at, and on the ground the part of the map the match opens on (the game's view: 45
// degrees tall, a 16:9 screen, as its screenshots' camera files say).
const CAM_FOV = Math.PI / 4, CAM_ASPECT = 16 / 9;

function drawStartCamera(it, group, colour, at) {
  const { THREE } = mv.gl, path = it.cam.path, rest = path[path.length - 1], size = mv.size || 1000;
  const v3 = (p) => new THREE.Vector3(p[0] * SCALE, p[2] * SCALE, p[1] * SCALE);
  const label = fill(mv.words.scen_cam_what || "Opening camera · team {n}, place {p}", { n: it.alliance || "?", p: it.place || 1 });
  if (path.length > 1) {  // the warm-up flight
    const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(path.map(v3)),
      new THREE.LineDashedMaterial({ color: colour, dashSize: size * 0.01, gapSize: size * 0.008, transparent: true, opacity: 0.6 }));
    line.computeLineDistances();
    group.add(line);
  }
  // the camera at rest: a small cone pointing the way it looks
  let look = it.cam.look || [it.x - rest[0], it.y - rest[1], 0];
  const n = Math.hypot(...look) || 1;
  look = look.map((c) => c / n);
  const cone = new THREE.Mesh(new THREE.ConeGeometry(size * 0.006, size * 0.016, 12),
    new THREE.MeshLambertMaterial({ color: colour, emissive: colour, emissiveIntensity: 0.35 }));
  cone.position.copy(v3(rest));
  cone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), new THREE.Vector3(look[0], look[2], look[1]));  // its tip
  cone.userData.label = label + " · " + (mv.words.scen_cam_rest || "the match opens looking from here");
  group.add(cone);
  // a wider, unseen grip round it: the Move tool drags the camera round its HQ by it (LittleGroove's camera ring)
  const grip = new THREE.Mesh(new THREE.SphereGeometry(size * 0.018, 12, 8),
    new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }));
  grip.position.copy(cone.position);
  grip.userData.camOf = it.item;
  grip.userData.label = cone.userData.label + (mv.words.scen_cam_drag_tip ? " · " + mv.words.scen_cam_drag_tip : "");
  group.add(grip);
  // where it looks, and the part of the map in view: each corner of the screen's ray down to the start's height
  const ground = at(it.x, it.y).y / SCALE;  // the ground's height at the HQ (map units, as the camera's)
  const hitAt = (d) => {
    if (d[2] >= -1e-3) return null;  // at or above the horizon: never reaches the ground
    const t = (rest[2] - ground) / -d[2];
    return [rest[0] + d[0] * t, rest[1] + d[1] * t];
  };
  const centre = hitAt(look);
  if (centre) {
    group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([v3(rest), at(centre[0], centre[1])]),
      new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity: 0.7 })));
  }
  const up = [0, 0, 1], right = [look[1] * up[2] - look[2] * up[1], look[2] * up[0] - look[0] * up[2], look[0] * up[1] - look[1] * up[0]];
  const rn = Math.hypot(...right) || 1;
  const r = right.map((c) => c / rn);
  const u = [r[1] * look[2] - r[2] * look[1], r[2] * look[0] - r[0] * look[2], r[0] * look[1] - r[1] * look[0]];
  const th = Math.tan(CAM_FOV / 2), tw = th * CAM_ASPECT, far = Math.max(1, Math.hypot(rest[0] - it.x, rest[1] - it.y) * 3);
  const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
    const d = [0, 1, 2].map((k) => look[k] + r[k] * sx * tw + u[k] * sy * th);
    const hit = hitAt(d);
    if (hit) return hit;
    const dn = Math.hypot(d[0], d[1]) || 1;  // a top corner over the horizon: cut the view off far away
    return [rest[0] + d[0] / dn * far, rest[1] + d[1] / dn * far];
  });
  const outline = new THREE.Line(new THREE.BufferGeometry().setFromPoints([...corners, corners[0]].map(([x, y]) => at(x, y, size * 0.002))),
    new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity: 0.85 }));
  outline.userData.label = label + " · " + (mv.words.scen_cam_view || "what the screen shows when the match opens");
  group.add(outline);
}

// A zone's border: the edges only one of its triangles has (whatever order its points come in), each with that
// triangle's third corner, which says which way the inside is. Points and triangles are told apart by where they are
// (`p`: the zone's x, y pairs), not by their numbers: a zone the build makes again (rusemod.sectors.zone_mesh, as the
// shipped ones are drawn) repeats its points in each of its parts and its band in its border part, which drew lines
// across a sector where its parts meet (the owner's blank D-Day, 2026-10-09).
function zoneBorder(triangles, p) {
  const seen = new Map(), done = new Set(), at = (i) => `${p[2 * i]},${p[2 * i + 1]}`;
  for (let i = 0; i + 2 < triangles.length; i += 3) {
    const t = [triangles[i], triangles[i + 1], triangles[i + 2]], where = t.map(at);
    const same = where.slice().sort().join(" ");
    if (done.has(same) || where[0] === where[1] || where[1] === where[2] || where[0] === where[2]) continue;
    done.add(same);
    for (let e = 0; e < 3; e++) {
      const a = t[e], b = t[(e + 1) % 3], ka = where[e], kb = where[(e + 1) % 3];
      const key = ka < kb ? `${ka} ${kb}` : `${kb} ${ka}`;
      const got = seen.get(key);
      if (got) got.n += 1;
      else seen.set(key, { a, b, c: t[(e + 2) % 3], n: 1 });
    }
  }
  return [...seen.values()].filter((e) => e.n === 1);
}

// A zone on the ground, Stellaris' way (ZONE_FILL_MOST): a clear line along its border, a glow just inside it that
// fades inwards (clear at the border, gone `band` in), and a faint fill, in its own colour; all following the ground.
// A zone's hover: "Zone 2 · an area of the map (a sector), not a side" (the owner asked whether zones are sides; the
// zone's own name in the file is only a code, zone_<guid>)
// a zone's sector number (the Sectors tool's "Sector 3" is number 2): its colour and its name everywhere, so a sector
// keeps one colour and one number in every view (the owner, 2026-10-10: the colours changed when the Sectors tool
// opened, coloured by list place here and by number there)
const zoneNumber = (z, k) => (Number.isInteger(z.number) && z.number >= 0 ? z.number : k);
const zoneLabel = (z, k) => `${mv.words.scen_zone} ${zoneNumber(z, k) + 1} · ${mv.words.scen_zone_what || z.name}`;

// A zone flat on the map, for pointing at it: its own triangles (a few hundred), not the drape that follows the
// ground (tens of thousands each; raycasting those took 20-46 ms a pointer move on a blank D-Day, 2026-10-09)
function flatZone(z, k) {
  const p = z.points;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (let i = 0; i < p.length; i += 2) {
    x0 = Math.min(x0, p[i]); x1 = Math.max(x1, p[i]); y0 = Math.min(y0, p[i + 1]); y1 = Math.max(y1, p[i + 1]);
  }
  return { p, t: z.triangles, box: [x0, y0, x1, y1], label: zoneLabel(z, k) };
}

// The zone at map point x, y ("" when none): the first whose triangles hold it, as the drape's raycast found it.
function zoneAt(x, y) {
  for (const { p, t, box, label } of scen.zoneFlat || []) {
    if (x < box[0] || x > box[2] || y < box[1] || y > box[3]) continue;
    for (let i = 0; i + 2 < t.length; i += 3) {
      const ax = p[2 * t[i]], ay = p[2 * t[i] + 1], bx = p[2 * t[i + 1]], by = p[2 * t[i + 1] + 1];
      const cx = p[2 * t[i + 2]], cy = p[2 * t[i + 2] + 1];
      const d1 = (x - bx) * (ay - by) - (ax - bx) * (y - by), d2 = (x - cx) * (by - cy) - (bx - cx) * (y - cy);
      const d3 = (x - ax) * (cy - ay) - (cx - ax) * (y - ay);
      if (!((d1 < 0 || d2 < 0 || d3 < 0) && (d1 > 0 || d2 > 0 || d3 > 0))) return label;  // inside or on an edge
    }
  }
  return "";
}

// The ground the zones are draped on, as a key (its heights' sum and range) and whether it's flat: a zone's drape is
// kept while the key is the same, and flat ground (Blank Terrain) needs none.
function groundKey(grid) {
  let sum = 0, lo = Infinity, hi = -Infinity;
  for (let k = 0; k < grid.z.length; k++) {
    const v = grid.z[k];
    sum += v * ((k % 97) + 1);
    if (v < lo) lo = v;
    if (v > hi) hi = v;
  }
  return { key: `${grid.cols}x${grid.rows}:${sum}:${lo}:${hi}`, flat: !(hi - lo > 1e-6 * Math.max(1, Math.abs(hi))) };
}

// A zone's drape (its triangles cut down to `step` so it follows the ground), glow and border on the ground, worked out
// once per zone and ground. The owner, 2026-10-10: "Taking like 20 seconds between each one" on the Scenario side:
// every tool's click draws the scenario again, and one painted sector's drape (long thin triangles cut down to a ground
// cell and a half) took 3 s of it, measured on a copy of his map.
const zoneShapesKept = new WeakMap();
function zoneShapes(z, colour, at, step, ground) {
  const kept = zoneShapesKept.get(z);
  if (kept && kept.ground === ground && kept.step === step) return kept;
  const p = z.points;
  const { xy, tris } = drapeZone(p, z.triangles, step), n = xy.length / 2, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const v = at(xy[2 * i], xy[2 * i + 1]);
    pos[3 * i] = v.x; pos[3 * i + 1] = v.y; pos[3 * i + 2] = v.z;
  }
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (let i = 0; i < p.length; i += 2) {
    x0 = Math.min(x0, p[i]); x1 = Math.max(x1, p[i]); y0 = Math.min(y0, p[i + 1]); y1 = Math.max(y1, p[i + 1]);
  }
  const band = Math.min(0.1 * Math.min(x1 - x0, y1 - y0), 0.015 * (mv.size || 1000) / SCALE);
  const line = [], glow = [], tint = [];
  const corner = (x, y, a) => { const v = at(x, y); glow.push(v.x, v.y, v.z); tint.push(colour.r, colour.g, colour.b, a); };
  for (const { a, b, c } of zoneBorder(z.triangles, p)) {
    const ax = p[2 * a], ay = p[2 * a + 1], dx = p[2 * b] - ax, dy = p[2 * b + 1] - ay, len = Math.hypot(dx, dy);
    if (!len) continue;
    let nx = -dy / len, ny = dx / len;  // across the edge, turned to the inside (where the third corner is)
    if (nx * (p[2 * c] - ax) + ny * (p[2 * c + 1] - ay) < 0) { nx = -nx; ny = -ny; }
    const m = Math.max(1, Math.ceil(len / step));
    for (let i = 0; i < m; i++) {
      const [sx, sy, ex, ey] = [ax + dx * i / m, ay + dy * i / m, ax + dx * (i + 1) / m, ay + dy * (i + 1) / m];
      const s0 = at(sx, sy, (mv.size || 1000) * 0.0005), e0 = at(ex, ey, (mv.size || 1000) * 0.0005);
      line.push(s0.x, s0.y, s0.z, e0.x, e0.y, e0.z);
      corner(sx, sy, 1); corner(ex, ey, 1); corner(ex + nx * band, ey + ny * band, 0);
      corner(sx, sy, 1); corner(ex + nx * band, ey + ny * band, 0); corner(sx + nx * band, sy + ny * band, 0);
    }
  }
  const out = { ground, step, pos, tris, glow: new Float32Array(glow), tint: new Float32Array(tint),
    line: new Float32Array(line), inside: zoneInside(z) };
  zoneShapesKept.set(z, out);
  return out;
}

function drawZone(z, k, zones, at, step, ground) {
  const { THREE } = mv.gl, number = zoneNumber(z, k), colour = zoneColour(number);
  const label = zoneLabel(z, k);
  const { pos, tris, glow, tint, line, inside } = zoneShapes(z, colour, at, step, ground);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  g.setIndex(tris);
  const fill = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ color: colour, transparent: true, opacity: 0,
    side: THREE.DoubleSide, depthWrite: false }));
  fill.userData = { label, zonePart: "fill" };  // pointing anywhere inside says which zone, filled or not
  fill.renderOrder = 7;
  zones.add(fill);
  if (!line.length) return;
  const gg = new THREE.BufferGeometry();
  gg.setAttribute("position", new THREE.BufferAttribute(glow, 3));
  gg.setAttribute("color", new THREE.BufferAttribute(tint, 4));
  const shine = new THREE.Mesh(gg, new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, opacity: 0,
    side: THREE.DoubleSide, depthWrite: false }));
  shine.userData.zonePart = "glow";
  shine.renderOrder = 8;
  zones.add(shine);
  const lg = new THREE.BufferGeometry();
  lg.setAttribute("position", new THREE.BufferAttribute(line, 3));
  const border = new THREE.LineSegments(lg, new THREE.LineBasicMaterial({ color: colour.clone().offsetHSL(0, 0, 0.2),
    transparent: true, opacity: 0.95, depthWrite: false }));
  border.renderOrder = 9;
  zones.add(border);
  zones.add(sectorTag(number, colour, inside, at));
}

// A point inside zone `z` for its number: the middle of its biggest triangle (a triangle's middle is always in it).
function zoneInside(z) {
  const p = z.points, t = z.triangles;
  let best = -1, x = p[0], y = p[1];
  for (let i = 0; i + 2 < t.length; i += 3) {
    const ax = p[2 * t[i]], ay = p[2 * t[i] + 1], bx = p[2 * t[i + 1]], by = p[2 * t[i + 1] + 1];
    const cx = p[2 * t[i + 2]], cy = p[2 * t[i + 2] + 1];
    const area = Math.abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay));
    if (area > best) { best = area; x = (ax + bx + cx) / 3; y = (ay + by + cy) / 3; }
  }
  return [x, y];
}

// A sector's number on the map, in its colour, always facing the camera: the same in the map view and the Sectors
// tool, so "Sector 3" on a button is the 3 on the ground (the owner, 2026-10-10: "numbered and color-coded").
function sectorTag(number, colour, [x, y], at) {
  const light = colour.clone().offsetHSL(0, 0, 0.22);   // lighter than its fill, on a dark outline: readable on it
  const tag = mapLabel(String(number + 1), `#${light.getHexString()}`, (mv.size || 1000) * 0.06);
  tag.position.copy(at(x, y, (mv.size || 1000) * 0.01));
  tag.userData.label = `${mv.words.scen_zone} ${number + 1}`;
  tag.userData.sectorTag = true;  // hidden when the camera is close (fitSectorTags)
  return tag;
}

// A sector's number is as big as the map makes it (sectorTag): close in it filled the view and hid everything under it
// (the owner, 2026-10-15: "when you're super close in, the giant numbers for the sectors don't go away and they block
// like all of your view ... when you're close, it just doesn't show them"). Each number hides once it would be taller
// than this share of the view, and shows again further out. Before every frame (the view's draw).
const SECTOR_TAG_MOST = 0.18;
function fitSectorTags() {
  const cam = mv.gl.camera, view = 2 * Math.tan(cam.fov * Math.PI / 360);
  for (const tags of [scen.zones, sec.tags]) {
    for (const o of (tags && tags.children) || []) {
      if (o.userData.sectorTag) o.visible = o.scale.y <= SECTOR_TAG_MOST * view * cam.position.distanceTo(o.position);
    }
  }
}

// Everything the picked scenario puts on the map, on the ground as it is now (strokes too).
function drawScenario() {
  clearScenario();
  const gl = mv.gl, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!gl || !mv.edit || !s) { if (gl) gl.draw(); renderSelection(); return; }
  const { THREE } = gl, grid = makeGrid(mv.edit), group = new THREE.Group(), size = mv.size || 1000;
  const lift = size * 0.0015, at = (x, y, up = 0) => new THREE.Vector3(x * SCALE, groundAt(grid, x, y) * SCALE + lift + up, y * SCALE);
  // about a ground cell and a half: the zone follows hills and pits (flat ground: no drape at all, nothing to follow)
  const ground = groundKey(grid), step = ground.flat ? Infinity : 1.5 * Math.max(grid.sx, grid.sy);
  const zones = new THREE.Group();  // the zones together (their switch in the Scenario tray)
  group.add(zones);
  scen.zones = zones;
  s.zones.forEach((z, k) => drawZone(z, k, zones, at, step, ground.key));
  fillZones();
  zones.visible = scen.layers.zones && scen.tool !== "sectors";  // the Sectors brush shows its own cells instead
  scen.zoneFlat = s.zones.map((z, k) => flatZone(z, k));  // for pointing at them (scenarioAt)
  const names = new THREE.Group();  // the towns' and hills' names: the Map side's (MAP_SIDE "names")
  group.add(names);
  scen.names = names;
  const pillar = size * 0.03, blank = blankMap();
  // the hover line's last words: "drag to move" on the Scenario side; on the Map side, where to go to change it
  const dragTip = mv.mode === "scenario" ? mv.words.scen_drag_tip : mv.words.locked_scenario;
  for (const it of s.items) {
    if (blank && it.gone) continue;  // a blank map: what it took out of the map it copies isn't there to put back
    // a blank map's HQs: only those the modder has placed, with their cameras (StudioApi._with_hqs; the owner,
    // 2026-10-09: "the HQ shouldn't be there, the camera starting angle shouldn't be there")
    // (only a Battles map's seats are marked placed or not: an Operation's and a chapter's starting points have no
    // online seating, so they always show; hiding every unmarked one hid them all, the new ones too: the owner,
    // 2026-10-10, "I'm pressing HQ start but nothing's popping up on the map")
    if (blank && it.kind === "StartingPoint" && (it.unused || it.placed === false)) continue;
    if (it.kind === "StartingPoint") {  // an HQ badge in the team's colour, its player's number on it
      const colour = ALLIANCE[((it.alliance || 1) - 1) % ALLIANCE.length];
      if (it.cam && scen.layers.cams) {
        const own = new THREE.Group();
        own.userData = { camItem: it.item, colour, at };
        drawStartCamera(it, own, colour, at);
        group.add(own);
      }
      if (!scen.layers.starts) continue;
      // the HQ the game builds here for the seat's player (the owner, 2026-10-10: he liked the HQ icon a placed HQ
      // building had, and "It should just be all in one"): drawn as that icon, not a bare pillar
      const m = spawnIcon({ unit_kind: "buildings", icon: "hq", camp: it.alliance || 1, mine: it.mine,
        tag: String(it.place || 1) }, ICON_BASE, scen.selected === it.item);
      m.position.copy(at(it.x, it.y, 0));
      m.userData.label = (mv.words.scen_start_what ? mv.words.scen_start_what + " · " : "")
        + fill(mv.words.scen_start_place, { n: it.alliance || "?", p: it.place || 1 })
        + (it.name ? ` · ${it.name}` : "") + (it.moved ? ` · ${mv.words.scen_moved}` : "")
        + (it.mine ? ` · ${mv.words.scen_mine}` : "") + (dragTip ? ` · ${dragTip}` : "");
      m.userData.item = it.item;
      group.add(m);
    } else if (it.kind === "Spawn") {  // an icon where a unit or building appears: what it is, its side, its country
      if (!scen.layers[spawnLayer(it)]) continue;
      const m = spawnIcon(it, ICON_BASE, scen.selected === it.item || scen.sel.has(it.item));
      m.position.copy(at(it.x, it.y, 0));
      m.userData.label = spawnLabel(it) + (dragTip && !it.gone ? ` · ${dragTip}` : "");
      if (it.gone) m.material.opacity = GONE_OPACITY;  // taken out by the mod: faded, to put back
      m.userData.item = it.item;
      group.add(m);
    } else if (["Name", "CircularZone", "RectangleZone"].includes(it.kind)) {
      // a named point or a trigger zone the mission scripts use: shown with the Points layer, while adding one, or
      // when the mod adds it; a zone's outline and a diamond at its middle to pick it and drag it by
      if (!(scen.layers.points || scen.tool === "mark" || it.mine || scen.selected === it.item)) continue;
      const picked = scen.selected === it.item, colour = picked ? 0xffffff : POINT_COLOUR;
      const label = `${mv.words[MARK_WORD[it.kind]] || it.kind}${it.name ? " · " + it.name : ""}`
        + (it.mine ? ` · ${mv.words.scen_mine}` : "") + (it.gone ? ` · ${mv.words.scen_taken_out}` : "")
        + (dragTip && !it.gone ? ` · ${dragTip}` : "");
      let pts = null;
      if (it.kind === "CircularZone" && it.radius) {
        pts = [];
        for (let a = 0; a <= 64; a++) {
          const r = a / 64 * Math.PI * 2;
          pts.push(at(it.x + Math.cos(r) * it.radius, it.y + Math.sin(r) * it.radius));
        }
      } else if (it.kind === "RectangleZone" && it.width && it.height) {
        const c = Math.cos(it.turn), sn = Math.sin(it.turn), hw = it.width / 2, hh = it.height / 2;
        pts = [[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh], [-hw, -hh]].map(([dx, dy]) =>
          at(it.x + dx * c - dy * sn, it.y + dx * sn + dy * c));
      }
      if (pts) {
        const line = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts),
          new THREE.LineBasicMaterial({ color: colour, transparent: true, opacity: it.gone ? GONE_OPACITY : 1 }));
        line.userData = { label, item: it.item };
        group.add(line);
      }
      const diamond = new THREE.Mesh(new THREE.OctahedronGeometry(pillar * (it.kind === "Name" ? 0.3 : 0.22)),
        new THREE.MeshLambertMaterial({ color: colour, transparent: true, opacity: it.gone ? GONE_OPACITY : 1 }));
      diamond.position.copy(at(it.x, it.y, pillar * 0.35));
      diamond.userData = { label, item: it.item, marker: true };   // sized by the icon slider too (fitIcons)
      diamond.scale.setScalar(scen.iconSize);
      group.add(diamond);
    } else if ((it.kind === "LabelVille" || it.kind === "LabelMontagne") && (it.text || it.name) && scen.layers.towns) {
      // a new label shows its own words (the map project's new text), in the language the Studio is in
      const own = it.words && (it.words[mv.lang === "base" ? "us" : mv.lang] || it.words.us);
      const text = own || it.text || it.name;
      const sprite = mapLabel(text, scen.selected === it.item ? "#ffd34d"
        : it.kind === "LabelVille" ? "#ffffff" : "#e8d9a8", size * 0.012);
      sprite.position.copy(at(it.x, it.y, pillar * 0.4));
      sprite.userData.label = text + (it.mine ? ` · ${mv.words.scen_mine}` : "")
        + (it.gone ? ` · ${mv.words.scen_taken_out}` : "")
        + (mv.mode !== "map" && mv.words.locked_map ? ` · ${mv.words.locked_map}` : "");  // changed on the Map side
      sprite.userData.item = it.item;  // picked to take it out (or put it back), dragged to move it
      if (it.gone) sprite.material.opacity = GONE_OPACITY;
      names.add(sprite);
    }
  }
  group.visible = scen.show;
  scen.group = group;
  gl.scene.add(group);
  renderLegend();
  gl.draw();
  renderSelection();
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
  if (scen.tool) { if (mv.brush.on) setBrushMode(false); if (mv.place.on) setPlaceMode(false); stopRoad(); stopBridge(); }
  if (scen.tool) toMode(MAP_SIDE_TOOLS.has(scen.tool) ? "map" : "scenario");  // the bar shows the side the tool is on
  if (scen.tool === "names" && !NAME_KINDS.has(scen.markKind)) scen.markKind = "LabelVille";
  if (scen.tool === "mark" && NAME_KINDS.has(scen.markKind)) scen.markKind = "Name";
  dock.check = false;
  pointerMode();
  renderScenTools();
  drawScenario();
  renderDock();
  if (MISSION_TOOLS.has(scen.tool)) openMissionTray();
  drawMissionCameras();
}

// --- a new Operation's or chapter's own mission (mission.js): its trays, and its camera moves on the map ---
function openMissionTray() {
  const mvw = window.MissionView;
  if (!mvw) return;
  mvw.onPlay = playCamera;
  mvw.onAddCamera = addCamera;
  if (!scen.units && !scen.unitsLoading) loadSpawnUnits().then(() => { if (MISSION_TOOLS.has(scen.tool)) mvw.render(); }).catch(() => {});
  mvw.open({ api: mv.api, words: mv.words, lang: mv.lang, pack: mv.current, units: scen.units || [],
    nationNames: mv.nationNames || [], box: $("ms-box"), onChange: drawMissionCameras }, scen.tool)
    .then(() => drawMissionCameras());  // (the camera moves are drawn once the mission is read)
}

// The camera moves on the map while Camera moves is open: each path as a line through its points (the one picked
// bright), its points as dots, a line from its first point to the spot it looks at
function drawMissionCameras() {
  const gl = mv.gl;
  if (!gl) return;
  if (gl.missionCams) {
    gl.scene.remove(gl.missionCams);
    gl.missionCams.traverse((o) => { if (o.geometry) o.geometry.dispose(); if (o.material) o.material.dispose(); });
    gl.missionCams = null;
  }
  const mvw = window.MissionView, draft = mvw && mvw.draft();
  if (scen.tool !== "cameras" || !draft) { gl.draw(); return; }
  const { THREE } = gl, group = new THREE.Group(), picked = mvw.camera();
  const v = ([x, y, z]) => new THREE.Vector3(x * SCALE, z * SCALE, y * SCALE);
  for (const c of draft.camera || []) {
    const pts = (c.points || []).map(v), bright = c === picked;
    if (pts.length >= 2) {
      const curve = new THREE.CatmullRomCurve3(pts);
      group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(curve.getPoints(pts.length * 12)),
        new THREE.LineBasicMaterial({ color: bright ? 0xffd34d : 0x9fb8c8, transparent: true, opacity: bright ? 1 : 0.6 })));
    }
    for (const p of pts) {
      const dot = new THREE.Mesh(new THREE.SphereGeometry((mv.size || 1000) * 0.004, 10, 8),
        new THREE.MeshBasicMaterial({ color: bright ? 0xffd34d : 0x9fb8c8 }));
      dot.position.copy(p);
      group.add(dot);
    }
    if (c.look && pts.length) {
      group.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([pts[0], v(c.look)]),
        new THREE.LineDashedMaterial({ color: 0xff8a3d, dashSize: (mv.size || 1000) * 0.01, gapSize: (mv.size || 1000) * 0.006 }))
        .computeLineDistances());
    }
  }
  group.renderOrder = 9;
  gl.scene.add(group);
  gl.missionCams = group;
  gl.draw();
}

// A new camera move: three points round where the view looks, at the height set, looking at it
function addCamera() {
  const gl = mv.gl, mvw = window.MissionView;
  if (!gl || !mvw) return;
  const t = gl.controls.target, x = t.x / SCALE, y = t.z / SCALE, ground = t.y / SCALE, r = (mv.size || 1000) / SCALE * 0.08;
  const h = ground + mvw.heightUnits();
  mvw.addCamera({ points: [[x - r, y + r, h], [x, y + r * 1.3, h], [x + r, y + r, h]].map((p) => p.map(Math.round)),
    look: [Math.round(x), Math.round(y), Math.round(ground)] });
}

// Play a camera move on the map view as the game would fly it: along its points, eased in and out, looking at its
// spot; the view comes back where it was
function playCamera(c) {
  const gl = mv.gl;
  if (!gl || !c || (c.points || []).length < 2) return;
  const { THREE } = gl, v = ([x, y, z]) => new THREE.Vector3(x * SCALE, z * SCALE, y * SCALE);
  const curve = new THREE.CatmullRomCurve3(c.points.map(v)), look = v(c.look || c.points[0]);
  const keep = { pos: gl.camera.position.clone(), target: gl.controls.target.clone() };
  const ms = Math.max(1, c.seconds || 15) * 1000, t0 = performance.now();
  gl.controls.enabled = false;
  const step = (now) => {
    const t = Math.min(1, (now - t0) / ms), e = t < 0.5 ? 2 * t * t : 1 - 2 * (1 - t) * (1 - t);
    gl.camera.position.copy(curve.getPoint(e));
    gl.camera.lookAt(look);
    gl.renderer.render(gl.scene, gl.camera);
    if (t < 1) requestAnimationFrame(step);
    else {
      gl.camera.position.copy(keep.pos);
      gl.controls.target.copy(keep.target);
      gl.controls.enabled = true;
      gl.controls.update();
      gl.draw();
    }
  };
  requestAnimationFrame(step);
}

async function loadSpawnUnits() {
  if (scen.units) return;
  if (scen.unitsLoading) return scen.unitsLoading;  // asked for by the labels and the Spawn tool at once: one call
  scen.unitsLoading = (async () => {
    const res = await mv.api.units(mv.lang || "base", "all", -1, "", "all");
    const units = res.units.filter((u) => !u.new);  // a mod's new unit isn't in the game's files yet
    // a map's supply depot spot (the slab a player builds a depot on): not a unit of the list, offered first in Money
    units.unshift({ address: DEPOT_SLAB, kind: "buildings", group: "money", name: mv.words.scen_depot_slab || "Supply depot spot",
      base_name: DEPOT_SLAB, nation_name: mv.words.scen_depot_any || "Any side" });
    scen.units = units;
    scen.unitByAddress = new Map(units.map((u) => [u.address, u]));
    renderScenTools();
  })();
  try { await scen.unitsLoading; } finally { scen.unitsLoading = null; }
}

// What a player calls a spawned unit or building: its name in the game, in the Studio's language (the Add unit list's
// names), never its code name (the owner, 2026-10-05: "make this stuff way more intuitive so it can make sense to a
// toddler"). Until the list is loaded, or for a mod's new unit, its kind.
function spawnTitle(it) {
  if (it.what === DEPOT_SLAB) return mv.words.scen_depot_slab || "Supply depot spot";
  const u = it.unit && scen.unitByAddress ? scen.unitByAddress.get(it.unit) : null;
  if (u) return spawnName(u);
  if (!scen.units && !scen.unitsLoading && !scen.unitsFailed && it.unit) {
    loadSpawnUnits().then(() => { drawScenario(); renderSelection(); })
      .catch(() => { scen.unitsFailed = true; });  // the kind words stay; not asked again on every redraw
  }
  return mv.words["scen_kind_word_" + (it.unit_kind || "")] || mv.words.scen_spawn;
}

// A spawn said in words, for the map's hover line and the selection strip: what it is, its country, whose side.
function spawnLabel(it) {
  const w = mv.words, title = spawnTitle(it), kindWord = w["scen_kind_word_" + (it.unit_kind || "")] || "";
  const nation = it.nation !== undefined && it.group !== "depot" ? (mv.nationNames || [])[it.nation] || NATION_CODES[it.nation] : "";
  return [title, kindWord !== title ? kindWord : "", nation,
    it.camp === -1 || (it.mine && it.camp === null) ? w.scen_side_neutral
      : it.camp !== undefined && it.camp !== null ? fill(w.scen_side_n, { n: it.camp }) : "",
    it.mine ? w.scen_mine : it.gone ? w.scen_taken_out : it.moved ? w.scen_moved : ""].filter(Boolean).join(" · ");
}

// --- Selecting spawns as the game selects units (the owner, 2026-10-05: "drag, selectable, and then tell you like
// Ruse does what's the breakdown of the unit ... four tanks, five infantry, four aircraft ... just above where the
// build section is ... it should look like the icon on the map"): a click picks one, Shift+click adds or takes one
// off, a box dragged on the ground with Move picks every spawn in it; above the tray, the map's own icons with how
// many of each, and the count by kind. ---
function selectSpawn(it, add) {
  if (it.kind !== "Spawn") { scen.sel.clear(); scen.selected = it.item; }
  else if (add) {
    if (scen.sel.has(it.item)) scen.sel.delete(it.item); else scen.sel.add(it.item);
    scen.selected = scen.sel.size === 1 ? [...scen.sel][0] : null;
  } else { scen.sel = new Set([it.item]); scen.selected = it.item; }
  drawScenario();
  renderScenTools();
}

function clearSelection() {
  if (!scen.sel.size && scen.selected === null) return;
  scen.sel.clear();
  scen.selected = null;
  drawScenario();
  renderScenTools();
}

// The spawns inside a box dragged on the screen (x0, y0, x1, y1 in the page's pixels): the icons drawn now, by
// where they stand on the screen.
function spawnsInBox(x0, y0, x1, y1) {
  const gl = mv.gl, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!s || !scen.group) return [];
  const rect = gl.renderer.domElement.getBoundingClientRect(), v = new gl.THREE.Vector3();
  const [l, r, t, b] = [Math.min(x0, x1), Math.max(x0, x1), Math.min(y0, y1), Math.max(y0, y1)];
  // a spawn the mod took out (drawn faded, "gone") isn't on the map: a box leaves it, a click still picks it to put back
  const spawns = new Set(s.items.filter((it) => it.kind === "Spawn" && !it.gone).map((it) => it.item)), out = new Set();
  for (const o of scen.group.children) {
    if (!o.userData.icon || !spawns.has(o.userData.item)) continue;
    v.copy(o.position).project(gl.camera);
    if (v.z > 1) continue;  // behind the camera
    const sx = rect.left + (v.x + 1) / 2 * rect.width, sy = rect.top + (1 - v.y) / 2 * rect.height;
    if (sx >= l && sx <= r && sy >= t && sy <= b) out.add(o.userData.item);
  }
  return [...out];
}

function boxStart(ev) {
  scen.box = { x0: ev.clientX, y0: ev.clientY, x1: ev.clientX, y1: ev.clientY, add: ev.shiftKey || ev.ctrlKey,
    shown: false, ev };
  try { mv.gl.renderer.domElement.parentElement.setPointerCapture(ev.pointerId); } catch { /* the box still works over the map */ }
}

function boxMove(ev) {
  const b = scen.box;
  b.x1 = ev.clientX;
  b.y1 = ev.clientY;
  if (!b.shown && Math.abs(b.x1 - b.x0) + Math.abs(b.y1 - b.y0) < 6) return;  // a click, not a box (yet)
  b.shown = true;
  let el = $("scen-box");
  if (!el) {
    el = document.createElement("div");
    el.id = "scen-box";
    el.className = "scen-box";
    document.body.append(el);
  }
  el.style.left = `${Math.min(b.x0, b.x1)}px`;
  el.style.top = `${Math.min(b.y0, b.y1)}px`;
  el.style.width = `${Math.abs(b.x1 - b.x0)}px`;
  el.style.height = `${Math.abs(b.y1 - b.y0)}px`;
}

function boxEnd() {
  const b = scen.box;
  scen.box = null;
  const el = $("scen-box");
  if (el) el.remove();
  if (!b) return;
  const s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!b.shown) {  // a click on the ground: Move's second click puts the item picked there; else it clears
    if (scen.selected !== null && s && mv.brush.mod) {
      const p = hitGround(b.ev);
      if (p) scenPlaceAt(s, p.x / SCALE, p.z / SCALE);
      return;
    }
    clearSelection();
    scenNote(mv.words.scen_sel_hint);
    return;
  }
  const got = spawnsInBox(b.x0, b.y0, b.x1, b.y1);
  scen.sel = new Set(b.add ? [...scen.sel, ...got] : got);
  scen.selected = scen.sel.size === 1 ? [...scen.sel][0] : null;
  drawScenario();
  renderScenTools();
}

function renderSelection() {
  const box = $("scen-selection");
  if (!box) return;
  const s = ((scen.data || {}).scenarios || [])[scen.pick];
  const items = s && scen.show ? s.items.filter((it) => it.kind === "Spawn" && scen.sel.has(it.item)) : [];
  if (s && items.length !== scen.sel.size) scen.sel = new Set(items.map((it) => it.item));  // gone since (an edit)
  box.classList.toggle("hidden", !items.length);
  box.replaceChildren();
  if (!items.length) return;
  const w = mv.words, groups = new Map(), kinds = {};
  for (const it of items) {
    const key = `${it.unit || it.what}|${it.camp}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(it);
    const k = SPAWN_KINDS.includes(it.unit_kind) ? it.unit_kind : "other";
    kinds[k] = (kinds[k] || 0) + 1;
  }
  const head = document.createElement("div");
  head.className = "sel-head";
  const count = document.createElement("strong");
  count.textContent = fill(w.scen_sel_count, { n: items.length });
  const split = document.createElement("span");
  split.textContent = ["ground", "infantry", "air", "buildings", "other"].filter((k) => kinds[k])
    .map((k) => `${kinds[k]} ${w["scen_sel_" + k]}`).join(" · ");
  const clear = document.createElement("button");
  clear.type = "button";
  clear.className = "chip";
  clear.textContent = w.scen_sel_clear;
  clear.addEventListener("click", clearSelection);
  head.append(count, split, clear);
  const row = document.createElement("div");
  row.className = "sel-row";
  for (const list of groups.values()) {
    const it = list[0], b = document.createElement("button");
    b.type = "button";
    b.className = "sel-unit";
    b.title = `${spawnLabel(it)}\n${w.scen_sel_only}`;
    const img = new Image();
    img.src = spawnIconCanvas(it, false).toDataURL();
    img.alt = "";
    const n = document.createElement("span");
    n.className = "sel-n";
    n.textContent = list.length > 1 ? `×${list.length}` : "";
    const name = document.createElement("span");
    name.className = "sel-name";
    name.textContent = spawnTitle(it);
    b.append(img, n, name);
    b.addEventListener("click", () => {
      scen.sel = new Set(list.map((x) => x.item));
      scen.selected = list.length === 1 ? it.item : null;
      drawScenario();
      renderScenTools();
    });
    row.append(b);
  }
  const hint = document.createElement("div");
  hint.className = "muted small";
  hint.textContent = w.scen_sel_hint;
  box.append(head, row, hint);
}

// --- Stick to roads (LittleGroove's RUSE-Mod-Manager map editor, its _snap_to_road and _ROAD_SNAP_OFFSET, GPL-3.0):
// a supply depot spot and a starting point (its HQ) go beside the nearest road, at the distance the game's own maps
// keep (depot 11,696, HQ 13,580 map units from the road network's line, measured on every shipped scenario), on the
// side the click is on. A toggle, kept in this window: off places them exactly where clicked (a field, say). ---
const DEPOT_SLAB = "DalleBatimentDepot";
let snapRoads = true;
try { snapRoads = localStorage.getItem("studio.snaproads") !== "0"; } catch { /* not kept: fine */ }

async function roadGraph() {
  if (scen.roads && scen.roads.pack === mv.current) return scen.roads;
  const g = await mv.api.map_road_graph(mv.current);
  scen.roads = { ...g, pack: mv.current };
  return scen.roads;
}

// (x, y) moved to the road-side spot nearest it, `kind` "depot" or "hq"; unchanged with the toggle off or no roads
async function snapToRoad(kind, x, y) {
  if (!snapRoads) return [x, y];
  let g;
  try { g = await roadGraph(); } catch { return [x, y]; }
  const d = (g.offset || {})[kind], nodes = g.nodes || [];
  if (!d || !nodes.length) return [x, y];
  let best = null;
  for (const [a, b] of g.edges || []) {
    const [ax, ay] = nodes[a], [bx, by] = nodes[b], ex = bx - ax, ey = by - ay, l2 = ex * ex + ey * ey;
    if (l2 <= 1e-9) continue;
    const t = Math.max(0, Math.min(1, ((x - ax) * ex + (y - ay) * ey) / l2)), px = ax + t * ex, py = ay + t * ey;
    let ux = x - px, uy = y - py;
    const dl = Math.hypot(ux, uy);
    if (dl < 1e-6) { const n = Math.sqrt(l2); ux = -ey / n; uy = ex / n; } else { ux /= dl; uy /= dl; }
    const cx = px + d * ux, cy = py + d * uy, dd = (cx - x) ** 2 + (cy - y) ** 2;
    if (!best || dd < best[0]) best = [dd, cx, cy];
  }
  return best ? [best[1], best[2]] : [x, y];
}

// The Add unit list's name for a unit: the game's own (English with the code names), else its code name.
function spawnName(u) {
  return mv.lang === "base" ? u.game_name || u.name : u.name;
}

// Under the Add unit list: the game's own line for the unit picked ("May field armored units and armored recon.",
// "Decoy building: ... booby-trapped"), as on its card in the game.
function spawnDesc() {
  const box = $("scen-unit-desc"), pick = $("scen-unit").value;
  const u = (scen.units || []).find((x) => x.address === pick);
  box.textContent = (u && u.desc) || "";
  box.classList.toggle("hidden", !spawningNow() || !box.textContent);
  renderSpawnTrucks();
}

// --- A supply depot's money (the owner, 2026-10-10: "no way to increase max amt of money in supply depot"): a depot
// holds about trucks x trucks a convoy x money a truck (LittleGroove's measure in the game, StudioApi.depot_money,
// with the unit mod's Economy values); its trucks go up to the file's own top (scenario.TRUCKS_MOST), and past the
// game's own depots (15 to 72) the Studio says it isn't tried in the game ---
const TRUCKS_MOST = 2147483647;

// The money values and the unit mod's rule for this map's depots (its Economy tab's Depots on the maps), read again
// each time (that tab may have changed them meanwhile).
async function depotMoney() {
  try { mv.depotMoney = await mv.api.depot_money(mv.current); } catch { mv.depotMoney = null; }
  return mv.depotMoney;
}

// Under a depot's trucks: about what it holds, and a word when it has more than the game's depots. `ruled`: the
// depot's trucks aren't set by hand, so the Economy tab's rule for this map (if any) gives it its trucks.
function showDepotMoney(box, trucks, ruled = false) {
  const w = mv.words, m = mv.depotMoney;
  const parts = [];
  const rule = ruled && m && m.rule;
  if (rule && Number.isFinite(trucks)) {
    const what = rule.times !== null && rule.times !== undefined ? fill(w.economy_depots_x, { n: rule.times })
      : fill(w.economy_depots_n, { n: Number(rule.trucks).toLocaleString() });
    trucks = rule.times !== null && rule.times !== undefined ? Math.round(trucks * rule.times) : rule.trucks;
    parts.push(fill(w.scen_depot_rule, { what, n: trucks.toLocaleString() }));
  }
  if (m && m.ready && Number.isFinite(trucks) && trucks >= 0) {
    parts.push(fill(w.scen_depot_money, { money: Math.round(trucks * m.per_convoy * m.per_truck).toLocaleString(),
      trucks: Math.round(trucks).toLocaleString(), convoy: m.per_convoy, truck: m.per_truck }));
  }
  if (m && Number.isFinite(trucks) && trucks > m.shipped[1]) parts.push(fill(w.scen_depot_untried, { most: m.shipped[1] }));
  box.textContent = parts.join(" ");
}

// The Spawn tool with the supply depot spot picked: the new depots' trucks, and what each will hold.
function renderSpawnTrucks() {
  const w = mv.words, row = $("scen-depot-row");
  const on = scen.tool === "spawn" && $("scen-unit").value === DEPOT_SLAB;
  row.classList.toggle("hidden", !on);
  if (!on) { row.replaceChildren(); return; }
  const number = el("input", { type: "number", min: "0", max: String(TRUCKS_MOST), step: "1", className: "scen-detail-number",
    value: String(scen.trucks), title: w.tip_scen_spawn_trucks });
  const holds = el("div", { className: "muted" });
  number.addEventListener("input", () => {
    const n = Number(number.value);
    const good = number.value.trim() !== "" && Number.isInteger(n) && n >= 0 && n <= TRUCKS_MOST;
    number.setAttribute("aria-invalid", String(!good));
    if (good) { scen.trucks = n; scen.trucksSet = true; }  // (untouched: the build's 25, or the Economy tab's rule)
    showDepotMoney(holds, n);
  });
  row.title = w.tip_scen_spawn_trucks;
  row.replaceChildren(el("span", { textContent: w.scen_item_trucks }), number, holds);
  depotMoney().then(() => showDepotMoney(holds, scen.trucks, !scen.trucksSet));
}

// what a placed or moved item sticks to the road as: "depot", "hq" or null
function snapKind(item, unit) {
  if (scen.tool === "start" || (item && item.kind === "StartingPoint")) return "hq";
  if (unit === DEPOT_SLAB || (item && item.what === DEPOT_SLAB)) return "depot";
  return null;
}

function renderScenTools() {
  const w = mv.words, s = ((scen.data || {}).scenarios || [])[scen.pick];
  spawnDesc();  // shown only with Add unit
  // (the tools themselves are tiles in the bar on the Scenario side, and Sectors on the Map side: renderDock)
  // Names or Add a spot or zone: what to add (each chip says what it is for), and a town's or hill's words to show
  // (Names, on the Map side, holds the towns' and hills' names; Add a spot or zone the mission's spots and zones)
  const markPick = $("scen-mark-kind"), wordsRow = $("scen-mark-words-row");
  const marking = scen.tool === "mark" || scen.tool === "names";
  markPick.classList.toggle("hidden", !marking);
  const labelKind = NAME_KINDS.has(scen.markKind);
  wordsRow.classList.toggle("hidden", !marking || !labelKind);
  // a zone's size, set before it's placed (the owner, 2026-10-10: "you also can't change how big or small the zone
  // is"); after, the zone stays picked with its own size box (renderItemDetails)
  const zoneKind = scen.markKind === "CircularZone" || scen.markKind === "RectangleZone";
  $("scen-mark-size-row").classList.toggle("hidden", !marking || !zoneKind);
  $("scen-mark-size-label").textContent = scen.markKind === "CircularZone" ? w.scen_item_radius : w.scen_mark_side;
  $("scen-mark-size-row").title = w.tip_scen_mark_size;
  if (marking) {
    const kinds = MARK_KINDS.filter((k) => NAME_KINDS.has(k) === (scen.tool === "names"));
    markPick.replaceChildren(...kinds.map((k) => chipOf(w[MARK_WORD[k]] || k, w["tip_" + MARK_WORD[k]],
      scen.markKind === k, () => { scen.markKind = k; renderScenTools(); })));
    $("scen-mark-words-label").textContent = w.scen_mark_words;
    $("scen-mark-words").placeholder = w.scen_mark_words_hint;
    wordsRow.title = w.tip_scen_mark_words;
  }
  // the HQs are Add HQ start's, not Add unit's (the owner, 2026-10-10: "Headquarters should not be considered units
  // ... It should just be all in one"): every player, the computer's too, has a seat, and the game builds its HQ at
  // that seat's start; Add unit lists no HQ
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
    if (scen.type === "hq") scen.type = null;
    kindPick.replaceChildren(...SPAWN_KINDS.map((k) => chipOf(w[k] || k, w.tip_scen_kind, scen.kind === k,
      () => { scen.kind = k; scen.type = null; renderScenTools(); })));
    const ofKind = all.filter((u) => u.kind === scen.kind);
    const types = GROUP_ORDER.filter((g) => g !== "hq" && ofKind.some((u) => u.group === g));
    if (!types.includes(scen.type)) scen.type = types[0] || null;
    typePick.replaceChildren(...types.map((g) => chipOf(`${w["group_" + g] || g} (${ofKind.filter((u) => u.group === g).length})`,
      w.tip_group, scen.type === g, () => { scen.type = g; renderScenTools(); })));
    const keep = unit.value, byNation = new Map();
    for (const u of ofKind.filter((x) => x.group === scen.type)) {
      if (!byNation.has(u.nation_name)) byNation.set(u.nation_name, []);
      byNation.get(u.nation_name).push(u);
    }
    // each unit by the name a player knows (the game's, even with the code names: "ARMOR BASE", not
    // VehiculeFactory), its type ("Light Tank", "Heavy Bomber") and its code name; the game's own line for the one
    // picked shows under the list (spawnDesc)
    unit.replaceChildren(...[...byNation].map(([nation, us]) => el("optgroup", { label: nation || "?" },
      ...us.sort((a, b) => spawnName(a).localeCompare(spawnName(b))).map((u) => el("option", { value: u.address,
        textContent: spawnName(u) + (u.type ? ` · ${u.type}` : "")
          + (spawnName(u) !== u.base_name ? ` (${u.base_name.replace(/^Descriptor_[A-Za-z]+_/, "")})` : "") })))));
    if (keep && [...unit.options].some((o) => o.value === keep)) unit.value = keep;
    spawnDesc();
    unit.title = w.tip_scen_unit;
    // a skirmish game spawns only neutral items (camp -1): a unit for a player's side would never appear there
    // Who gets it: a scripted scenario's own camps from its mission script (StudioApi._scenario_owners_of,
    // rusemod.missions): the human player's camp, the computer's, each with its country, Neutral first. A BATTLES map:
    // Neutral only (the game starts it with no team list). The camp's number is what's saved. (The tester,
    // 2026-10-03: "There is no option to place player units": the player's camp is 0, which wasn't offered.)
    const skirmish = !!s && s.kind === "skirmish";
    const neutral = { camp: -1, kind: "neutral" };
    const owners = skirmish ? [neutral] : (s && s.owners) || [neutral];
    if (scen.ownerScenario !== (s && s.file)) {  // a new scenario: its player's camp first
      scen.ownerScenario = s && s.file;
      scen.camp = String((owners.find((o) => o.kind === "player") || neutral).camp);
    }
    if (!owners.some((o) => String(o.camp) === scen.camp)) scen.camp = "-1";
    camp.setAttribute("aria-label", w.scen_camp_label);
    camp.replaceChildren(el("span", { className: "muted small", textContent: w.scen_camp_label }),
      ...owners.map((o) => {
        const id = String(o.camp), nation = o.nation === null || o.nation === undefined ? "" : (mv.nationNames || [])[o.nation] || "";
        const number = fill(w.scen_owner_camp, { camp: o.camp });
        const label = o.kind === "neutral" ? w.scen_side_neutral
          : o.kind === "camp" ? fill(w.scen_owner_unknown, { camp: o.camp })
            : `${o.kind === "player" ? w.scen_owner_player : w.scen_owner_ai}${nation ? " · " + nation : ""} (${number})`;
        const tip = skirmish ? w.tip_scen_camp_skirmish
          : w.tip_scen_camp + (o.team > 0 ? " " + fill(w.scen_owner_team, { team: o.team }) : "");
        return chipOf(label, tip, scen.camp === id, () => { scen.camp = id; renderScenTools(); });
      }));
    // a slider, 1 to SPAWN_MOST (a player asked for 3, 5, 7 and 9 too, 2026-10-03: the buttons offered 1, 2, 4, 6, 8, 10)
    const countLabel = el("span", { className: "muted small", textContent: fill(w.scen_count_n, { n: scen.count }) });
    const countSlider = el("input", { type: "range", min: "1", max: String(SPAWN_MOST), step: "1",
      value: String(scen.count), title: w.tip_scen_count });
    countSlider.addEventListener("input", () => {
      scen.count = Number(countSlider.value);
      countLabel.textContent = fill(w.scen_count_n, { n: scen.count });
      $("scen-formation").classList.toggle("hidden", scen.count === 1);
    });
    $("scen-count").replaceChildren(el("label", { className: "brush-slider small" }, countLabel, countSlider));
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
    typedBeside("scen-gap", TYPED.gap, () => spawnGap(), (n) => { scen.gap[scen.kind] = n; renderScenTools(); }, w.tip_scen_gap);
  }
  $("scen-layers").replaceChildren(el("span", { className: "muted small", textContent: w.scen_layers_show || "Show" }),
    ...SCEN_LAYERS.map((k) => chipOf(w["scen_layer_" + k] || k, w.tip_scen_layers, scen.layers[k], () => {
      scen.layers[k] = !scen.layers[k];
      saveScenView();
      drawScenario();
      renderScenTools();
    })));
  $("scen-size").value = Math.round(scen.iconSize * 100);
  $("scen-size-label").textContent = fill(w.scen_icon_size || "Icon size {pct} %", { pct: Math.round(scen.iconSize * 100) });
  $("scen-size-row").title = w.tip_scen_icon_size || "";
  const snapRow = $("scen-snap-row");
  snapRow.classList.toggle("hidden", !["start", "move", "spawn"].includes(scen.tool));
  $("scen-snap").checked = snapRoads;
  $("scen-snap-label").textContent = w.scen_snap_roads || "Stick to roads";
  snapRow.title = w.tip_scen_snap_roads || "";
  renderScenClear(s);
  renderScenHqs(s);
  renderSectorTools(s);  // the Sectors brush's own controls (shown with its tool only)
  renderItemDetails(null, null);  // the picked item's values: shown again below when there is one
  if (!mv.brush.mod && scen.tool) { scenNote(w.no_mod, "error"); return; }
  if (scen.tool === "move") {
    const it = s && scen.selected !== null ? s.items[scen.selected] : null;
    if (!it) { scenNote(w.scen_pick_item + (w.scen_cam_drag ? " " + w.scen_cam_drag : "")); return; }
    if (it.seat && !it.placed) { scenNote(fill(w.scen_hq_click, { t: it.seat[0], k: it.seat[1] })); return; }
    const parts = [fill(w.scen_pick_place, { what: it.kind === "StartingPoint" && it.seat
      ? fill(w.scen_hq_seat, { t: it.seat[0], k: it.seat[1] }) : it.kind === "StartingPoint"
      ? fill(w.scen_start_place, { n: it.alliance || "?", p: it.place || 1 })
      : it.kind === "Spawn" ? w.scen_spawn : it.text || it.name || "" })];
    const n = $("scen-note");
    scenNote(parts[0]);
    if (it.kind === "StartingPoint" && it.cam && it.camera) {  // its camera turned: say how far, and offer it back
      const back = el("button", { type: "button", className: "link", textContent: w.scen_cam_back || "Camera back" });
      back.addEventListener("click", () => saveCamTurn(s, it, 0));
      n.append(" ", fill(w.scen_cam_turned || "Camera turned {deg}°", { deg: Math.round(degOf(it.camera)) }), " ", back);
    }
    if (it.mine || it.moved) {
      const b = el("button", { type: "button", className: "link", textContent: it.mine ? w.scen_remove : w.scen_put_back,
        title: !it.mine ? w.tip_scen_put_back : it.place !== undefined ? w.tip_scen_remove_place : w.tip_scen_remove_mine });
      b.addEventListener("click", () => it.mine
        ? scenEdit(() => it.start !== undefined ? mv.api.scenario_remove_start(mv.current, it.start)
          : it.place !== undefined ? mv.api.scenario_remove_place(mv.current, it.place)
            : mv.api.scenario_remove_spawn(mv.current, it.spawn)).then(() => loadPlayers(mv.current))
        : scenEdit(() => mv.api.scenario_put_back(mv.current, s.file, it.item)));
      n.append(" ", b);
    }
    itemTakeOut(s, it, n);
    renderItemDetails(s, it);
  } else if (spawningNow()) { scenNote(w.scen_spawn_help); renderItemDetails(null, null); }
  else if (scen.tool === "start") { scenNote(w.scen_start_help); renderItemDetails(null, null); }
  else if (scen.tool === "mark" || scen.tool === "names") {
    scenNote(w[MARK_WORD[scen.markKind] + "_help"]);
    const it = s && scen.selected !== null ? s.items[scen.selected] : null;   // the one just placed: its name, size
    renderItemDetails(s, it && MARK_KINDS.includes(it.kind) ? it : null);
  }
  else if (scen.tool === "sectors") { scenNote(""); renderItemDetails(null, null); }  // its notes: renderSectorTools
  else {
    scenNote(s && w.scen_drag_help ? w.scen_drag_help : "");
    const it = s && scen.selected !== null ? s.items[scen.selected] : null;
    if (it && mv.brush.mod && it.mine && it.place !== undefined) {  // a name, point or zone the mod adds: taken back
      const b = el("button", { type: "button", className: "link", textContent: w.scen_remove, title: w.tip_scen_remove_place });
      b.addEventListener("click", () => scenEdit(() => mv.api.scenario_remove_place(mv.current, it.place)));
      $("scen-note").append(" ", b);
    }
    if (it && mv.brush.mod) itemTakeOut(s, it, $("scen-note"));
    renderItemDetails(s, it);
  }
}

// The picked item of the map's own taken out (the match leaves it out: StudioApi.scenario_remove, LittleGroove's
// way), or put back: its depots and other spawns, and its town and hill names. Starting points can only be moved.
function itemTakeOut(s, it, n) {
  const w = mv.words;
  if (it.mine || it.kind === "StartingPoint") return;
  if (it.gone) {
    const back = el("button", { type: "button", className: "link", textContent: w.scen_put_back, title: w.tip_scen_take_out });
    back.addEventListener("click", () => scenEdit(() => mv.api.scenario_put_back(mv.current, s.file, it.item)));
    n.append(" ", back);
    return;
  }
  if (!["Spawn", "LabelVille", "LabelMontagne", "Name", "CircularZone", "RectangleZone"].includes(it.kind)) return;
  const out = el("button", { type: "button", className: "link", textContent: w.scen_take_out,
    title: ["Name", "CircularZone", "RectangleZone"].includes(it.kind) ? w.tip_scen_take_out_point : w.tip_scen_take_out });
  out.addEventListener("click", () => scenEdit(() => mv.api.scenario_remove(mv.current, s.file, [it.item])));
  n.append(" ", out);
}

// The picked item's own values, changed in the map project (StudioApi.scenario_change, maps/<map>/items.toml;
// LittleGroove's Details panel): a spawn's side and a supply depot's trucks, a zone's size in metres, and a town
// name's words in every language (the label holds a key of the game's texts: app.js wordsPanel). Each control says
// in its tooltip what it is and what changing it does.
const DETAIL_KINDS = ["Spawn", "CircularZone", "RectangleZone", "LabelVille", "LabelMontagne", "Name"];

function renderItemDetails(s, it) {
  const w = mv.words, box = $("scen-details");
  // the map's own items, and the spawns, names, points and zones the mod adds (its own starts have none here)
  const ownSpawn = Boolean(it && it.mine && it.spawn !== undefined);
  const show = Boolean(s && it && !it.gone && DETAIL_KINDS.includes(it.kind) && (!it.mine || it.place !== undefined || ownSpawn));
  box.classList.toggle("hidden", !show);
  box.replaceChildren();
  if (!show) return;
  const can = Boolean(mv.brush.mod);
  const save = (field, value) => scenEdit(() => ownSpawn ? mv.api.scenario_spawn_set(mv.current, it.spawn, field, value)
    : it.mine ? mv.api.scenario_place_set(mv.current, it.place, field, value)
      : mv.api.scenario_change(mv.current, s.file, it.item, field, value), true);
  const gameLine = (field, text, back) => {
    if (!it.game || !(field in it.game)) return null;
    const reset = el("button", { type: "button", className: "link", textContent: w.scen_item_reset,
      title: w.tip_scen_item_reset, disabled: !can });
    reset.addEventListener("click", () => save(field, back));
    return el("div", { className: "muted" }, fill(w.scen_item_game, { value: text }), " ", reset);
  };
  const row = (label, tip, control, ...more) => el("div", { className: "scen-detail-row", title: tip },
    el("span", { textContent: label }), control, ...more.filter(Boolean));
  box.append(el("div", { className: "scen-details-title", textContent: w.scen_item_title, title: w.tip_scen_item_title }));
  if (it.kind === "Spawn") {
    const skirmish = s.kind === "skirmish";
    // (a map's own spawn without a Camp is the game's camp 0; one the mod adds without a side is neutral)
    const now = it.camp === null || it.camp === undefined ? (ownSpawn ? -1 : 0) : it.camp;
    const owners = (s.owners || [{ camp: -1, kind: "neutral" }]).slice();
    if (!owners.some((o) => o.camp === now)) owners.push({ camp: now, kind: "camp" });
    const label = (o) => o.kind === "neutral" ? w.scen_side_neutral
      : o.kind === "camp" ? fill(w.scen_owner_unknown, { camp: o.camp })
        : `${o.kind === "player" ? w.scen_owner_player : w.scen_owner_ai}${o.nation !== null && o.nation !== undefined
          && (mv.nationNames || [])[o.nation] ? " · " + mv.nationNames[o.nation] : ""} (${fill(w.scen_owner_camp, { camp: o.camp })})`;
    const tip = skirmish ? w.tip_scen_item_camp_skirmish : w.tip_scen_item_camp;
    const side = el("select", { className: "small", disabled: !can || (skirmish && now === -1), title: tip },
      ...owners.map((o) => el("option", { value: String(o.camp), textContent: label(o), selected: o.camp === now })));
    side.addEventListener("change", () => save("camp", Number(side.value)));
    const gameCamp = it.game && "camp" in it.game ? (it.game.camp === null || it.game.camp === undefined ? 0 : it.game.camp) : null;
    box.append(row(w.scen_item_camp, tip, side,
      gameLine("camp", gameCamp === null ? "" : label(owners.find((o) => o.camp === gameCamp) || { camp: gameCamp, kind: "camp" }), gameCamp)));
    if (ownSpawn && !missionLocked()) {  // a group of the map's own mission it joins, for its events to order it
      const group = el("input", { type: "text", className: "small", value: it.mission_group || "", maxLength: 40,
        placeholder: w.ms_group_hint, disabled: !can, title: w.tip_scen_item_group });
      group.addEventListener("keydown", (e) => e.stopPropagation());
      group.addEventListener("change", () => save("group", group.value.trim().replace(/[^A-Za-z0-9_]/g, "_")));
      box.append(row(w.ms_group, w.tip_scen_item_group, group));
    }
    if (it.trucks !== undefined || it.what === DEPOT_SLAB) {
      // no top but the file's own (scenario.TRUCKS_MOST): the Studio's old 1000 was its own, not the game's
      const trucks = el("input", { type: "number", min: "0", max: String(TRUCKS_MOST), step: "1", className: "scen-detail-number",
        value: it.trucks === undefined || it.trucks === null ? "" : String(it.trucks), disabled: !can, title: w.tip_scen_item_trucks });
      const holds = el("div", { className: "muted" });
      trucks.addEventListener("change", () => {
        const n = Number(trucks.value);
        if (trucks.value.trim() === "" || !Number.isInteger(n) || n < 0 || n > TRUCKS_MOST) { trucks.value = it.trucks ?? ""; return; }
        save("trucks", n);
      });
      trucks.addEventListener("input", () => showDepotMoney(holds, Number(trucks.value)));
      box.append(row(w.scen_item_trucks, w.tip_scen_item_trucks, trucks,
        gameLine("trucks", it.game && it.game.trucks !== null && it.game.trucks !== undefined ? String(it.game.trucks) : "", it.game ? it.game.trucks : null)),
      holds);
      // set by hand here (the map's own depot changed, or one the mod adds given trucks): the Economy tab's rule
      // for this map leaves it be
      const byHand = ownSpawn ? Boolean(it.trucks_set) : Boolean(it.game && "trucks" in it.game);
      depotMoney().then(() => showDepotMoney(holds, it.trucks === undefined || it.trucks === null ? 0 : it.trucks, !byHand));
    }
  } else if (it.kind === "CircularZone" || it.kind === "RectangleZone") {
    const fields = it.kind === "CircularZone" ? [["radius", w.scen_item_radius]] : [["width", w.scen_item_width], ["height", w.scen_item_height]];
    for (const [field, name] of fields) {
      const units = it[field];
      const metres = el("input", { type: "number", min: "1", step: "1", className: "scen-detail-number", disabled: !can,
        value: units ? String(Math.round(units / METRE * 10) / 10) : "", title: w.tip_scen_item_size });
      metres.addEventListener("change", () => {
        const m = Number(metres.value);
        if (metres.value.trim() === "" || !(m > 0)) { metres.value = units ? String(Math.round(units / METRE * 10) / 10) : ""; return; }
        save(field, Math.round(m * METRE));
      });
      const g = it.game && it.game[field];
      box.append(row(name, w.tip_scen_item_size, metres, el("span", { className: "muted", textContent: " m" }),
        gameLine(field, g ? fill(w.scen_item_metres, { m: Math.round(g / METRE * 10) / 10 }) : "", g)));
    }
    box.append(el("div", { className: "muted", textContent: w.scen_item_zone_note }));
  } else if ((it.kind === "LabelVille" || it.kind === "LabelMontagne") && it.key) {
    // a town's or a hill's name: the label names a key of the game's texts (its first 10 letters); its words change
    // in every language (a new label's are the map project's own text)
    const said = el("span", { className: "muted", textContent: "…" });
    const edit = el("button", { type: "button", className: "link", textContent: w.values_words_edit,
      title: w.tip_scen_item_words, disabled: !can || typeof window.wordsPanel !== "function" });
    let panel = null;
    edit.addEventListener("click", () => {
      if (panel) { panel.remove(); panel = null; return; }
      panel = window.wordsPanel(it.key, () => it.mine ? scenEdit(() => mv.api.map_scenarios(mv.current), true)
        : renderItemDetails(s, it), "map");  // kept in the map project
      box.append(panel);
    });
    mv.api.value_words(it.key, "map").then((res) => {
      const mine = (res.words || []).find((x) => x.lang === (mv.lang === "base" ? "us" : mv.lang));
      const words = mine ? (mine.mine || mine.game) : null;
      said.textContent = words ? `“${words}”` : w.values_words_none;
      if (!res.table) edit.disabled = true;
    }).catch(() => { said.textContent = w.values_words_none; edit.disabled = true; });
    box.append(row(it.kind === "LabelVille" ? w.scen_item_town : w.scen_item_hill, w.tip_scen_item_words, said, " ", edit));
  } else if (it.kind === "LabelVille" || it.kind === "LabelMontagne") {
    box.append(row(it.kind === "LabelVille" ? w.scen_item_town : w.scen_item_hill, w.tip_scen_item_no_key,
      el("span", { className: "muted", textContent: `“${it.text || it.name}”` })));
  }
  // the name the mission scripts find it by (a unit, a named point, a zone): changing it can break a script (a spawn
  // the mod adds has none)
  if (["Spawn", "Name", "CircularZone", "RectangleZone"].includes(it.kind) && !ownSpawn) {
    const name = el("input", { type: "text", maxLength: 200, className: "scen-detail-text", value: it.name || "",
      placeholder: w.scen_item_no_name, disabled: !can, title: w.tip_scen_item_name });
    name.addEventListener("change", () => {
      const v = name.value.trim();
      if (!v && !(it.game && "name" in it.game && !it.game.name)) { name.value = it.name || ""; return; }
      save("name", v);
    });
    box.append(row(w.scen_item_name, w.tip_scen_item_name, name,
      gameLine("name", it.game && it.game.name ? it.game.name : w.scen_item_no_name, it.game ? it.game.name || "" : "")));
  }
  // its turn, in degrees: only an item that has one (a label has none); a new point or zone gets one when set
  if (it.turns || ownSpawn || (it.mine && it.place !== undefined && it.kind !== "LabelVille" && it.kind !== "LabelMontagne")) {
    const deg = (r) => Math.round(r * 180 / Math.PI * 10) / 10;
    const turn = el("input", { type: "number", step: "1", className: "scen-detail-number", value: String(deg(it.turn || 0)),
      disabled: !can, title: w.tip_scen_item_turn });
    const turnTo = (radians) => scenEdit(() => ownSpawn ? mv.api.scenario_spawn_set(mv.current, it.spawn, "rotation", radians)
      : it.mine ? mv.api.scenario_place_set(mv.current, it.place, "rotation", radians)
        : mv.api.scenario_turn(mv.current, s.file, it.item, radians), true);
    turn.addEventListener("change", () => {
      const d = Number(turn.value);
      if (turn.value.trim() === "" || !Number.isFinite(d)) { turn.value = String(deg(it.turn || 0)); return; }
      turnTo(d * Math.PI / 180);
    });
    let back = null;
    if (it.game_turn !== undefined) {
      const reset = el("button", { type: "button", className: "link", textContent: w.scen_item_reset,
        title: w.tip_scen_item_reset, disabled: !can });
      reset.addEventListener("click", () => turnTo(it.game_turn));
      back = el("div", { className: "muted" }, fill(w.scen_item_game, { value: `${deg(it.game_turn)}°` }), " ", reset);
    }
    box.append(row(w.scen_item_turn, w.tip_scen_item_turn, turn, el("span", { className: "muted", textContent: " °" }), back));
  }
  if (!can) box.append(el("div", { className: "muted", textContent: w.no_mod }));
  else box.append(el("div", { className: "muted", textContent: w.scen_item_untested }));
}

// Every depot, or every town and hill name, of the picked scenario taken out at once (the owner's blank D-Day,
// 2026-10-05: "a blank blue map on the lowest terrain, with nothing on it").
function renderScenClear(s) {
  const w = mv.words, box = $("scen-clear");
  box.replaceChildren();
  if (!s || !mv.brush.mod) return;
  const depots = s.items.filter((it) => it.kind === "Spawn" && !it.mine && !it.gone && it.group === "depot");
  const names = s.items.filter((it) => (it.kind === "LabelVille" || it.kind === "LabelMontagne") && !it.gone && !it.mine);
  for (const [items, word] of [[depots, w.scen_take_out_depots], [names, w.scen_take_out_names]]) {
    if (!items.length) continue;
    const b = el("button", { type: "button", className: "link", textContent: `${word} (${items.length})`,
      title: w.tip_scen_take_out });
    b.addEventListener("click", () => scenEdit(() => mv.api.scenario_remove(mv.current, s.file, items.map((it) => it.item))));
    box.append(b, " ");
  }
  // Every supply depot of this scenario at once, the map's and the mod's own (StudioApi.scenario_depots): the same
  // trucks each, or each one's times a number; more trucks, more money in every depot (the owner, 2026-10-10: "no
  // way to increase max amt of money in supply depot")
  const allDepots = s.items.filter((it) => it.kind === "Spawn" && !it.gone && (it.group === "depot" || it.what === DEPOT_SLAB));
  if (allDepots.length) {
    const number = el("input", { type: "number", min: "0", step: "any", value: "2", className: "scen-detail-number",
      title: w.tip_scen_depots });
    const how = el("select", { className: "small", title: w.tip_scen_depots },
      el("option", { value: "times", textContent: w.scen_depots_times }),
      el("option", { value: "trucks", textContent: w.scen_depots_each }));
    how.addEventListener("change", () => { number.value = how.value === "trucks" ? "50" : "2"; });
    const apply = el("button", { type: "button", className: "small", textContent: w.scen_depots_apply, title: w.tip_scen_depots });
    apply.addEventListener("click", () => {
      const n = Number(number.value);
      if (number.value.trim() === "" || !Number.isFinite(n) || n < 0 || (how.value === "trucks" && !Number.isInteger(n))) {
        number.setAttribute("aria-invalid", "true");
        return;
      }
      number.setAttribute("aria-invalid", "false");
      scenEdit(() => how.value === "trucks" ? mv.api.scenario_depots(mv.current, s.file, n, null)
        : mv.api.scenario_depots(mv.current, s.file, null, n), true);
    });
    const back = el("button", { type: "button", className: "link", textContent: w.scen_depots_back, title: w.tip_scen_depots_back });
    back.addEventListener("click", () => scenEdit(() => mv.api.scenario_depots(mv.current, s.file, null, null), true));
    box.append(el("div", { className: "scen-detail-row", title: w.tip_scen_depots },
      el("span", { textContent: fill(w.scen_depots_label, { n: allDepots.length }) }), number, " ", how, " ", apply, " ", back));
  }
  // Sectors over the whole map: every scenario of the map, each place its sectors leave out to the nearest one
  // (StudioApi.scenario_sectors, rusemod.sectors); drawn as the build will make them
  if ((s.zones || []).length) {
    const whole = Boolean((scen.data || {}).sectors_whole);
    box.append(chipOf(w.scen_sectors_whole, w.tip_scen_sectors_whole, whole,
      () => scenEdit(() => mv.api.scenario_sectors(mv.current, !whole))), " ");
    if (whole && s.sectors_note) box.append(el("span", { className: "muted", textContent: s.sectors_note }));
  }
}

// A blank map's HQs (StudioApi._with_hqs: s.hqs), one row per player the map seats: placed or not, and Place (or
// Move, once placed): it's picked with the Move tool, and the next click on the ground puts it there, its camera with
// it. Test in game waits until every one is placed (the build says which aren't).
function renderScenHqs(s) {
  const w = mv.words, box = $("scen-hqs"), hqs = (s && s.hqs) || [];
  box.replaceChildren();
  box.classList.toggle("hidden", !hqs.length);
  if (!hqs.length) return;
  box.title = w.tip_scen_hqs;
  box.append(el("div", { className: "scen-hqs-title", textContent: w.scen_hqs_title, title: w.tip_scen_hqs }));
  for (const h of hqs) {
    const picked = scen.tool === "move" && scen.selected === h.item;
    const row = el("div", { className: "scen-hq-row" + (picked ? " picked" : "") },
      el("span", { textContent: fill(w.scen_hq_seat, { t: h.team, k: h.seat }) + " · " }),
      el("span", { className: h.placed ? "muted" : "error-text",
        textContent: h.placed ? w.scen_hq_placed : w.scen_hq_not_placed }), " ");
    const b = el("button", { type: "button", className: "link", textContent: h.placed ? w.scen_hq_move : w.scen_hq_place,
      title: mv.brush.mod ? w.tip_scen_hq_place : w.no_mod });
    b.disabled = !mv.brush.mod;
    b.addEventListener("click", () => {
      if (scen.tool !== "move") setScenTool("move");
      scen.selected = h.item;
      scen.sel = new Set();
      drawScenario();
      renderScenTools();
    });
    row.append(b);
    box.append(row);
  }
  const left = hqs.filter((h) => !h.placed).length;
  box.append(el("div", { className: left ? "error-text" : "muted",
    textContent: left ? fill(w.scen_hqs_left, { n: left }) : w.scen_hqs_all }));
}

// --- the Sectors brush (the owner, 2026-10-09: "Build a sector tool now"): pick a sector (or New sector, or No
// sector to take ground out of every sector), then drag on the ground to paint it, like the Cover brush paints
// cover. Saved in the map project's scenario.toml, per scenario (StudioApi.sector_paint, rusemod.sectors); the cells
// shown are the build's own (StudioApi.sector_view), so what the note says is what the build will say. Not tried in
// the game yet. ---
// mode: "shapes" (each sector's corners dragged on the map: the owner, 2026-10-09, "draggable square rectangles that
// you can adjust", his pick "Shapes + brush") or "paint" (the brush, for touch-ups); drag: a corner being dragged
// ({key, owners: [[sector, index in its outline]], moved}); newBox: a new sector's box being dragged
const sec = { view: null, file: null, pack: null, pick: "new", shape: "round", size: 4, painting: null, busy: false,
  dirty: false, outlines: false, lines: null, nx: 0, ny: 0, box: null, cells: null, canvas: null, ctx: null, img: null,
  tex: null, mesh: null, linesMesh: null, on: false, error: "", mode: "shapes", dotsMesh: null, hotMesh: null,
  drag: null, newBox: null, hot: null };
const SECTOR_SIZE_MOST = 20;  // the size slider: a dab's radius as a share of the map's width, in %

// a sector's colour on the overlay: the zones' own (zoneColour), by its number (worked out once each)
const sectorColours = [];
function sectorRgb(number) {
  if (!sectorColours[number]) {
    const c = zoneColour(number);
    sectorColours[number] = [Math.round(c.r * 255), Math.round(c.g * 255), Math.round(c.b * 255)];
  }
  return sectorColours[number];
}

function sectorRadius() {
  const [x0, , , x1] = mv.edit.bounds;
  return sec.size / 100 * (x1 - x0);
}

// The tool's controls and notes, and its cells on the ground while it's picked.
function renderSectorTools(s) {
  const w = mv.words, box = $("scen-sectors-box"), on = scen.tool === "sectors" && Boolean(s);
  box.classList.toggle("hidden", !on);
  if (on !== sec.on) {
    sec.on = on;
    if (!on && sec.dirty) {  // the sectors as the build makes them, drawn as zones again
      sec.dirty = false;
      scenEdit(() => mv.api.map_scenarios(mv.current), true);
    }
    if (!on && mv.gl && mv.gl.ring) { mv.gl.ring.visible = false; mv.gl.squareRing.visible = false; }
  }
  if (!on) { sectorOverlayShow(false); return; }
  if (sec.file !== s.file || sec.pack !== mv.current || (sec.mesh && mv.gl && mv.gl.ground
    && sec.mesh.geometry.index !== mv.gl.ground.geometry.index)) {
    sec.file = s.file;   // another scenario, another map (or its ground made again): its own cells
    sec.pack = mv.current;
    sec.view = null;
    sec.lines = null;
    sec.cells = null;
    sectorDropMesh();
    loadSectorView();
  }
  sectorOverlayShow(true);
  const v = sec.view, can = Boolean(mv.brush.mod) && Boolean(v) && !sec.busy, shapes = sec.mode === "shapes";
  if (shapes && v && !v.empty && !v.outlines && !sec.lines && !sec.busy) loadSectorView(true);   // the corners need them
  $("scen-sectors-mode").replaceChildren(...["shapes", "paint"].map((k) => chipOf(w["sectors_mode_" + k],
    w["tip_sectors_mode_" + k], sec.mode === k, () => {
      sec.mode = k;
      if (mv.gl && mv.gl.ring) { mv.gl.ring.visible = false; mv.gl.squareRing.visible = false; }
      sectorDrawLines();
      renderSectorTools(s);
    })));
  $("scen-sectors-shape").classList.toggle("hidden", shapes);   // the brush's own: its dab and size
  $("scen-sectors-size-row").classList.toggle("hidden", shapes);
  $("scen-sectors-outlines-row").classList.toggle("hidden", shapes);   // (Shapes always shows them)
  const picks = $("scen-sectors-pick");
  const listed = v ? v.sectors : [];
  if (sec.pick !== "new" && sec.pick !== -1 && !listed.some((x) => x.number === sec.pick)) sec.pick = "new";
  const swatch = (n) => el("span", { className: "sector-swatch", style: `background: rgb(${sectorRgb(n).join(", ")})` });
  // a sector's own ×: taken out in one click, its ground to the sectors round it (Undo brings it back); the owner,
  // 2026-10-10: "It doesn't let you just like delete the ... sector super easy"
  const takeOut = (n) => {
    const x = el("span", { className: "chip-x", textContent: "×", title: fill(w.tip_sectors_delete_n, { n: n + 1 }) });
    x.onclick = (e) => {
      e.stopPropagation();
      if (!can) return;
      if (sec.pick === n) sec.pick = "new";
      sectorCall(() => mv.api.sector_area(mv.current, s.file, [{ sector: n, points: [] }]));
    };
    return x;
  };
  const chip = (label, tip, value, n) => {
    const c = chipOf(label, tip, sec.pick === value, () => { sec.pick = value; renderSectorTools(s); });
    if (n !== undefined) {
      c.prepend(swatch(n));
      if (mv.brush.mod) c.append(takeOut(n));
      c.classList.toggle("busy", !can);
    }
    return c;
  };
  const newChip = chip(w.sectors_new, v && v.next === null ? w.tip_sectors_new_full : w.tip_sectors_new, "new");
  newChip.disabled = Boolean(v) && v.next === null;
  picks.replaceChildren(...listed.map((x) => chip(fill(w.sectors_n, { n: x.number + 1 }), w.tip_sectors_pick, x.number, x.number)),
    newChip, chip(w.sectors_none, shapes ? w.tip_sectors_none_shapes : w.tip_sectors_none, -1));
  $("scen-sectors-shape").replaceChildren(...["round", "square"].map((k) => chipOf(w["sectors_" + k], w.tip_sectors_shape,
    sec.shape === k, () => { sec.shape = k; renderSectorTools(s); })));
  $("scen-sectors-size").value = String(sec.size);
  $("scen-sectors-size").max = String(SECTOR_SIZE_MOST);
  $("scen-sectors-size-label").textContent = fill(w.sectors_size, { pct: sec.size });
  $("scen-sectors-size-row").title = w.tip_sectors_size;
  const strokes = v ? v.strokes : 0;
  const button = (id, word, tip, locked, why, call) => {
    const b = $(id);
    b.textContent = word;
    b.disabled = !can || locked;
    b.title = !mv.brush.mod ? w.no_mod : locked ? why : tip;
    b.onclick = () => sectorCall(call);
  };
  button("scen-sectors-undo", w.sectors_undo, w.tip_sectors_undo, !strokes, w.tip_sectors_undo_none,
    () => mv.api.sector_undo(mv.current, s.file));
  button("scen-sectors-clear", w.sectors_clear, w.tip_sectors_clear, !strokes, w.tip_sectors_undo_none,
    () => mv.api.sector_clear(mv.current, s.file));
  const picked = typeof sec.pick === "number" && sec.pick >= 0;   // a sector taken out: its ground to its neighbours
  button("scen-sectors-delete", w.sectors_delete, w.tip_sectors_delete, !picked, w.tip_sectors_delete_none,
    () => mv.api.sector_area(mv.current, s.file, [{ sector: sec.pick, points: [] }]));
  const empty = Boolean(v && v.starts_empty);
  button("scen-sectors-start", empty ? w.sectors_start_map : w.sectors_start_none,
    empty ? w.tip_sectors_start_map : w.tip_sectors_start_none, false, "",
    () => mv.api.sector_start(mv.current, s.file, !empty));
  // Make sectors (the owner, 2026-10-17: "more intricate sectors rather than just four big blobs"): the whole map cut
  // into sectors about this many km across; Another layout: the same size cut another way (StudioApi.sector_auto)
  const made = v && v.auto, km = $("scen-sectors-auto");
  if (made && document.activeElement !== km) km.value = String(made.metres / 1000);
  $("scen-sectors-auto-label").textContent = w.sectors_auto;
  $("scen-sectors-auto-row").title = w.tip_sectors_auto;
  const metres = () => Math.round(Number(km.value) * 1000);
  button("scen-sectors-auto-make", w.sectors_auto_make, w.tip_sectors_auto_make, false, "",
    () => mv.api.sector_auto(mv.current, s.file, metres(), 0));
  button("scen-sectors-auto-again", w.sectors_auto_again, w.tip_sectors_auto_again, !made, w.tip_sectors_auto_again_none,
    () => mv.api.sector_auto(mv.current, s.file, metres(), made.seed + 1));
  const outl = $("scen-sectors-outlines");
  outl.checked = sec.outlines;
  outl.disabled = !v;
  $("scen-sectors-outlines-label").textContent = w.sectors_outlines;
  $("scen-sectors-outlines-row").title = w.tip_sectors_outlines;
  // what the build will say: no sector at all, a sector in pieces or with a hole (and that it's untried)
  const note = $("scen-sectors-note"), lines = [];
  let bad = false;
  if (!mv.brush.mod) { lines.push(w.no_mod); bad = true; }
  if (sec.error) { lines.push(sec.error); bad = true; }
  if (!v) lines.push(sec.busy ? w.sectors_busy : "");
  else {
    if (sec.busy) lines.push(w.sectors_busy);   // a save on its way: said, and the buttons wait (no second delete)
    if (v.empty) { lines.push(w.sectors_empty); bad = true; }
    for (const p of v.problems) {
      lines.push(fill(p.pieces > 1 ? w.sectors_pieces : w.sectors_hole, { n: p.number + 1, pieces: p.pieces }));
      bad = true;
    }
    // what the build tidies, as shown (StudioApi.sector_view "tidied": rusemod.sectors.tidy_cells); bits too small
    // to see (under 0.1 % of the sectors' ground: a moved border's straight line against the old cells' steps, a few
    // metres) aren't said, the thin lines always are
    const total = v.sectors.reduce((n, x) => n + x.cells, 0);
    const said = (v.tidied || []).filter((t) => t.kind !== "pieces" || t.cells >= total / 1000);
    for (const t of said) {
      if (t.kind === "pieces") {
        lines.push(fill(t.to < 0 ? w.sectors_tidy_pieces_none : w.sectors_tidy_pieces,
          { bits: t.bits, n: t.number + 1, to: t.to + 1 }));
      } else {
        lines.push(fill(t.number < 0 ? w.sectors_tidy_gap : w.sectors_tidy_line, { n: t.number + 1, around: t.around + 1 }));
      }
    }
    if (made) lines.push(fill(w.sectors_auto_made, { n: v.sectors.length, km: made.metres / 1000, seed: made.seed + 1 }));
    if (!bad) lines.push(shapes ? w.sectors_shapes_help : w.sectors_help);
    if (said.length) lines.push(w.sectors_tidy_untried);
    lines.push(w.sectors_untried);
  }
  note.replaceChildren(...lines.filter(Boolean).map((t) => el("div", { textContent: t })));
  note.className = "small" + (bad ? " error-text" : "");
}

async function loadSectorView(outlines) {
  const pack = mv.current, file = sec.file;
  sec.busy = true;
  try {
    const v = await mv.api.sector_view(pack, file, Boolean(outlines || sec.outlines || sec.mode === "shapes"));
    if (pack !== mv.current || file !== sec.file) return;
    takeSectorView(v);
  } catch (err) {
    sec.error = (err && err.message) || String(err);
  } finally {
    sec.busy = false;
    renderSectorTools(((scen.data || {}).scenarios || [])[scen.pick]);
  }
}

// A save (a stroke, Undo, Clear, the start): the view it returns shown; its outlines asked for again when they're on.
async function sectorCall(call) {
  const pack = mv.current;
  sec.busy = true;
  renderSectorTools(((scen.data || {}).scenarios || [])[scen.pick]);   // "working…" and the buttons wait, at once
  try {
    const v = await call();
    if (pack === mv.current) {
      sec.dirty = true;
      takeSectorView(v);
      if ((sec.outlines || sec.mode === "shapes") && !v.outlines && !v.empty) loadSectorView(true);
    }
  } catch (err) {
    if (sec.view && pack === mv.current) takeSectorView(sec.view);  // a stroke not saved: off the ground again
    sec.error = (err && err.message) || String(err);
  } finally {
    sec.busy = false;
    renderSectorTools(((scen.data || {}).scenarios || [])[scen.pick]);
  }
}

// The view's cells (run by run) into the overlay's picture; its outlines, when it has them, as lines.
function takeSectorView(v) {
  sec.view = v;
  sec.error = "";
  sec.lines = v.outlines || (sec.outlines ? sec.lines : null);
  const n = v.nx * v.ny;
  if (!sec.cells || sec.nx !== v.nx || sec.ny !== v.ny) {
    sec.nx = v.nx;
    sec.ny = v.ny;
    sec.cells = new Uint8Array(n);
    sectorDropMesh();
  }
  sec.box = v.box;
  let i = 0;
  for (let k = 0; k < v.runs.length; k += 2) { sec.cells.fill(v.runs[k], i, i + v.runs[k + 1]); i += v.runs[k + 1]; }
  sectorDrawCells(0, sec.ny - 1, 0, sec.nx - 1);
  sectorDrawLines();
  sectorDrawTags();
}

// Each sector's number on the Sectors tool's cells, where the view puts its label (inside it), in its colour: the
// same tag the map view draws on its zones (sectorTag).
function sectorDrawTags() {
  const gl = mv.gl;
  if (sec.tags) {
    if (gl) gl.scene.remove(sec.tags);
    sec.tags.traverse((o) => { if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
    sec.tags = null;
  }
  if (!gl || !mv.edit || !sec.view) return;
  const { THREE } = gl, grid = makeGrid(mv.edit), size = mv.size || 1000;
  const at = (x, y, up = 0) => new THREE.Vector3(x * SCALE, groundAt(grid, x, y) * SCALE + size * 0.0015 + up, y * SCALE);
  sec.tags = new THREE.Group();
  for (const x of sec.view.sectors) sec.tags.add(sectorTag(x.number, zoneColour(x.number), [x.x, x.y], at));
  sec.tags.visible = sec.on;
  gl.scene.add(sec.tags);
  gl.draw();
}

function sectorDropMesh() {
  for (const k of ["mesh", "linesMesh"]) {
    const o = sec[k];
    if (!o) continue;
    if (mv.gl) mv.gl.scene.remove(o);
    o.geometry.dispose();
    o.material.dispose();
    sec[k] = null;
  }
}

// The cells on the ground: the ground's own points, with their place in the cells' picture (like overlayMesh).
function sectorOverlayShow(show) {
  const gl = mv.gl;
  if (!gl) return;
  if (show && !sec.mesh && sec.cells && gl.ground && mv.edit) {
    const { THREE } = gl, ed = mv.edit, [bx, by, bw, bh] = sec.box;
    if (!sec.canvas || sec.canvas.width !== sec.nx || sec.canvas.height !== sec.ny) {
      sec.canvas = document.createElement("canvas");
      sec.canvas.width = sec.nx;
      sec.canvas.height = sec.ny;
      sec.ctx = sec.canvas.getContext("2d");
      sec.img = sec.ctx.createImageData(sec.nx, sec.ny);
      if (sec.tex) sec.tex.dispose();
      sec.tex = new THREE.CanvasTexture(sec.canvas);
      sec.tex.flipY = false;  // row 0 is the cells' first row (y 0)
      sec.tex.userData.keep = true;
      sectorDrawCells(0, sec.ny - 1, 0, sec.nx - 1);
    }
    const src = gl.ground.geometry, g = new THREE.BufferGeometry(), uv = new Float32Array(ed.n * 2);
    for (let i = 0; i < ed.n; i++) { uv[2 * i] = (ed.wx[i] - bx) / bw; uv[2 * i + 1] = (ed.wy[i] - by) / bh; }
    g.setAttribute("position", src.attributes.position);
    g.setAttribute("uv", new THREE.BufferAttribute(uv, 2));
    g.setIndex(src.index);
    sec.mesh = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: sec.tex, transparent: true, depthWrite: false,
      polygonOffset: true, polygonOffsetFactor: -6, polygonOffsetUnits: -6, side: THREE.DoubleSide }));
    sec.mesh.frustumCulled = false;  // its points move with the ground's
    sec.mesh.renderOrder = 5;
    gl.scene.add(sec.mesh);
  }
  if (sec.mesh) sec.mesh.visible = show;
  if (sec.tags) sec.tags.visible = show;
  const lines = show && (sec.outlines || sec.mode === "shapes");
  if (sec.linesMesh) sec.linesMesh.visible = lines;
  if (sec.dotsMesh) sec.dotsMesh.visible = lines && sec.mode === "shapes";
  if (sec.hotMesh) sec.hotMesh.visible = lines && sec.mode === "shapes";
  gl.draw();
}

function sectorDrawCells(r0, r1, c0, c1) {
  if (!sec.cells || !sec.img) return;
  const n = sec.nx, px = sec.img.data;
  for (let r = r0; r <= r1; r++) {
    for (let c = c0; c <= c1; c++) {
      const i = r * n + c, k = 4 * i, v = sec.cells[i];
      if (v) { const rgb = sectorRgb(v - 1); px[k] = rgb[0]; px[k + 1] = rgb[1]; px[k + 2] = rgb[2]; px[k + 3] = 130; }
      else px[k + 3] = 0;
    }
  }
  sec.ctx.putImageData(sec.img, 0, 0, c0, r0, c1 - c0 + 1, r1 - r0 + 1);
  sec.tex.needsUpdate = true;
  if (mv.gl) mv.gl.draw();
}

// The sectors' outlines as the build traces them (Show outlines, and always in Shapes): lines on the ground in each
// sector's colour; in Shapes their corners as dots too (the one under the pointer or dragged bigger), and a new
// sector's box while it's dragged.
function sectorDrawLines() {
  const gl = mv.gl;
  if (!gl || !mv.edit) return;
  for (const k of ["linesMesh", "dotsMesh", "hotMesh"]) {
    const o = sec[k];
    if (o) { gl.scene.remove(o); o.geometry.dispose(); o.material.dispose(); sec[k] = null; }
  }
  const shapes = sec.mode === "shapes";
  if (!(sec.outlines || shapes) || !(sec.lines || sec.newBox)) { gl.draw(); return; }
  const { THREE } = gl, grid = makeGrid(mv.edit), lift = (mv.size || 1000) * 0.002, pos = [], col = [];
  const at = (x, y) => [x * SCALE, groundAt(grid, x, y) * SCALE + lift, y * SCALE];
  const ring = (p, rgb) => {
    for (let i = 0; i < p.length; i += 2) {
      const j = (i + 2) % p.length;
      pos.push(...at(p[i], p[i + 1]), ...at(p[j], p[j + 1]));
      col.push(...rgb, ...rgb);
    }
  };
  for (const [num, p] of Object.entries(sec.lines || {})) ring(p, sectorRgb(Number(num)).map((c) => Math.min(1, c / 255 + 0.2)));
  const b = sec.newBox;
  if (b) ring([b.x0, b.y0, b.x1, b.y0, b.x1, b.y1, b.x0, b.y1], b.none ? [0.85, 0.85, 0.85] : [1, 0.83, 0.3]);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(pos), 3));
  g.setAttribute("color", new THREE.BufferAttribute(new Float32Array(col), 3));
  sec.linesMesh = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ vertexColors: true, depthTest: false }));
  sec.linesMesh.renderOrder = 11;
  sec.linesMesh.visible = sec.on;
  gl.scene.add(sec.linesMesh);
  if (shapes && sec.lines) {
    const dots = [], hot = [];
    for (const [key, d] of sectorDots()) (key === sec.hot || (sec.drag && key === sec.drag.key) ? hot : dots).push(...at(d.x, d.y));
    const points = (list, size, colour) => {
      const pg = new THREE.BufferGeometry();
      pg.setAttribute("position", new THREE.BufferAttribute(new Float32Array(list), 3));
      const m = new THREE.Points(pg, new THREE.PointsMaterial({ size, sizeAttenuation: false, color: colour, depthTest: false }));
      m.renderOrder = 12;
      m.visible = sec.on;
      gl.scene.add(m);
      return m;
    };
    sec.dotsMesh = points(dots, 7, 0xffffff);
    sec.hotMesh = points(hot, 13, 0xffd34d);
  }
  gl.draw();
}

// --- Shapes: each sector's outline (as the build traces it: two sectors share their border's corners, point for
// point) with its corners as dots. Dragging a dot moves it in every sector that has it, so a shared border stays
// shared; let go and each sector it changed is saved as its new shape (StudioApi.sector_area, rusemod.sectors
// SectorArea: the build fills it on its own grid, the ground a sector gives up going to what touches it, and tidies
// as for the brush). Double-click a border: a new dot; right-click a dot: it's taken out. New sector: drag a box;
// No sector: a box of no sector (its edges are the borders round it, their dots dragged as any). ---
function sectorDots() {   // {key "x,y": {x, y, owners: [[sector, index of x in its outline], ...]}}
  const out = new Map();
  for (const [num, p] of Object.entries(sec.lines || {})) {
    for (let i = 0; i < p.length; i += 2) {
      const key = `${p[i]},${p[i + 1]}`;
      if (!out.has(key)) out.set(key, { x: p[i], y: p[i + 1], owners: [] });
      out.get(key).owners.push([num, i]);
    }
  }
  return out;
}

function sectorScreen(x, y, grid, rect) {   // a map point on the screen: [x, y] in pixels, or null behind the camera
  const gl = mv.gl, v = new gl.THREE.Vector3(x * SCALE, groundAt(grid, x, y) * SCALE, y * SCALE).project(gl.camera);
  if (v.z > 1) return null;
  return [rect.left + (v.x + 1) / 2 * rect.width, rect.top + (1 - v.y) / 2 * rect.height];
}

const SECTOR_REACH = 10;   // pixels: how near the pointer a dot or a border is to be picked
function sectorDotAt(ev) {
  if (!sec.lines || !mv.gl || !mv.edit) return null;
  const grid = makeGrid(mv.edit), rect = mv.gl.renderer.domElement.getBoundingClientRect();
  let best = null, bestD = SECTOR_REACH * SECTOR_REACH;
  for (const [key, d] of sectorDots()) {
    const s = sectorScreen(d.x, d.y, grid, rect);
    if (!s) continue;
    const dd = (s[0] - ev.clientX) ** 2 + (s[1] - ev.clientY) ** 2;
    if (dd < bestD) { bestD = dd; best = { key, ...d }; }
  }
  return best;
}

// The border under the pointer: its two corners' keys and the map point on it nearest the pointer.
function sectorEdgeAt(ev) {
  if (!sec.lines || !mv.gl || !mv.edit) return null;
  const grid = makeGrid(mv.edit), rect = mv.gl.renderer.domElement.getBoundingClientRect();
  let best = null, bestD = SECTOR_REACH * SECTOR_REACH;
  for (const p of Object.values(sec.lines)) {
    for (let i = 0; i < p.length; i += 2) {
      const j = (i + 2) % p.length, a = sectorScreen(p[i], p[i + 1], grid, rect), b = sectorScreen(p[j], p[j + 1], grid, rect);
      if (!a || !b) continue;
      const ex = b[0] - a[0], ey = b[1] - a[1], l2 = ex * ex + ey * ey;
      if (!l2) continue;
      const t = Math.max(0.05, Math.min(0.95, ((ev.clientX - a[0]) * ex + (ev.clientY - a[1]) * ey) / l2));
      const dd = (a[0] + t * ex - ev.clientX) ** 2 + (a[1] + t * ey - ev.clientY) ** 2;
      if (dd < bestD) {
        bestD = dd;
        best = { a: `${p[i]},${p[i + 1]}`, b: `${p[j]},${p[j + 1]}`,
          x: Math.round(p[i] + t * (p[j] - p[i])), y: Math.round(p[i + 1] + t * (p[j + 1] - p[i + 1])) };
      }
    }
  }
  return best;
}

// Save the new shapes of the sectors `nums` (their outlines as they are in sec.lines) in one go, changed only inside
// `within` (the triangles round a corner that moved), so the rest of each stays cell for cell as the build had it.
function sectorSaveShapes(nums, within) {
  const pairs = (p) => { const out = []; for (let i = 0; i < p.length; i += 2) out.push([p[i], p[i + 1]]); return out; };
  const areas = [...new Set(nums)].map((n) => ({ sector: Number(n), points: pairs(sec.lines[n]), within }));
  if (areas.length) sectorCall(() => mv.api.sector_area(mv.current, sec.file, areas));
}

// A corner's neighbours in each sector that has it: [[sector, index, [prev x, y], [next x, y]], ...]
function sectorAround(owners) {
  return owners.map(([num, i]) => {
    const p = sec.lines[num], n = p.length, a = (i - 2 + n) % n, b = (i + 2) % n;
    return [num, i, [p[a], p[a + 1]], [p[b], p[b + 1]]];
  });
}

function sectorShapesOn() {
  return scen.tool === "sectors" && sec.on && sec.mode === "shapes" && Boolean(sec.view) && Boolean(mv.gl) && Boolean(mv.edit);
}

// A press in Shapes, before the view's own (capture): on a dot, its drag; with New sector picked, a box; with No
// sector picked, a box of no sector (the owner, 2026-10-10: "at any place in the map, there could be no sector or it
// could be covered"); else the view turns as usual.
function sectorShapeDown(ev) {
  if (!sectorShapesOn() || ev.button !== 0 || sec.busy) return;
  if (!mv.brush.mod) { scenNote(mv.words.no_mod, "error"); return; }
  const dot = sectorDotAt(ev);
  const p = dot ? null : hitGround(ev);
  const box = p && ((sec.pick === "new" && sec.view.next !== null) || sec.pick === -1);
  if (!dot && !box) return;
  ev.preventDefault();
  ev.stopPropagation();   // the view doesn't turn under the drag
  mv.gl.renderer.domElement.parentElement.setPointerCapture(ev.pointerId);
  if (dot) sec.drag = { key: dot.key, owners: dot.owners, moved: false, from: [dot.x, dot.y], around: sectorAround(dot.owners) };
  else {
    const x = Math.round(p.x / SCALE), y = Math.round(p.z / SCALE);
    sec.newBox = { x0: x, y0: y, x1: x, y1: y, none: sec.pick === -1 };
  }
  sectorDrawLines();
}

function sectorShapeMove(ev) {
  if (!sectorShapesOn()) return;
  if (!sec.drag && !sec.newBox) {   // over a dot: it's drawn bigger, so it's clear what a press takes
    const dot = sectorDotAt(ev), key = dot ? dot.key : null;
    if (key !== sec.hot) { sec.hot = key; sectorDrawLines(); }
    mv.gl.renderer.domElement.style.cursor = key ? "grab" : "";
    return;
  }
  const p = hitGround(ev);
  if (!p) return;
  const x = Math.round(p.x / SCALE), y = Math.round(p.z / SCALE);
  if (sec.drag) {
    for (const [num, i] of sec.drag.owners) { sec.lines[num][i] = x; sec.lines[num][i + 1] = y; }
    sec.drag.key = `${x},${y}`;
    sec.drag.moved = true;
  } else {
    sec.newBox.x1 = x;
    sec.newBox.y1 = y;
  }
  sectorDrawLines();
}

function sectorShapeUp() {
  const d = sec.drag, b = sec.newBox;
  sec.drag = null;
  sec.newBox = null;
  if (d && d.moved) {   // the ground that changed: each sector's two triangles round the corner, before and after
    const [ox, oy] = d.from, [nx, ny] = d.key.split(",").map(Number), within = [];
    for (const [, , prev, next] of d.around) within.push([prev, [ox, oy], next], [prev, [nx, ny], next]);
    sectorSaveShapes(d.owners.map(([num]) => num), within);
  } else if (b) {
    const [x0, x1] = [Math.min(b.x0, b.x1), Math.max(b.x0, b.x1)], [y0, y1] = [Math.min(b.y0, b.y1), Math.max(b.y0, b.y1)];
    const [mx0, , , mx1] = mv.edit.bounds;
    if (x1 - x0 > (mx1 - mx0) / 200 && y1 - y0 > (mx1 - mx0) / 200) {   // (a click, not a box: nothing)
      const n = b.none ? -1 : sec.view.next;
      sec.pick = n;   // the new sector stays picked (No sector too: another box)
      sectorCall(() => mv.api.sector_area(mv.current, sec.file, [{ sector: n, points: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]] }]));
    }
  }
  sectorDrawLines();
}

// Double-click a border: a new dot there, in each sector the border belongs to. Nothing changes until it's dragged
// (the drag saves it with the shape), so it's only drawn till then.
function sectorAddDot(ev) {
  if (!sectorShapesOn() || !mv.brush.mod || sec.busy) return;
  const e = sectorEdgeAt(ev);
  if (!e) return;
  for (const p of Object.values(sec.lines)) {
    for (let i = 0; i < p.length; i += 2) {
      const j = (i + 2) % p.length, a = `${p[i]},${p[i + 1]}`, b = `${p[j]},${p[j + 1]}`;
      if ((a === e.a && b === e.b) || (a === e.b && b === e.a)) {
        p.splice(i + 2, 0, e.x, e.y);
        break;
      }
    }
  }
  sec.hot = `${e.x},${e.y}`;
  sectorDrawLines();
}

// Right-click a dot: it's taken out of each sector that has it (a sector keeps at least three corners).
function sectorRemoveDot(ev) {
  if (!sectorShapesOn()) return false;
  const dot = sectorDotAt(ev);
  if (!dot) return false;
  ev.preventDefault();
  if (!mv.brush.mod || sec.busy || dot.owners.some(([num]) => sec.lines[num].length <= 6)) return true;
  const within = sectorAround(dot.owners).map(([, , prev, next]) => [prev, [dot.x, dot.y], next]);   // the corner cut off
  for (const [num, i] of dot.owners) sec.lines[num].splice(i, 2);
  sectorSaveShapes(dot.owners.map(([num]) => num), within);
  return true;
}

// One dab on the shown cells (the build's rule: a cell whose middle is inside it), before the save.
function sectorDab(x, y, value) {
  if (!sec.cells || !sec.box) return;
  const [bx, by, bw, bh] = sec.box, cw = bw / sec.nx, ch = bh / sec.ny, r = sec.painting.radius;
  const s = { x, y, radius: r, shape: sec.shape };
  const c0 = Math.max(0, Math.floor((x - r - bx) / cw)), c1 = Math.min(sec.nx - 1, Math.ceil((x + r - bx) / cw));
  const r0 = Math.max(0, Math.floor((y - r - by) / ch)), r1 = Math.min(sec.ny - 1, Math.ceil((y + r - by) / ch));
  if (c0 > c1 || r0 > r1) return;
  for (let row = r0; row <= r1; row++) {
    const cy = by + (row + 0.5) * ch;
    for (let c = c0; c <= c1; c++) if (footT2(s, bx + (c + 0.5) * cw, cy) < 1) sec.cells[row * sec.nx + c] = value + 1;
  }
  sectorDrawCells(r0, r1, c0, c1);
}

// A press on the ground with the Sectors brush: the drag starts (its dabs every half radius, as Cover's).
function sectorDown(ev, s) {
  if (sec.mode !== "paint") return;   // (Shapes: sectorShapeDown, before the view's own)
  if (!mv.brush.mod || !sec.view || sec.busy) return;  // (no mod: the note says so already)
  const value = sec.pick === "new" ? sec.view.next : sec.pick;
  if (value === null || value === undefined) { sec.error = mv.words.tip_sectors_new_full; renderSectorTools(s); return; }
  const p = hitGround(ev);
  if (!p) return;
  const x = Math.round(p.x / SCALE), y = Math.round(p.z / SCALE);
  sec.painting = { file: s.file, value, radius: Math.max(1, Math.round(sectorRadius())), points: [[x, y]], last: [x, y] };
  sectorDab(x, y, value);
  mv.gl.renderer.domElement.setPointerCapture(ev.pointerId);
}

function sectorMove(p) {
  const g = sec.painting;
  if (sec.mode !== "paint") return;
  sectorRing(p);
  if (!g || !p) return;
  const x = p.x / SCALE, y = p.z / SCALE, spacing = g.radius / 2;
  let [lx, ly] = g.last, dist = Math.hypot(x - lx, y - ly);
  while (dist >= spacing && g.points.length < 5000) {
    lx += (x - lx) * spacing / dist;
    ly += (y - ly) * spacing / dist;
    g.points.push([Math.round(lx), Math.round(ly)]);
    sectorDab(lx, ly, g.value);
    dist = Math.hypot(x - lx, y - ly);
  }
  g.last = [lx, ly];
}

// Let go: the drag saved as one stroke; a new sector stays picked, so the next drag paints more of it.
function sectorUp() {
  const g = sec.painting;
  sec.painting = null;
  if (!g) return;
  if (sec.pick === "new") sec.pick = g.value;
  sectorCall(() => mv.api.sector_paint(mv.current, g.file, g.value, g.radius, g.points, sec.shape));
}

// The brush's outline under the pointer, in the picked sector's colour (red: No sector).
function sectorRing(p) {
  const gl = mv.gl;
  if (!gl || !gl.ring) return;
  const r = sectorRadius() * SCALE, square = sec.shape === "square";
  gl.ring.visible = Boolean(p) && !square;
  gl.squareRing.visible = Boolean(p) && square;
  if (p) {
    const value = sec.pick === "new" ? (sec.view ? sec.view.next : 0) : sec.pick;
    if (value === -1 || value === null) gl.ring.material.color.setHex(0xe0533d);
    else gl.ring.material.color.setRGB(...sectorRgb(value).map((c) => c / 255));
    gl.ring.position.set(p.x, p.y + r * 0.02, p.z);
    gl.ring.scale.set(r, r, r);
    gl.squareRing.position.set(p.x, p.y + r * 0.02, p.z);
    gl.squareRing.scale.set(r * Math.SQRT2, r * Math.SQRT2, r * Math.SQRT2);
    gl.squareRing.rotation.set(-Math.PI / 2, 0, 0);
  }
  gl.draw();
}

function watchSectorPointer(canvas) {
  let pending = null, frame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    if (scen.tool !== "sectors") return;
    pending = ev;
    if (!frame) frame = requestAnimationFrame(() => { frame = 0; if (scen.tool === "sectors" && pending) sectorMove(hitGround(pending)); });
  });
  for (const type of ["pointerup", "pointercancel"]) canvas.addEventListener(type, () => { if (sec.painting) sectorUp(); });
  canvas.addEventListener("pointerleave", () => { if (scen.tool === "sectors") sectorRing(null); });
  // Shapes: a press on a dot (or a box for a new sector) is taken before the view turns (as Drag to move does)
  const host = canvas.parentElement;
  host.addEventListener("pointerdown", sectorShapeDown, { capture: true });
  let shapeEv = null, shapeFrame = 0;
  host.addEventListener("pointermove", (ev) => {
    if (!sectorShapesOn()) return;
    shapeEv = ev;
    if (!shapeFrame) shapeFrame = requestAnimationFrame(() => { shapeFrame = 0; if (shapeEv) sectorShapeMove(shapeEv); });
  });
  for (const type of ["pointerup", "pointercancel"]) host.addEventListener(type, () => { if (sec.drag || sec.newBox) sectorShapeUp(); });
  canvas.addEventListener("dblclick", sectorAddDot);
  // right-drag moves the view: only a right-click that stays put takes a dot out
  let rightAt = null;
  host.addEventListener("pointerdown", (ev) => { rightAt = ev.button === 2 ? [ev.clientX, ev.clientY] : null; }, { capture: true });
  canvas.addEventListener("contextmenu", (ev) => {
    if (rightAt && Math.hypot(ev.clientX - rightAt[0], ev.clientY - rightAt[1]) <= 4) sectorRemoveDot(ev);
    rightAt = null;
  });
  $("scen-sectors-size").addEventListener("input", (e) => {
    sec.size = Number(e.target.value) || 1;
    $("scen-sectors-size-label").textContent = fill(mv.words.sectors_size, { pct: sec.size });
  });
  $("scen-sectors-outlines").addEventListener("change", (e) => {
    sec.outlines = e.target.checked;
    if (sec.outlines && sec.file) loadSectorView(true);
    else sectorDrawLines();
  });
}

// Save a change, then draw the scenario as the mod leaves it now.
async function scenEdit(call, keepPicked = false) {
  try {
    const keepFile = ((scen.data || {}).scenarios || [])[scen.pick];
    scen.data = await call();
    const i = scen.data.scenarios.findIndex((x) => keepFile && x.file === keepFile.file);
    if (i >= 0) scen.pick = i;
    if (!keepPicked) scen.selected = null;  // a value of the picked item changed (renderItemDetails): it stays picked
    renderScenarioPick();
    drawScenario();
    renderScenTools();
  } catch (err) { scenNote((err && err.message) || String(err), "error"); }
}

function scenPointerDown(ev) {
  const gl = mv.gl, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (scen.tool === "cameras" && ev.button === 0 && gl.ground && mv.edit) {  // Camera moves: the next point, or the look
    ev.preventDefault();
    const p = hitGround(ev);
    if (p && window.MissionView) window.MissionView.cameraClick(p.x / SCALE, p.z / SCALE, p.y / SCALE);
    return;
  }
  if (!scen.tool || FORM_TOOLS.has(scen.tool) || ev.button !== 0 || !gl.ground || !mv.edit || !s) return;
  ev.preventDefault();
  if (scen.tool === "sectors") { sectorDown(ev, s); return; }  // the Sectors brush: a drag paints
  // Move, pressed on the ground (a press on an item is grabStart's): a box dragged selects every spawn in it (no mod
  // needed); a click puts the item picked there, or clears what's selected (boxEnd)
  if (scen.tool === "move") { boxStart(ev); return; }
  if (!mv.brush.mod) { scenNote(mv.words.no_mod, "error"); return; }
  const p = hitGround(ev);
  if (!p) return;
  scenPlaceAt(s, p.x / SCALE, p.z / SCALE);
}

// --- Drag to move (the owner, 2026-10-03: "a selector tool where you can then just go grab any of these little things
// on the map and move it around"): with no placing tool picked (or Move), press on a starting point, a spawn (the
// map's supply depots too) or a start's camera and drag; let go and it's saved in the mod, as the Move tool saves it.
// A camera goes round its HQ (the camera ring); a depot spot and a starting point stick to roads when that's on.
// Pressing on empty ground still turns the view. ---
const GRABBABLE = ["StartingPoint", "Spawn", "LabelVille", "LabelMontagne", "Name", "CircularZone", "RectangleZone"];

// On the Scenario side the scenario's things move (on the Map side they're faded and locked), except the towns' and
// hills' names: those move on the Map side, looking around or with Names open.
function canGrab() {
  const tools = mv.mode === "scenario" ? !scen.tool || scen.tool === "move" || FORM_TOOLS.has(scen.tool)
    : !scen.tool || scen.tool === "names";
  return Boolean(mv.gl && mv.edit && scen.group && scen.group.visible && !mv.brush.on && !mv.place.on && !road.on
    && !bridge.on && tools);
}

// What a press at `ev` would grab: {cam: the start} for a camera's grip, {it, objs} for an item (its drawn parts), or null
function grabAt(ev) {
  const gl = mv.gl, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!s || !canGrab()) return null;
  const rect = gl.renderer.domElement.getBoundingClientRect();
  gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  gl.raycaster.setFromCamera(gl.ndc, gl.camera);
  const onMap = mv.mode === "map";   // the Map side grabs the names alone, the Scenario side everything but them
  const items = (onMap ? (scen.names ? scen.names.children : []) : scen.group.children)
    .filter((o) => o.userData.item !== undefined);
  const grips = onMap ? [] : scen.group.children.flatMap((o) => o.isGroup && o !== scen.names ? o.children : [])
    .filter((o) => o.userData.camOf !== undefined);
  const hit = gl.raycaster.intersectObjects([...items, ...grips], false)[0];
  if (!hit) return null;
  if (hit.object.userData.camOf !== undefined) {
    const it = s.items.find((x) => x.item === hit.object.userData.camOf);
    return it && it.cam ? { cam: it, s } : null;
  }
  const it = s.items.find((x) => x.item === hit.object.userData.item);
  if (!it || !GRABBABLE.includes(it.kind)) return null;
  const own = scen.group.children.find((o) => o.isGroup && o.userData.camItem === it.item);  // its camera moves with it
  return { it, s, objs: items.filter((o) => o.userData.item === it.item).concat(own ? [own] : []) };
}

function grabStart(ev) {
  if (ev.button !== 0) return false;
  const g = grabAt(ev);
  if (!g) return false;
  ev.preventDefault();
  ev.stopPropagation();  // the view doesn't turn under the drag
  const add = ev.shiftKey || ev.ctrlKey;
  // selecting needs no mod (moving does); Shift+click only selects; one taken out is picked (to put back), never dragged
  if (!mv.brush.mod || (add && !g.cam) || (g.it && g.it.gone)) {
    if (g.it) selectSpawn(g.it, add);
    if (!mv.brush.mod && !add) scenNote(mv.words.no_mod);  // why it won't move: a hint, not an error
    return true;
  }
  const host = mv.gl.renderer.domElement.parentElement;
  host.setPointerCapture(ev.pointerId);
  if (g.cam) {
    const it = g.cam, rest = it.cam.path[it.cam.path.length - 1];
    scen.camDrag = { it, cam: it.cam, from: Math.atan2(rest[1] - it.y, rest[0] - it.x), turn: 0 };
    return true;
  }
  const grid = makeGrid(mv.edit);
  scen.itemDrag = { ...g, grid, x0: g.it.x, y0: g.it.y, x: g.it.x, y: g.it.y, moved: false, sx: ev.clientX, sy: ev.clientY,
    start: g.objs.map((o) => ({ o, x: o.position.x, y: o.position.y, z: o.position.z })) };
  mv.gl.renderer.domElement.style.cursor = "grabbing";
  return true;
}

function itemDragMove(ev) {
  const d = scen.itemDrag, p = d && hitGround(ev);
  if (!p) return;
  if (Math.abs(ev.clientX - d.sx) + Math.abs(ev.clientY - d.sy) > 3) d.moved = true;
  d.x = p.x / SCALE;
  d.y = p.z / SCALE;
  const dx = (d.x - d.x0) * SCALE, dz = (d.y - d.y0) * SCALE;
  const lift = (groundAt(d.grid, d.x, d.y) - groundAt(d.grid, d.x0, d.y0)) * SCALE;
  for (const { o, x, y, z } of d.start) {
    if (o.isGroup) o.position.set(dx, lift, dz);  // the camera's parts are placed in map space: the group slides
    else o.position.set(x + dx, y + lift, z + dz);
  }
  mv.gl.draw();
}

async function itemDragEnd() {
  const d = scen.itemDrag;
  scen.itemDrag = null;
  pointerMode();
  if (!d || !d.moved) { if (d) selectSpawn(d.it, false); return; }  // a click: that one's selected
  const it = d.it, kind = snapKind(it, null);
  const [x, y] = kind ? await snapToRoad(kind, d.x, d.y) : [d.x, d.y];
  moveItem(d.s, it, x, y);
}

// Save item `it` of scenario `s` at x, y: the mod's own starting point, spawn or name/point/zone, or the map's own
function moveItem(s, it, x, y) {
  if (it.mine && it.start !== undefined) scenEdit(() => mv.api.scenario_move_start(mv.current, it.start, x, y));
  else if (it.mine && it.place !== undefined) scenEdit(() => mv.api.scenario_move_place(mv.current, it.place, x, y));
  else if (it.mine) scenEdit(() => mv.api.scenario_move_spawn(mv.current, it.spawn, x, y));
  else scenEdit(() => mv.api.scenario_move(mv.current, s.file, it.item, x, y));
}

// A start's warm-up camera turned `a` radians about the start, as the build turns it (scenario.CamPaths.turn): the
// path goes round on its ring and the look turns as much, so it frames the HQ as before, from another side.
function turnedCam(cam, x, y, a) {
  const c = Math.cos(a), sn = Math.sin(a);
  return { ...cam, path: cam.path.map(([px, py, pz]) => [x + (px - x) * c - (py - y) * sn, y + (px - x) * sn + (py - y) * c, pz]),
    look: cam.look && [cam.look[0] * c - cam.look[1] * sn, cam.look[0] * sn + cam.look[1] * c, cam.look[2]] };
}

// Dragging a camera: it follows the pointer's angle round its HQ (its distance and height stay); only its own
// drawing is redone each frame.
function camDragMove(ev) {
  const d = scen.camDrag, p = d && hitGround(ev);
  if (!p) return;
  d.turn = Math.atan2(p.z / SCALE - d.it.y, p.x / SCALE - d.it.x) - d.from;
  const own = scen.group && scen.group.children.find((o) => o.isGroup && o.userData.camItem === d.it.item);
  if (!own) return;
  own.clear();
  drawStartCamera({ ...d.it, cam: turnedCam(d.cam, d.it.x, d.it.y, d.turn) }, own, own.userData.colour, own.userData.at);
  scenNote(fill(mv.words.scen_cam_turned || "Camera turned {deg}°", { deg: Math.round(degOf((d.it.camera || 0) + d.turn)) }));
  mv.gl.draw();
}

// -180..180 degrees
function degOf(a) {
  return ((a * 180 / Math.PI) % 360 + 540) % 360 - 180;
}

// Let go: the turn is saved (the start's whole turn, from where the game has its camera).
function camDragEnd() {
  const d = scen.camDrag, s = ((scen.data || {}).scenarios || [])[scen.pick];
  scen.camDrag = null;
  if (!d || !s || Math.abs(d.turn) < 1e-3) { renderScenTools(); return; }
  saveCamTurn(s, d.it, (d.it.camera || 0) + d.turn);
}

function saveCamTurn(s, it, turn) {
  const keep = it.item;
  scenEdit(() => it.mine && it.start !== undefined ? mv.api.scenario_turn_start_camera(mv.current, it.start, turn)
    : mv.api.scenario_turn_camera(mv.current, s.file, it.item, turn)).then(() => { scen.selected = keep; drawScenario(); renderScenTools(); });
}

// The scenario tools' click on the ground at (cx, cy): move, add a starting point, or spawn (Stick to roads applied)
async function scenPlaceAt(s, cx, cy) {
  if (scen.tool === "move") {
    const it = s.items[scen.selected], kind = snapKind(it, null);
    const [x, y] = kind ? await snapToRoad(kind, cx, cy) : [cx, cy];
    moveItem(s, it, x, y);
    return;
  }
  if (scen.tool === "mark" || scen.tool === "names") {  // a new name on the map, named point or zone where clicked
    const kind = scen.markKind, words = $("scen-mark-words").value.trim();
    if ((kind === "LabelVille" || kind === "LabelMontagne") && !words) {
      scenNote(mv.words.scen_mark_words_first, "error");
      $("scen-mark-words").focus();
      return;
    }
    const metres = Number($("scen-mark-size").value);
    const size = (kind === "CircularZone" || kind === "RectangleZone") && metres > 0 ? metres * METRE : null;
    const before = new Set(s.items.map((it) => it.item));
    await scenEdit(() => mv.api.scenario_place(mv.current, s.file, kind, cx, cy, words, size));
    // the one just placed stays picked: its name and size in the tray, to change at once
    const now = ((scen.data || {}).scenarios || [])[scen.pick];
    const made = now && now.items.find((it) => it.kind === kind && it.mine && !before.has(it.item));
    if (made && kind !== "LabelVille" && kind !== "LabelMontagne") selectSpawn(made, false);
    return;
  }
  // a new starting point: the team's next place, beside a road unless the toggle's off
  if (scen.tool === "start") {
    const [x, y] = await snapToRoad("hq", cx, cy);
    scenEdit(() => mv.api.scenario_add_start(mv.current, s.file, scen.team, x, y)).then(() => loadPlayers(mv.current));
    return;
  }
  const unit = $("scen-unit").value, camp = scen.camp, [fx, fy] = screenAhead();
  if (!unit) { scenNote(mv.words.scen_pick_unit, "error"); return; }
  let points = formationPoints(cx, cy);
  if (snapKind(null, unit) === "depot") points = await Promise.all(points.map(([px, py]) => snapToRoad("depot", px, py)));
  scenEdit(() => mv.api.scenario_spawn_many(mv.current, s.file, unit, points,
    camp === "" ? null : Number(camp), Math.atan2(fy, fx), unit === DEPOT_SLAB && scen.trucksSet ? scen.trucks : null));
}

// Pointing at a zone, a starting point or a spawn says what it is.
function scenarioAt(ev) {
  const gl = mv.gl;
  if (!scen.group || !scen.group.visible) return "";
  const rect = gl.renderer.domElement.getBoundingClientRect();
  gl.ndc.set(((ev.clientX - rect.left) / rect.width) * 2 - 1, -((ev.clientY - rect.top) / rect.height) * 2 + 1);
  gl.raycaster.setFromCamera(gl.ndc, gl.camera);
  // the spawns' icons are sprites, not meshes: left out, pointing at a unit said nothing (a French player, 2026-10-05)
  const shown = scen.group.children.filter((o) => (o.isMesh || o.isSprite) && o.userData.label);
  const hit = gl.raycaster.intersectObjects(shown, false)[0];
  if (hit) return hit.object.userData.label || "";  // an icon, a pillar or a diamond before a zone
  if (!scen.zones || !scen.zones.visible || !gl.ground) return "";
  const p = gl.raycaster.intersectObject(gl.ground, false)[0];  // the zones under the pointer, on the map itself
  return p ? zoneAt(p.point.x / SCALE, p.point.z / SCALE) : "";
}

async function loadScenery(pack, ask) {
  clearScenery();
  $("scenery-stats").textContent = mv.words.scenery_loading;
  let data = await mv.api.map_scenery(pack);
  if (ask !== mv.ask || !mv.edit) return;
  if (blankMap(pack)) {  // every object of the map it copies is erased: none drawn or pointed at; the types stay (Place)
    const none = { shown: 0, total: 0 };
    data = { ...data, items: {}, groups: { building: none, prop: none, vegetation: none } };
  }
  mv.scenery.data = data;
  await loadOwn(ask);  // the mod's own models join its types (numbered after the map's) and the place list
  if (ask !== mv.ask || mv.scenery.data !== data) return;
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
// How a click places: one object; an area, painted by dragging (objects scattered at least `spacing` apart); a line
// between two clicks (objects every `spacing`, turned along it: a hedgerow, a tree line, a row of houses); a grid (a
// line, then rows moved out from it: gridOf); a box dragged on the ground, filled in rows (fillBox); or a path
// clicked along the way, curving through the clicks (pathOf: hedges, tree belts).
const PLACE_HOW = ["one", "area", "line", "path", "grid", "box", "select"];  // select: pick what stands on the map (sel)
const METRE = 260;  // world units in a metre (the game's distances: 260,000 to a kilometre)
const SPACING = { building: 20, prop: 8, vegetation: 6 };  // metres between objects to start with, per kind
const MOST = 800;  // objects one area or line may place at most, so a slip of the mouse can't bury a map
// the trees Forest strokes placed: the brushes' Undo takes them back with their cover, not the Place panel's
const forestTrees = new WeakSet();
// the dice for the objects' variety: Math.random, or a line's, grid's or box's own while it's made (withSeed)
let placeRand = Math.random;
const around = (turn, spread) => (turn + Math.round((placeRand() * 2 - 1) * spread) + 360) % 360;

function placeNote(text, kind) {
  const note = $("place-note");
  note.textContent = text || "";
  note.className = kind === "error" ? "small error-text" : "small";
}

// The list only holds the map's own types: the game can't take a type a map doesn't already use (StudioApi.scenery_add
// refuses it), so the search and the tooltip say so rather than offering every type in the game.
function placeOptions() {
  const d = mv.scenery.data, p = mv.place, q = $("place-search").value.trim().toLowerCase();
  // each row: [type, code name, group, the game editor's folder, how many the map has, its name, what it is], the
  // last two in each of the Studio's languages ({code: text}; rusemod.scenerynames: the game names scenery only in its
  // editor's code, mostly French), shown in the Studio's language, searched in it and in English
  const said = (v) => (typeof v === "string" ? v : (v && (v[mv.lang] || v.us)) || "");
  const rows = ((d && d.palette) || []).filter((r) => r[2] === p.group
    && (!q || [r[1], r[3], said(r[5]), said(r[6]), (r[5] && r[5].us) || "", (r[6] && r[6].us) || ""]
      .some((t) => t.toLowerCase().includes(q))));
  if (!rows.some((r) => r[0] === p.type)) p.type = rows.length ? rows[0][0] : null;
  // a tile each: a picture of its model (rendered once the models are in: renderThumb), its name, how many the map has
  const w = mv.words;
  $("place-grid").replaceChildren(...rows.map((r) => {
    const name = said(r[5]) || r[1], what = said(r[6]), pic = thumbOf(r[0]), mine = r[8];  // mine: the mod's own model
    const tile = el("button", { type: "button", className: mine ? "place-tile own" : "place-tile",
      title: `${name}${what ? " · " + what : ""}`
      + (r[4] ? `\n${fill(w.place_used, { n: r[4].toLocaleString() })}` : "")
      + (pic === false ? `\n${w.place_no_picture}` : "")
      + (mine ? `\n${assetInfo(mine)}` : `\n${w.place_code || "In the game's files"}: ${r[1]} (${r[3]})`) });
    tile.dataset.type = r[0];
    tile.setAttribute("role", "option");
    tile.setAttribute("aria-selected", String(r[0] === p.type));
    tile.append(el("span", { className: "place-pic" }, pic ? el("img", { src: pic, alt: "" }) : kindIcon(p.group)),
      el("span", { className: "place-name", textContent: name }));
    if (r[4]) tile.append(el("span", { className: "place-count", textContent: r[4].toLocaleString() }));
    if (mine) tile.append(el("span", { className: "place-own-tag", textContent: w.asset_tag }));
    tile.addEventListener("click", () => pickType(r[0]));
    if (mine) tile.addEventListener("dblclick", () => openAsset(mine));
    return tile;
  }));
  renderOwnRow();
}

// Picking a type starts placing, as picking a brush starts painting
function pickType(type) {
  mv.place.type = type;
  for (const tile of $("place-grid").children) tile.setAttribute("aria-selected", String(tile.dataset.type === type));
  renderOwnRow();
  if (!mv.place.on) setPlaceMode(true); else placeNote("");
}

// --- the mod's own models (StudioApi.assets, asset_import, asset_change, asset_remove, asset_models; rusemod.sceneryasset;
// the owner, 2026-10-18: "let's start working on the importers. The asset importer and building importers, and then the
// map importer"): a model file made one of the map mod's rocks, props, plants or trees, first in the Props and Trees
// lists with a "yours" mark. Each joins the map's types after the map's own (its number follows theirs), so it's drawn,
// pictured and placed as they are; the build puts it in the game on every map of the mod. ---
const OWN_KINDS = { prop: ["rock", "prop"], vegetation: ["plant", "tree"] };  // the kinds each list imports
const LICENCES = ["", "CC0", "CC-BY"];  // "": a model of one's own (the build takes others' only under these two)
// the mod's models (StudioApi.assets); the dialog: the model shown (null: a new one), its kind, a file waiting on
// "replace it?" or a model waiting on "remove it?" (sure), busy while the Studio imports
const own = { list: [], editing: null, kind: "prop", sure: null, busy: false };

async function loadOwn(ask) {
  let res = null;
  try { res = await mv.api.assets(); } catch (err) { placeNote((err && err.message) || String(err), "error"); }
  if (ask !== mv.ask) return;
  own.list = (res && res.assets) || [];
  mergeOwn(mv.scenery.data);
}

// The mod's models into the map's types and place list (the ones from before taken out first)
function mergeOwn(d) {
  if (!d) return;
  if (d.ownFrom !== undefined) {
    d.types.length = d.ownFrom;
    d.palette = d.palette.filter((r) => !r[8]);
  }
  d.ownFrom = d.types.length;
  const rows = own.list.map((a) => {
    d.types.push([a.name, a.group, a.label, a.file, [a.file], false]);
    return [a.type, a.name, a.group, a.label, 0, { us: a.name }, fill(mv.words.asset_what, { kind: kindWord(a.kind) }),
      d.types.length - 1, a];
  });
  d.palette = rows.concat(d.palette);
  d.numbers = null;  // (typeNumber reads them again)
}

function kindWord(kind) {
  return mv.words[`asset_kind_${kind}`] || kind;
}

// The mod's models as the 3D view draws them (StudioApi.asset_models): a source for modelLibrary, its models by their
// numbers in the map's types; null when the mod has none
async function ownModels(ask) {
  if (!own.list.length) return null;
  let res;
  try { res = await mv.api.asset_models(); } catch (err) { placeNote((err && err.message) || String(err), "error"); return null; }
  if (ask !== mv.ask || !res || !res.index || !res.index.bin) return null;
  const models = {};
  for (const [type, parts] of Object.entries(res.index.models)) {
    const t = typeNumber(type);
    if (t !== null) models[t] = parts;
  }
  const buf = await (await fetch(res.base + res.index.bin)).arrayBuffer();
  return { base: res.base, index: { ...res.index, models }, buf };
}

// After an import, a change or a removal: the list, the place list and the models again
async function refreshOwn(res) {
  own.list = (res && res.assets) || [];
  const d = mv.scenery.data;
  mergeOwn(d);
  thumbs.lib = null;  // (the pictures are drawn again with the new models)
  placeOptions();
  if (d && mv.current) await loadModels(mv.current, mv.ask, blankMap(mv.current));
  drawPlaced();
}

// "file: 1,234 triangles; middle: 600; far: 120 · From <source> by <author> (licence)"
function assetInfo(a) {
  const w = mv.words, n = (v) => (v === null || v === undefined ? "?" : v.toLocaleString());
  const v = a.versions || {};
  let text = fill(w.asset_info, { file: a.file, triangles: n(a.triangles), middle: n((v.medium || {}).triangles),
    far: n((v.far || {}).triangles) });
  const c = a.credit || {};
  if (c.source || c.author || c.licence) {
    text += "\n" + fill(w.asset_credit_line, { source: c.source || "?", author: c.author || "?",
      licence: c.licence || w.asset_licence_own });
  }
  return text;
}

// Import model under the search in the Props and Trees lists; Your model… when one of the mod's is picked
function renderOwnRow() {
  const w = mv.words, p = mv.place, kinds = OWN_KINDS[p.group];
  $("place-own").classList.toggle("hidden", !kinds);
  const imp = $("place-import");
  imp.textContent = w.asset_import;
  imp.title = mv.place.mod ? w.tip_asset_import : w.no_mod;
  imp.disabled = !mv.place.mod;
  const mine = ownOf(p.type), edit = $("place-own-edit");
  edit.classList.toggle("hidden", !kinds || !mine);
  edit.textContent = w.asset_edit;
  edit.title = w.tip_asset_edit;
}

function ownOf(type) {
  return own.list.find((a) => a.type === type) || null;
}

// The dialog: a new model (`a` null: Choose the model file… imports it) or one of the mod's (its settings saved,
// replaced by another file, or removed)
function openAsset(a) {
  own.editing = a || null;
  own.kind = a ? a.kind : (OWN_KINDS[mv.place.group] || OWN_KINDS.prop)[0];
  own.sure = null;
  $("asset-name").value = a ? a.name : "";
  $("asset-size").value = a ? a.size : 1;
  slideTo(a ? a.size : 1);
  $("asset-solid").checked = a ? Boolean(a.solid) : false;
  $("asset-two").checked = a ? a.two_sided : false;
  const c = (a && a.credit) || {};
  $("asset-licence").value = LICENCES.includes(c.licence || "") ? c.licence || "" : "";
  $("asset-source").value = c.source || "";
  $("asset-author").value = c.author || "";
  assetNote("");
  renderAsset();
  if (!$("asset-box").open) $("asset-box").showModal();
}

function assetNote(text, bad) {
  const note = $("asset-note");
  note.textContent = text || "";
  note.className = bad ? "small error-text" : "small";
}

function renderAsset() {
  const w = mv.words, a = own.editing;
  $("asset-title").textContent = a ? fill(w.asset_title_edit, { name: a.name }) : w.asset_title_new;
  $("asset-lead").textContent = w.asset_lead;
  // a new one: its kind (rock or prop, plant or tree); one of the mod's keeps its own (its type is made of it)
  const kinds = a ? [a.kind] : OWN_KINDS[mv.place.group] || [...OWN_KINDS.prop, ...OWN_KINDS.vegetation];
  $("asset-kinds").replaceChildren(...kinds.map((k) => {
    const chip = el("button", { type: "button", className: "chip", textContent: kindWord(k), title: w[`tip_asset_kind_${k}`] || "" });
    chip.setAttribute("aria-pressed", String(own.kind === k));
    chip.disabled = Boolean(a) || own.busy;
    chip.addEventListener("click", () => { own.kind = k; renderAsset(); });
    return chip;
  }));
  $("asset-name-label").textContent = w.asset_name;
  $("asset-name").placeholder = w.asset_name_from_file;
  $("asset-name").title = w.tip_asset_name;
  $("asset-name").disabled = Boolean(a);  // (placed ones name it: a new name is a new model)
  if (a) $("asset-name").value = a.name;
  $("asset-size-label").textContent = w.asset_size;
  $("asset-size").title = w.tip_asset_size;
  $("asset-size-slide").title = w.tip_asset_size_slide;
  $("asset-size-slide").disabled = own.busy;
  renderMetres();
  $("asset-solid-label").textContent = w.asset_solid;
  $("asset-solid").parentElement.title = w.tip_asset_solid;
  $("asset-solid").disabled = own.busy;
  $("asset-two-label").textContent = w.asset_two_sided;
  $("asset-two").parentElement.title = w.tip_asset_two_sided;
  $("asset-credit-title").textContent = w.asset_credit;
  $("asset-licence-label").textContent = w.asset_licence;
  const lic = $("asset-licence"), was = lic.value;
  lic.replaceChildren(...LICENCES.map((l) => el("option", { value: l,
    textContent: { "": w.asset_licence_own, CC0: w.asset_licence_free, "CC-BY": w.asset_licence_credit }[l] })));
  lic.value = was;
  lic.title = w.tip_asset_licence;
  $("asset-source-label").textContent = w.asset_source;
  $("asset-source").title = w.tip_asset_source;
  $("asset-author-label").textContent = w.asset_author;
  $("asset-author").title = w.tip_asset_author;
  $("asset-info").textContent = a ? assetInfo(a) : w.asset_files;
  const s = own.sure;
  $("asset-sure").classList.toggle("hidden", !s);
  if (s) {
    $("asset-sure-text").textContent = s.kind === "replace" ? fill(w.asset_exists, { name: s.name })
      : s.placed ? fill(w.asset_placed, { n: Object.values(s.placed).reduce((x, y) => x + y, 0).toLocaleString(),
        maps: Object.keys(s.placed).map(mapName).join(", ") }) : fill(w.asset_remove_sure, { name: s.name });
    $("asset-sure-yes").textContent = s.kind === "replace" ? w.asset_replace : w.asset_remove_yes;
    $("asset-sure-no").textContent = w.asset_keep;
  }
  const pick = $("asset-pick");
  pick.textContent = a ? w.asset_pick_again : w.asset_pick;
  pick.title = mv.place.mod ? w.tip_asset_pick : w.no_mod;
  pick.disabled = own.busy || !mv.place.mod || Boolean(s);
  const save = $("asset-save");
  save.classList.toggle("hidden", !a);
  save.textContent = w.asset_save;
  save.disabled = own.busy || Boolean(s);
  const remove = $("asset-remove");
  remove.classList.toggle("hidden", !a);
  remove.textContent = w.asset_remove;
  remove.title = w.tip_asset_remove;
  remove.disabled = own.busy || Boolean(s);
  $("asset-close").textContent = w.close;
}

function assetForm() {
  return { size: Number($("asset-size").value) || 1, two: $("asset-two").checked, solid: $("asset-solid").checked,
    licence: $("asset-licence").value, source: $("asset-source").value.trim(), author: $("asset-author").value.trim() };
}

// The size slider runs 0.1 to 10 times, even steps either side of 1 (its value is the size's power of ten); the number
// beside it is the exact size (0.01 to 100)
function slideTo(size) {
  $("asset-size-slide").value = String(Math.max(-1, Math.min(1, Math.log10(Number(size) || 1))));
}

function slidSize() {
  const v = 10 ** Number($("asset-size-slide").value);
  return Number(v < 1 ? v.toFixed(2) : v.toFixed(1));
}

// "About 8 × 11 m across and 6 m high" at the size set now (one of the mod's models: measured by the Studio)
function renderMetres() {
  const a = own.editing, m = a && a.metres, out = $("asset-metres");
  const size = Number($("asset-size").value) || 1;
  if (!m) { out.textContent = ""; return; }
  const n = (v) => { const x = v * size; return (x < 10 ? x.toFixed(1) : Math.round(x)).toLocaleString(); };
  out.textContent = fill(mv.words.asset_metres, { across: n(m[0]), deep: n(m[1]), high: n(m[2]) });
}

// Choose the model file… (or, after "replace it?", the file picked then): imported into the mod
async function importAsset(file, replaceIt) {
  const a = own.editing, f = assetForm(), w = mv.words;
  const name = a ? a.name : $("asset-name").value.trim();
  own.busy = true;
  own.sure = null;
  assetNote(w.asset_importing);
  renderAsset();
  try {
    const res = await mv.api.asset_import(a ? a.kind : own.kind, file || null, name, f.size, f.two, f.source, f.author,
      f.licence, Boolean(replaceIt || a), f.solid);
    if (res.exists) {  // the mod has a model of that name: asked before it's replaced
      own.sure = { kind: "replace", name: res.exists, file: res.file };
      assetNote("");
      return;
    }
    if (!res.asset) { assetNote(""); return; }  // (no file picked)
    own.editing = res.asset;
    await refreshOwn(res);
    own.editing = ownOf(res.asset.type) || res.asset;
    pickType(res.asset.type);
    assetNote(fill(w.asset_done, { name: res.asset.name }));
  } catch (err) {
    assetNote((err && err.message) || String(err), true);
  } finally {
    own.busy = false;
    renderAsset();
  }
}

async function saveAsset() {
  const a = own.editing, f = assetForm();
  if (!a) return;
  own.busy = true;
  renderAsset();
  try {
    const res = await mv.api.asset_change(a.name, f.size, f.two, f.source, f.author, f.licence, f.solid);
    await refreshOwn(res);
    own.editing = ownOf(a.type);
    assetNote(mv.words.asset_saved);
  } catch (err) {
    assetNote((err && err.message) || String(err), true);
  } finally {
    own.busy = false;
    renderAsset();
  }
}

// Remove this model: asked first; where it's placed, those go too once that's said yes to
async function removeAsset(sure) {
  const a = own.editing;
  if (!a) return;
  if (!sure) {
    own.sure = { kind: "remove", name: a.name, placed: null };
    renderAsset();
    return;
  }
  own.busy = true;
  renderAsset();
  try {
    const res = await mv.api.asset_remove(a.name, Boolean(own.sure && own.sure.placed));
    if (res.placed) {  // placed on maps: asked again, saying where
      own.sure = { kind: "remove", name: a.name, placed: res.placed };
      return;
    }
    own.sure = null;
    await refreshOwn(res);
    if (mv.current) await loadPlaced(mv.current, mv.ask);  // (those placed of it are gone from the file)
    if (mv.place.type === a.type) mv.place.type = null;
    placeOptions();
    $("asset-box").close();
  } catch (err) {
    own.sure = null;
    assetNote((err && err.message) || String(err), true);
  } finally {
    own.busy = false;
    if ($("asset-box").open) renderAsset();
  }
}

function wireAsset() {
  $("place-import").addEventListener("click", () => openAsset(null));
  $("place-own-edit").addEventListener("click", () => { const a = ownOf(mv.place.type); if (a) openAsset(a); });
  $("asset-pick").addEventListener("click", () => importAsset(null, false));
  $("asset-save").addEventListener("click", () => saveAsset());
  // the slider and the number follow each other; letting go of the slider, or ticking Solid, saves one of the mod's
  // models at once, so the map behind shows its new size
  $("asset-size-slide").addEventListener("input", () => { $("asset-size").value = slidSize(); renderMetres(); });
  $("asset-size-slide").addEventListener("change", () => { if (own.editing && !own.busy) saveAsset(); });
  $("asset-size").addEventListener("input", () => { slideTo($("asset-size").value); renderMetres(); });
  $("asset-solid").addEventListener("change", () => { if (own.editing && !own.busy) saveAsset(); });
  $("asset-remove").addEventListener("click", () => removeAsset(false));
  $("asset-sure-yes").addEventListener("click", () => {
    const s = own.sure;
    if (!s) return;
    if (s.kind === "replace") importAsset(s.file, true);
    else removeAsset(true);
  });
  $("asset-sure-no").addEventListener("click", () => { own.sure = null; renderAsset(); });
  $("asset-close").addEventListener("click", () => $("asset-box").close());
  $("asset-box").addEventListener("keydown", (e) => e.stopPropagation());  // keys never move the map behind it
}

function kindIcon(kind) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.innerHTML = `<path d="${ICONS[kind] || ICONS.building}"/>`;
  return svg;
}

// --- the place list's pictures: each type's model drawn once, small, from above at three quarters, on a renderer of
// their own (made the first time); a type's picture is kept while the map's models are. ---
const THUMB = 112;  // pixels
const thumbs = { lib: null, cache: new Map(), queue: [], busy: false, renderer: null, scene: null, camera: null };

// A type's picture: its address once drawn, null while it's on the way (the tile is filled in then), false when the
// type has no model to draw (or the models aren't in yet: the tiles are made again when they are)
function thumbOf(type) {
  const lib = mv.scenery.lib, t = typeNumber(type);
  if (!lib) return null;
  if (t === null || !lib.has(t)) return false;
  if (thumbs.lib !== lib) Object.assign(thumbs, { lib, cache: new Map(), queue: [] });
  if (thumbs.cache.has(type)) return thumbs.cache.get(type);
  thumbs.cache.set(type, null);
  thumbs.queue.push(type);
  if (!thumbs.busy) drawThumbs();
  return null;
}

async function drawThumbs() {
  thumbs.busy = true;
  try {
    while (thumbs.queue.length) {
      const lib = thumbs.lib, type = thumbs.queue.shift(), t = typeNumber(type);
      await lib.ready(t);  // its pictures loaded first
      if (thumbs.lib !== lib || mv.scenery.lib !== lib) break;
      const url = renderThumb(lib, t, groupOfType(type));
      thumbs.cache.set(type, url);
      for (const tile of $("place-grid").children) {
        if (tile.dataset.type === type) tile.firstChild.replaceChildren(el("img", { src: url, alt: "" }));
      }
      await new Promise((done) => setTimeout(done, 0));  // the page stays quick while they're drawn
    }
  } finally {
    thumbs.busy = false;
  }
}

function renderThumb(lib, t, group) {
  const { THREE } = mv.gl;
  if (!thumbs.renderer) {
    thumbs.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    thumbs.renderer.setPixelRatio(1);
    thumbs.renderer.setSize(THUMB, THUMB, false);
    thumbs.scene = new THREE.Scene();
    thumbs.scene.add(new THREE.HemisphereLight(0xe3ecf2, 0x6a5a44, 2.6));  // brighter than the map: a picture to read
    const sun = new THREE.DirectionalLight(0xfff1dc, 2.8);
    sun.position.set(0.4, 1.0, 0.9);  // from above, behind the camera's shoulder: the faces seen are lit
    thumbs.scene.add(sun);
    thumbs.camera = new THREE.PerspectiveCamera(30, 1, 1, 1);
  }
  const model = new THREE.Group(), box = new THREE.Box3();
  for (const part of lib.parts(t)) {
    model.add(new THREE.Mesh(part.geo, lib.material(group, part)));
    box.union(part.geo.boundingBox);
  }
  thumbs.scene.add(model);
  const cam = thumbs.camera, centre = box.getCenter(new THREE.Vector3());
  const r = Math.max(box.getSize(new THREE.Vector3()).length() / 2, 1);
  const dist = r / Math.sin(cam.fov * Math.PI / 360);
  cam.position.copy(centre).addScaledVector(new THREE.Vector3(0.9, 0.75, 1.3).normalize(), dist);  // from the south-east
  cam.near = dist / 50;
  cam.far = dist * 3;
  cam.updateProjectionMatrix();
  cam.lookAt(centre);
  thumbs.renderer.render(thumbs.scene, cam);
  const url = thumbs.renderer.domElement.toDataURL("image/png");
  thumbs.scene.remove(model);
  for (const m of model.children) m.material.dispose();
  return url;
}

function renderPlace() {
  const w = mv.words, p = mv.place;
  $("place-scenery-note").textContent = w.scenery_note;  // no cover from placed scenery; buildings stop units
  renderOwnRow();
  $("place-search").placeholder = w.search || "";
  $("place-search").title = w.tip_place_search;
  $("place-grid").title = w.tip_place_type;
  $("place-turn-label").textContent = `${w.place_turn} ${p.turn}°`;
  $("place-turn").title = w.tip_place_turn;
  $("place-size-label").textContent = `${w.brush_size} ${p.size.toFixed(1)}×`;
  $("place-size").title = w.tip_place_size;
  typedBeside("place-size", TYPED.place, () => p.size, (n) => { p.size = n; renderPlace(); }, w.tip_place_size);
  $("place-solid-row").classList.toggle("hidden", p.group !== "building" || p.how === "select");  // only buildings stop units
  $("place-solid").checked = p.solid;
  $("place-solid-label").textContent = w.place_solid;
  $("place-solid-row").title = w.tip_place_solid;
  const picking = p.how === "select";
  if (picking && sel.items.length) {  // Turn and Size say the first picked one's, and set every picked one's
    const first = selPose(sel.items[0]);
    if (first) {
      $("place-turn-label").textContent = `${w.place_turn} ${Math.round(((first.turn % 360) + 360) % 360)}°`;
      $("place-size-label").textContent = `${w.brush_size} ${first.size.toFixed(2)}×`;
    }
  }
  $("place-undo").textContent = w.brush_undo;
  $("place-undo").title = picking ? w.tip_sel_undo : w.tip_place_undo;
  $("place-undo").disabled = picking ? !sel.undo.length || sel.busy : !p.objects.length;
  $("place-redo").textContent = w.brush_redo;
  $("place-redo").title = picking ? w.tip_sel_redo : w.tip_place_redo;
  $("place-redo").disabled = picking ? !sel.redo.length || sel.busy : !redo.place.length || !p.mod;
  renderSel();
  $("place-count").textContent = p.objects.length ? fill(w.place_count, { n: p.objects.length.toLocaleString() }) : "";
  $("place-how").replaceChildren(...PLACE_HOW.map((how) => {
    const chip = el("button", { type: "button", className: "chip", textContent: w[`place_${how}`], title: w[`tip_place_${how}`] });
    chip.setAttribute("aria-pressed", String(p.how === how));
    chip.addEventListener("click", () => {
      p.how = how;
      dropPlaceGesture();
      showPlaceGhost(null);
      if (!p.on) setPlaceMode(true); else renderPlace();
      drawSelection();  // the picks' rings show in Select (and stay picked when another way is tried)
    });
    return chip;
  }));
  $("place-spacing-row").classList.toggle("hidden", p.how === "one" || p.how === "select");
  $("place-area-row").classList.toggle("hidden", p.how !== "area");
  $("place-spacing").value = spacingOf(p.group);
  $("place-spacing-label").textContent = fill(w.place_spacing, { m: spacingOf(p.group) });
  $("place-spacing").title = w.tip_place_spacing;
  typedBeside("place-spacing", TYPED.spacing, () => spacingOf(p.group), (n) => { p.spacing[p.group] = n; renderPlace(); },
    w.tip_place_spacing);
  $("place-area").value = p.area;
  $("place-area-label").textContent = fill(w.place_area_size, { m: p.area });
  $("place-area").title = w.tip_place_area_size;
  typedBeside("place-area", TYPED.area, () => p.area, (n) => { p.area = n; renderPlace(); }, w.tip_place_area_size);
  $("place-rows-row").classList.toggle("hidden", p.how !== "grid" && p.how !== "box");
  $("place-rows").value = rowsOf(p.group);
  $("place-rows-label").textContent = fill(w.place_rows, { m: rowsOf(p.group) });
  $("place-rows").title = w.tip_place_rows;
  typedBeside("place-rows", TYPED.spacing, () => rowsOf(p.group), (n) => { p.rows[p.group] = n; renderPlace(); },
    w.tip_place_rows);
  // Face the roads: what stands (buildings, props), placed one by one or in rows; an area scatters, Select moves
  $("place-roads-row").classList.toggle("hidden", p.group === "vegetation" || p.how === "area" || p.how === "select");
  $("place-roads").checked = p.roads;
  $("place-roads-label").textContent = w.place_roads;
  $("place-roads-row").title = w.tip_place_roads;
  // Path: its width, its cover (trees), Finish, and Along the last path
  const path = p.how === "path";
  $("place-width-row").classList.toggle("hidden", !path);
  $("place-width").value = widthOf(p.group);
  $("place-width-label").textContent = widthOf(p.group) ? fill(w.place_width, { m: widthOf(p.group) }) : w.place_width_line;
  $("place-width").title = w.tip_place_width;
  typedBeside("place-width", [0, 1000], () => widthOf(p.group), (n) => { p.width[p.group] = n; renderPlace(); },
    w.tip_place_width);
  $("place-cover-row").classList.toggle("hidden", !path || p.group !== "vegetation");
  $("place-cover").checked = p.cover;
  $("place-cover-label").textContent = w.place_cover;
  $("place-cover-row").title = w.tip_place_cover;
  $("place-path-row").classList.toggle("hidden", !path);
  $("place-finish").textContent = w.road_finish || "Finish";
  $("place-finish").title = w.tip_place_finish;
  $("place-finish").disabled = !(p.path && p.path.pts.length >= 2);
  $("place-again").textContent = w.place_again;
  $("place-again").title = w.tip_place_again;
  $("place-again").disabled = !p.lastPath || !p.type || !p.mod;
  if (p.on) {
    $("map-help").textContent = { area: w.place_area_help, line: w.place_line_help, grid: w.place_grid_help,
      box: w.place_box_help, path: w.place_path_help, select: w.sel_help }[p.how] || w.place_help;
  }
}

function spacingOf(group) {
  return mv.place.spacing[group] ?? SPACING[group] ?? 10;
}

function setPlaceMode(on) {
  mv.place.on = on;
  if (on) { toMode("map"); dock.check = false; stopRoad(); stopBridge(); }
  if (on && scen.tool) { scen.tool = null; scen.selected = null; renderScenTools(); drawScenario(); }
  if (!on) { dropPlaceGesture(); showPlaceGhost(null); }
  if (on && mv.brush.on) setBrushMode(false);
  pointerMode();
  if (on) placeNote(!mv.place.mod ? mv.words.no_mod : !mv.place.type ? whyNoType() : "", "error");
  if (!on) $("map-help").textContent = mv.brush.on ? mv.words.brush_help : mv.words.map_help;
  renderPlace();
  renderDock();
  drawSelection();  // Select's rings show only while the place tools are open
}

// Nothing to place yet: the map's types are still being read (a second or two on a real map), or the kind picked has
// none, or the search left none.
function whyNoType() {
  return mv.scenery.data ? mv.words.place_pick : mv.words.scenery_loading;
}

// The objects this mod places, on the ground as it is now: each with its real model once the models are in (until
// then, or for a type without one, a gold shape), and a gold dot that marks it at any zoom, so what was placed shows
// even from far away (the owner, 2026-10-15: placing buildings "seemed not to work", and that it showed only an
// orange or yellow square: a building was a 4 m gold box, two pixels at a normal zoom).
const PLACED_DOT = 9;  // pixels across, at any zoom
function drawPlaced() {
  const gl = mv.gl, p = mv.place, lib = mv.scenery.lib;
  if (!gl) return;
  for (const list of Object.values(p.meshes)) for (const m of list) forget(m);
  p.meshes = {};
  const bridges = bridgeTypes();  // drawn as decks (drawBridges)
  // what the mod placed (where a drag is carrying the picked ones), and the map's own it moved (Select)
  const dragging = sel.drag && sel.drag.moved ? new Map(sel.items.filter((it) => it.kind === "placed")
    .map((it) => [it.obj, shownPose(it)])) : null;
  const shown = (dragging ? p.objects.map((o) => (dragging.has(o) ? { ...o, ...dragging.get(o) } : o)) : p.objects)
    .concat(ownMovedObjects());
  if (mv.edit && shown.length) {
    const lists = new Map();  // a type with a model, or a group's shape: its objects
    for (const o of shown) {
      if (bridges.has(o.type)) continue;
      const group = groupOfType(o.type), t = typeNumber(o.type), model = lib && t !== null && lib.has(t);
      const key = model ? t : group;
      (lists.get(key) || lists.set(key, { group, t: model ? t : null, list: [] }).get(key)).list.push(o);
    }
    const { THREE } = gl, grid = makeGrid(mv.edit), m = new THREE.Matrix4(), q = new THREE.Quaternion();
    const at = new THREE.Vector3(), s = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0), dots = {};
    for (const { group, t, list } of lists.values()) {
      const [shape, width, height] = SCENERY_LOOK[group];
      let meshes;
      if (t !== null) {
        meshes = lib.parts(t).map((part) => new THREE.InstancedMesh(part.geo, lib.material(group, part), list.length));
      } else {
        const geo = shape === "cone" ? new THREE.ConeGeometry(0.5, 1, 6) : new THREE.BoxGeometry(1, 1, 1);
        geo.translate(0, 0.5, 0);
        meshes = [new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: PLACED_COLOUR }), list.length)];
      }
      list.forEach((o, k) => {
        const z = groundAt(grid, o.x, o.y);
        at.set(o.x * SCALE, z * SCALE, o.y * SCALE);
        q.setFromAxisAngle(up, -o.turn * Math.PI / 180);
        if (t !== null) s.set(o.size * SCALE, o.size * SCALE, o.size * SCALE);  // a model is in map units already
        else s.set(width * o.size * SCALE, height * o.size * SCALE, width * o.size * SCALE);
        m.compose(at, q, s);
        for (const mesh of meshes) mesh.setMatrixAt(k, m);
        (dots[group] ||= []).push(o.x * SCALE, (z + 150) * SCALE, o.y * SCALE);
      });
      for (const mesh of meshes) {
        mesh.instanceMatrix.needsUpdate = true;
        mesh.computeBoundingSphere();
        gl.scene.add(mesh);
      }
      (p.meshes[group] ||= []).push(...meshes);
    }
    for (const [group, xyz] of Object.entries(dots)) {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(xyz), 3));
      const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color: PLACED_COLOUR, size: PLACED_DOT,
        sizeAttenuation: false }));
      pts.frustumCulled = false;
      gl.scene.add(pts);
      p.meshes[group].push(pts);
    }
  }
  drawBridges();  // (draws the view)
}

// The picked type at the pointer before a click places it (One, and a Line's or a Grid's start): its real model, see-
// through, turned and sized as it will stand (beside a road, with Face the roads); a gold shape until the models are
// in. The owner, 2026-10-15: "how do I know what they look like?" A line or a grid under way shows its preview instead.
const GHOST_ALPHA = 0.6;
function showPlaceGhost(hit) {
  const gl = mv.gl, p = mv.place, lib = mv.scenery.lib;
  if (!gl) return;
  const first = p.how === "one" || ((p.how === "line" || p.how === "grid") && !p.lineStart) || (p.how === "path" && !p.path);
  const type = hit && p.on && first && p.type && mv.edit ? p.type : null;
  if (!type) {
    if (gl.ghost && gl.ghost.visible) { gl.ghost.visible = false; gl.draw(); }
    return;
  }
  const { THREE } = gl, t = typeNumber(type), group = groupOfType(type), model = Boolean(lib && t !== null && lib.has(t));
  const key = `${type}|${model}`;
  if (!gl.ghost || gl.ghost.userData.key !== key) {
    if (gl.ghost) {
      gl.scene.remove(gl.ghost);
      gl.ghost.traverse((o) => { if (o.isMesh) { o.material.dispose(); if (!o.geometry.userData.keep) o.geometry.dispose(); } });
    }
    const ghost = new THREE.Group(), [shape, width, height] = SCENERY_LOOK[group];
    if (model) {
      for (const part of lib.parts(t)) ghost.add(new THREE.Mesh(part.geo, ghostLook(lib.material(group, part))));
    } else {
      const geo = shape === "cone" ? new THREE.ConeGeometry(0.5, 1, 6) : new THREE.BoxGeometry(1, 1, 1);
      geo.translate(0, 0.5, 0);
      geo.scale(width, height, width);
      ghost.add(new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: PLACED_COLOUR, transparent: true,
        opacity: GHOST_ALPHA, depthWrite: false })));
    }
    ghost.userData.key = key;
    for (const o of ghost.children) o.renderOrder = 9;
    gl.ghost = ghost;
    gl.scene.add(ghost);
  }
  const ghost = gl.ghost, k = p.size * SCALE, pose = placePose(hit.x / SCALE, hit.z / SCALE);
  const y = pose.x === hit.x / SCALE && pose.y === hit.z / SCALE ? hit.y : groundAt(makeGrid(mv.edit), pose.x, pose.y) * SCALE;
  ghost.position.set(pose.x * SCALE, y, pose.y * SCALE);
  ghost.rotation.set(0, -pose.turn * Math.PI / 180, 0);
  ghost.scale.set(k, k, k);
  ghost.visible = true;
  gl.draw();
}

async function loadPlaced(pack, ask) {
  const res = await mv.api.scenery(pack);
  if (ask !== mv.ask) return;
  mv.place.objects = res.objects;
  mv.place.groups = [];
  dropPlaceGesture();
  mv.place.lastPath = null;
  mv.place.mod = res.mod;
  forgetSel(res.own || []);  // the map's own objects this mod moves or takes away ([[own]]): Select's, not drawn
  if (sel.own.length && mv.edit && Object.keys(mv.scenery.meshes).length) placeScenery();  // where they were
  drawSelection();
  mv.brush.erase = res.erase || [];  // the Erase brush's circles: the same file's [[erase]] tables
  mv.brush.eraseGroups = [];
  refreshErased();
  showCount();
  countTakes(pack);
  placeNote("");
  drawPlaced();
  renderPlace();
  renderBridgeTray();
  renderCheck();
  if (res.objects.length || bridge.on) loadBridges(pack);  // which of them are bridges, to draw their decks
}

// A click that places nothing always says why: no mod, nothing picked, or the click missed the ground (the sky, or
// the map's edge seen from the side).
async function placeAt(ev) {
  const p = mv.place, pack = mv.current, w = mv.words;
  if (!p.mod) { placeNote(w.no_mod, "error"); return; }
  if (!p.type) { placeNote(whyNoType(), "error"); return; }
  const hit = hitGround(ev);
  if (!hit) { placeNote(w.place_ground, "error"); return; }
  const pose = placePose(hit.x / SCALE, hit.z / SCALE);  // beside a road, facing it (Face the roads)
  const obj = { type: p.type, x: Math.round(pose.x), y: Math.round(pose.y), turn: pose.turn, size: p.size, solid: p.solid };
  p.objects.push(obj);
  drawPlaced();
  try {
    await mv.api.scenery_add(pack, [obj]);
    if (pack !== mv.current) return;
    p.groups.push([obj]);
    redo.place = [];
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
    redo.place = [];
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
// (their turn, and a tree's size) so a painted wood doesn't look stamped; buildings keep the turn they're given, and so
// does anything set beside a road (`keep`: a fence or a wall along it).
function objectAt(x, y, turn, keep = false) {
  const p = mv.place, varied = p.group !== "building" && !keep;
  const size = p.group === "vegetation" ? Math.round(p.size * (0.85 + placeRand() * 0.3) * 100) / 100 : p.size;
  return { type: p.type, x: Math.round(x), y: Math.round(y), turn: varied ? Math.floor(placeRand() * 360) : turn, size,
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
// face the same way, like houses along a street; the turn slider adds to that). Started near a road with Face the
// roads, it follows the road instead (rowOf).
function lineOf(a, b) {
  return withSeed(() => {
    const row = rowOf(a, b);
    return row.map((q) => objectAt(q.x, q.y, q.turn, row.road));
  });
}

// --- Grid, Box and Face the roads (the owner, 2026-10-16: "buildings snap to roads", a Cities: Skylines drag-out grid,
// "length, then rows, spacing", and "fill a box with a building type at a spacing"). A grid is a line (its first row)
// and rows moved out from it; a box is dragged on the ground and filled in rows. Both show what they'll place, see-
// through, with how many, until the click (or the button let go) places it, and both go back with one Undo. ---
const ROWS = { building: 25, prop: 8, vegetation: 6 };  // metres between a grid's or a box's rows to start with, per kind
const ROAD_REACH = 40;  // metres: with Face the roads, an object clicked this near a road's line goes beside the road
const ROW_STEP = 2;     // metres: a row along a road is found by following it in steps this long
const roadHalf = () => ROAD_WIDTH / 2 + 2 * METRE;  // a road's line to the side of what stands beside it (map units)
const facesRoads = () => mv.place.roads && mv.place.group !== "vegetation";  // (trees don't face anything)
const newSeed = () => Math.floor(Math.random() * 2 ** 32);

function rowsOf(group) {
  return mv.place.rows[group] ?? ROWS[group] ?? 10;
}

// make() with the dice of the gesture being made (mulberry32 from mv.place.seed): every preview of a line, a grid or a
// box comes out the same, and the click places just that.
function withSeed(make) {
  let s = mv.place.seed >>> 0;
  const keep = placeRand;
  placeRand = () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  try { return make(); } finally { placeRand = keep; }
}

// The roads as short straight pieces (the map's own Béziers about 10 m a piece, and the mod's new roads point to
// point), in squares of 100 m to find the nearest quickly; made again when the map or the mod's roads change.
let roadIndex = null;
function roadPieces() {
  const P = roads.pieces || [], mine = road.mine || [];
  if (roadIndex && roadIndex.P === P && roadIndex.mine === mine && roadIndex.n === mine.length) return roadIndex;
  const cell = 100 * METRE, cells = new Map(), seg = [];
  const add = (ax, ay, bx, by) => {
    const k = seg.length / 4;
    seg.push(ax, ay, bx, by);
    for (let i = Math.floor(Math.min(ax, bx) / cell); i <= Math.floor(Math.max(ax, bx) / cell); i++) {
      for (let j = Math.floor(Math.min(ay, by) / cell); j <= Math.floor(Math.max(ay, by) / cell); j++) {
        (cells.get(`${i},${j}`) || cells.set(`${i},${j}`, []).get(`${i},${j}`)).push(k);
      }
    }
  };
  for (let o = 0; o < P.length; o += 8) {
    const len = Math.hypot(P[o + 2] - P[o], P[o + 3] - P[o + 1]) + Math.hypot(P[o + 4] - P[o + 2], P[o + 5] - P[o + 3])
      + Math.hypot(P[o + 6] - P[o + 4], P[o + 7] - P[o + 5]);
    const n = Math.min(64, Math.max(2, Math.ceil(len / (10 * METRE))));
    let px = P[o], py = P[o + 1];
    for (let s = 1; s <= n; s++) {
      const t = s / n, u = 1 - t, a = u * u * u, b = 3 * u * u * t, c = 3 * u * t * t, d = t * t * t;
      const x = a * P[o] + b * P[o + 2] + c * P[o + 4] + d * P[o + 6], y = a * P[o + 1] + b * P[o + 3] + c * P[o + 5] + d * P[o + 7];
      add(px, py, x, y);
      px = x; py = y;
    }
  }
  for (const r of mine) for (let i = 0; i + 1 < r.points.length; i++) add(...r.points[i], ...r.points[i + 1]);
  return (roadIndex = { P, mine, n: mine.length, cell, cells, seg });
}

// The nearest point of a road's line to (x, y) within `reach` map units, and the road's way there (a unit vector):
// { x, y, tx, ty, d }, or null.
function nearestRoad(x, y, reach) {
  const I = roadPieces(), c = I.cell, span = Math.ceil(reach / c), cx = Math.floor(x / c), cy = Math.floor(y / c);
  const seen = new Set(), S = I.seg;
  let best = reach * reach, out = null;
  for (let i = cx - span; i <= cx + span; i++) for (let j = cy - span; j <= cy + span; j++) {
    for (const k of I.cells.get(`${i},${j}`) || []) {
      if (seen.has(k)) continue;
      seen.add(k);
      const ax = S[4 * k], ay = S[4 * k + 1], ex = S[4 * k + 2] - ax, ey = S[4 * k + 3] - ay, l2 = ex * ex + ey * ey;
      if (l2 <= 1e-9) continue;
      const t = Math.max(0, Math.min(1, ((x - ax) * ex + (y - ay) * ey) / l2)), px = ax + t * ex, py = ay + t * ey;
      const d2 = (x - px) ** 2 + (y - py) ** 2;
      if (d2 < best) { const l = Math.sqrt(l2); best = d2; out = { x: px, y: py, tx: ex / l, ty: ey / l, d: Math.sqrt(d2) }; }
    }
  }
  return out;
}

// Half the depth of what's being placed (map units, across a row: its model's z), from its model; else its kind's shape
function halfDepth() {
  const p = mv.place, lib = mv.scenery.lib, t = typeNumber(p.type);
  let d = 0;
  if (lib && t !== null && lib.has(t)) {
    for (const part of lib.parts(t)) {
      const b = part.geo.boundingBox;
      if (b) d = Math.max(d, Math.abs(b.min.z), Math.abs(b.max.z));
    }
  }
  return (d || SCENERY_LOOK[groupOfType(p.type)][1] / 2) * p.size;
}

// Where an object at (x, y) stands with Face the roads: beside the nearest road within `reach`, on the side (x, y) is
// on (or `side`, 1 left of the road's way `along`, -1 right), its back to the road, so a row on each side of a street
// faces the street; the turn slider adds to that (a model that faces the other way: 180°). { x, y, turn, back, side,
// along }, or null with no road that near.
function besideRoad(x, y, reach, side = 0, along = null) {
  const r = nearestRoad(x, y, reach);
  if (!r) return null;
  let tx = r.tx, ty = r.ty;
  if (along && tx * along[0] + ty * along[1] < 0) { tx = -tx; ty = -ty; }  // the road's pieces run either way
  const nx = -ty, ny = tx, s = side || ((x - r.x) * nx + (y - r.y) * ny >= 0 ? 1 : -1), off = roadHalf() + halfDepth();
  const heading = Math.atan2(ty, tx) * 180 / Math.PI + (s > 0 ? 0 : 180);
  return { x: r.x + nx * s * off, y: r.y + ny * s * off, turn: Math.round(heading + mv.place.turn + 720) % 360,
    back: [nx * s, ny * s], side: s, along: [tx, ty] };
}

// Where a click at (x, y) puts the next object: beside a road (Face the roads), else where it was clicked
function placePose(x, y) {
  const q = facesRoads() && besideRoad(x, y, ROAD_REACH * METRE);
  return q || { x, y, turn: mv.place.turn };
}

// A row from a to b: each spot and turn ({ x, y, turn, back }). Along a road (a starts within ROAD_REACH of one, with
// Face the roads): the road is followed from beside a to beside b, ROW_STEP at a time, an object every spacing along
// it, each facing it; the row stops where the road leaves a's line by more than twice ROAD_REACH (`road` set on the
// list). Else straight, both ends included.
function rowOf(a, b) {
  const p = mv.place, gap = spacingOf(p.group) * METRE, len = Math.hypot(b.x - a.x, b.y - a.y);
  const first = facesRoads() && besideRoad(a.x, a.y, ROAD_REACH * METRE);
  if (first) {
    const out = [first], steps = Math.min(20000, Math.ceil(len / (ROW_STEP * METRE)));
    let last = first, run = 0;
    for (let k = 1; k <= steps && out.length < MOST; k++) {
      const t = k / steps, q = besideRoad(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, 2 * ROAD_REACH * METRE,
        first.side, last.along);
      if (!q) break;
      run += Math.hypot(q.x - last.x, q.y - last.y);
      last = q;
      if (run >= gap) { out.push(q); run = 0; }
    }
    out.road = true;
    return out;
  }
  const n = Math.min(MOST, Math.max(1, Math.floor(len / gap) + 1));
  const heading = (Math.atan2(b.y - a.y, b.x - a.x) * 180 / Math.PI + 360) % 360, turn = Math.round(heading + p.turn) % 360;
  const out = [];
  for (let k = 0; k < n; k++) {
    const t = n === 1 ? 0 : k / (n - 1);
    out.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, turn });
  }
  return out;
}

// A grid: the row from a to b, and rows behind it out to `pt` (the pointer; none yet: the first row alone), rows apart.
// A row along a road gets its rows behind it (away from the road); a straight one on the pointer's side. With Face the
// roads, a spot on a road is left out (the first row along a road stands beside it already). `per` and `rows` are set
// on the list.
function gridOf(a, b, pt) {
  return withSeed(() => {
    const p = mv.place, row = rowOf(a, b), gap = rowsOf(p.group) * METRE, out = [];
    let rows = 1, backs;
    if (row.road) {
      backs = row.map((q) => q.back);
      if (pt) {
        let q = row[0], best = Infinity;
        for (const r of row) { const d = (r.x - pt.x) ** 2 + (r.y - pt.y) ** 2; if (d < best) { best = d; q = r; } }
        rows = 1 + Math.floor(Math.max(0, (pt.x - q.x) * q.back[0] + (pt.y - q.y) * q.back[1]) / gap);
      }
    } else {
      const len = Math.hypot(b.x - a.x, b.y - a.y) || 1, nx = -(b.y - a.y) / len, ny = (b.x - a.x) / len;
      const d = pt ? (pt.x - a.x) * nx + (pt.y - a.y) * ny : 0, s = d < 0 ? -1 : 1;
      rows = 1 + Math.floor(Math.abs(d) / gap);
      backs = row.map(() => [nx * s, ny * s]);
    }
    const avoid = facesRoads(), clear = roadHalf() + halfDepth() * 0.8, [x0, y0, , x1, y1] = mv.edit.bounds;
    for (let r = 0; r < rows && out.length < MOST; r++) {
      for (let i = 0; i < row.length && out.length < MOST; i++) {
        const x = row[i].x + backs[i][0] * gap * r, y = row[i].y + backs[i][1] * gap * r;
        if (x < x0 || x > x1 || y < y0 || y > y1) continue;
        if (avoid && (r > 0 || !row.road) && nearestRoad(x, y, clear)) continue;
        out.push(objectAt(x, y, row[i].turn, row.road));
      }
    }
    return Object.assign(out, { per: row.length, rows });
  });
}

// A box from corner a to corner b (the map's own axes): filled in rows, spacing apart along a row and rows apart, the
// rows centred in it, each turned by the turn slider (trees and props varied as in an area). With Face the roads, a
// spot on a road is left out. `cols`, `rows`, `w` and `h` (metres) are set on the list.
function fillBox(a, b) {
  return withSeed(() => {
    const p = mv.place, gx = spacingOf(p.group) * METRE, gy = rowsOf(p.group) * METRE, out = [];
    const bx0 = Math.min(a.x, b.x), bx1 = Math.max(a.x, b.x), by0 = Math.min(a.y, b.y), by1 = Math.max(a.y, b.y);
    const cols = Math.floor((bx1 - bx0) / gx) + 1, rows = Math.floor((by1 - by0) / gy) + 1;
    const ox = bx0 + (bx1 - bx0 - (cols - 1) * gx) / 2, oy = by0 + (by1 - by0 - (rows - 1) * gy) / 2;
    const avoid = facesRoads(), clear = roadHalf() + halfDepth() * 0.8, [x0, y0, , x1, y1] = mv.edit.bounds;
    for (let j = 0; j < rows && out.length < MOST; j++) {
      for (let i = 0; i < cols && out.length < MOST; i++) {
        const x = ox + i * gx, y = oy + j * gy;
        if (x < x0 || x > x1 || y < y0 || y > y1) continue;
        if (avoid && nearestRoad(x, y, clear)) continue;
        out.push(objectAt(x, y, p.turn));
      }
    }
    return Object.assign(out, { cols, rows, w: Math.round((bx1 - bx0) / METRE), h: Math.round((by1 - by0) / METRE) });
  });
}

// What a line, a grid or a box being made will place, at the pointer `hit` (none: nothing shown), with how many in
// the note.
function placePreview(hit) {
  const p = mv.place, w = mv.words, pt = hit && { x: hit.x / SCALE, y: hit.z / SCALE };
  let objs = null, note = "";
  if (pt && p.on && p.type && mv.edit) {
    if (p.how === "line" && p.lineStart) {
      objs = lineOf(p.lineStart, pt);
      note = fill(w.place_line_count, { n: objs.length.toLocaleString(),
        m: Math.round(Math.hypot(pt.x - p.lineStart.x, pt.y - p.lineStart.y) / METRE) });
    } else if (p.how === "grid" && p.lineStart) {
      objs = p.grid ? gridOf(p.lineStart, p.grid.b, pt) : gridOf(p.lineStart, pt, null);
      note = fill(w.place_grid_count, { n: objs.length.toLocaleString(), per: objs.per, rows: objs.rows });
    } else if (p.how === "box" && p.box) {
      p.box.b = pt;
      objs = fillBox(p.box.a, pt);
      note = fill(w.place_box_count, { n: objs.length.toLocaleString(), cols: objs.cols, rows: objs.rows, w: objs.w, h: objs.h });
    } else if (p.how === "path" && p.path) {
      objs = pathOf(p.path.pts.concat([[pt.x, pt.y]]));
      note = fill(w.place_line_count, { n: objs.length.toLocaleString(), m: objs.m });
    }
  }
  showPathLine(objs && objs.path);
  showPlacePreview(objs);
  showPlaceBox(p.how === "box" ? p.box : null);
  if (note) placeNote(note + (objs.length >= MOST ? " " + w.place_most : ""));
}

// A line, a path, a grid or a box half made is dropped: by Esc, another way or kind picked, the tools closed, another
// map
function dropPlaceGesture() {
  const p = mv.place;
  p.lineStart = null;
  p.grid = null;
  p.box = null;
  p.path = null;
  showPlaceGuide(null);
  showPlacePreview(null);
  showPlaceBox(null);
  showPathLine(null);
}

// --- Path: rows of hedges and forests (the owner, 2026-10-16: "I would like to be able to have rows of hedges and
// forests"). Clicked along the way (a double-click, Enter or Finish ends it): a smooth line through the clicks, as a
// Freeform road's (roadLine), with an object every spacing along it, turned along it; with a Width, a belt of them
// at least the spacing apart (a tree belt, a wood's edge); a path of trees with Cover hides units as the Forest
// brush's woods do (cover strokes along it, saved with the trees: the place tray's Undo takes both). "Along the last
// path" lays the picked object along the last path again: a hedge's bushes, then its trees. ---
const COVER_HALF = 10;   // metres: the least a path's cover reaches either side of its line (the cover grid is coarse)
const COVER_STEP = 40;   // metres of path per cover stroke (a line-shaped Cover stroke each)

function widthOf(group) {
  return mv.place.width[group] ?? 0;
}

const pathCovers = () => mv.place.group === "vegetation" && mv.place.cover;

// The smooth line through a path's clicks ([x, y] each), its points ~ROAD_SAMPLE apart, and the distance to each
function pathLine(pts) {
  const line = roadLine("free", pts), cum = [0];
  for (let i = 1; i < line.length; i++) cum.push(cum[i - 1] + Math.hypot(line[i][0] - line[i - 1][0], line[i][1] - line[i - 1][1]));
  return { line, cum, len: cum[cum.length - 1] };
}

// The spot `d` along a path line and its way there: [x, y, ux, uy]
function alongPath({ line, cum }, d) {
  let lo = 0, hi = cum.length - 1;
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (cum[mid] <= d) lo = mid; else hi = mid; }
  const seg = cum[hi] - cum[lo] || 1, t = Math.max(0, Math.min(1, (d - cum[lo]) / seg));
  const [ax, ay] = line[lo], [bx, by] = line[hi];
  return [ax + (bx - ax) * t, ay + (by - ay) * t, (bx - ax) / seg, (by - ay) / seg];
}

// What a path through `pts` places: one line of objects every spacing (both ends included), or with a Width at least
// the spacing, a belt of them scattered along it no closer than the spacing (to each other and to what the mod
// placed before, as an area). `m` (metres long) and `path` (pathLine) are set on the list.
function pathOf(pts) {
  return withSeed(() => {
    const p = mv.place, path = pathLine(pts), gap = spacingOf(p.group) * METRE, wide = widthOf(p.group) * METRE;
    const out = [], heading = (ux, uy) => Math.round(Math.atan2(uy, ux) * 180 / Math.PI + p.turn + 720) % 360;
    if (pts.length >= 2 && path.len > 0) {
      if (wide < gap) {
        const n = Math.min(MOST, Math.floor(path.len / gap) + 1);
        for (let k = 0; k < n; k++) {
          const [x, y, ux, uy] = alongPath(path, n === 1 ? 0 : k * path.len / (n - 1));
          out.push(objectAt(x, y, heading(ux, uy)));
        }
      } else {
        const key = (a, b) => `${Math.floor(a / gap)},${Math.floor(b / gap)}`, grid = new Map();
        const put = (o) => (grid.get(key(o.x, o.y)) || grid.set(key(o.x, o.y), []).get(key(o.x, o.y))).push(o);
        for (const o of p.objects) put(o);
        const free = (a, b) => {
          const cx = Math.floor(a / gap), cy = Math.floor(b / gap);
          for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) {
            for (const o of grid.get(`${cx + i},${cy + j}`) || []) if (Math.hypot(o.x - a, o.y - b) < gap) return false;
          }
          return true;
        };
        const [x0, y0, , x1, y1] = mv.edit.bounds, tries = Math.ceil(path.len * wide / (gap * gap) * 3);
        for (let t = 0; t < tries && out.length < MOST; t++) {
          const [x, y, ux, uy] = alongPath(path, placeRand() * path.len), off = (placeRand() - 0.5) * wide;
          const ox = x - uy * off, oy = y + ux * off;
          if (ox < x0 || ox > x1 || oy < y0 || oy > y1 || !free(ox, oy)) continue;
          const o = objectAt(ox, oy, heading(ux, uy));
          out.push(o);
          put(o);
        }
      }
    }
    return Object.assign(out, { m: Math.round(path.len / METRE), path });
  });
}

// The cover a path of trees gives: line-shaped Cover strokes along it, COVER_STEP apart, reaching half its width
// either side (COVER_HALF at least), as the Forest brush gives its woods cover
function pathCover(path) {
  const r = Math.round(Math.max(widthOf(mv.place.group) * METRE / 2, COVER_HALF * METRE)), out = [];
  const n = Math.max(1, Math.ceil(path.len / (COVER_STEP * METRE)));
  let [ax, ay] = alongPath(path, 0);
  for (let k = 1; k <= n; k++) {
    const [bx, by] = alongPath(path, k * path.len / n);
    out.push({ brush: "cover", x: Math.round(ax), y: Math.round(ay), radius: r, shape: "line", x2: Math.round(bx),
      y2: Math.round(by) });
    [ax, ay] = [bx, by];
  }
  return out;
}

// A path being clicked ends: placed (with its cover, for trees with Cover), and kept for "Along the last path"
async function finishPath() {
  const p = mv.place, pts = p.path ? p.path.pts : [];
  if (pts.length < 2 || !p.type) return;
  const objs = pathOf(pts);
  p.lastPath = pts;
  dropPlaceGesture();
  await placePath(objs);
}

// "Along the last path": the picked object, at its spacing and width, along the last path placed
async function placeAgain() {
  const p = mv.place;
  if (!p.lastPath || !p.type || !p.mod) return;
  p.seed = newSeed();
  await placePath(pathOf(p.lastPath));
}

async function placePath(objs) {
  if (pathCovers() && objs.length) await placeCovered(objs, pathCover(objs.path));
  else await placeMany(objs);
}

// Trees and their cover in one go: the trees saved, then the cover strokes (both or neither); one place group, which
// the place tray's Undo takes back with its cover (the cover is also the brushes' last group, `cover`).
async function placeCovered(objs, strokes) {
  const p = mv.place, b = mv.brush, pack = mv.current, w = mv.words;
  p.objects.push(...objs);
  drawPlaced();
  let placed = false;
  try {
    await mv.api.scenery_add(pack, objs);
    placed = true;
    await mv.api.terrain_add(pack, strokes);
    if (pack !== mv.current) return;
    addCover(objs, strokes);
    p.groups.push(objs);
    redo.place = [];
    placeNote(fill(w.place_placed_cover, { n: objs.length.toLocaleString() }) + (objs.length >= MOST ? " " + w.place_most : ""));
  } catch (err) {
    if (placed) { try { await mv.api.scenery_undo(pack, objs.length, objs); } catch (_) { /* said below */ } }
    if (pack !== mv.current) return;
    p.objects.splice(p.objects.length - objs.length, objs.length);
    drawPlaced();
    placeNote((err && err.message) || String(err), "error");
  }
  renderPlace();
}

// A path's cover strokes, saved: on the view and on the brushes' list, as the group `objs.cover`
function addCover(objs, strokes) {
  const b = mv.brush;
  b.strokes.push(...strokes);
  for (const s of strokes) applyStroke(mv.edit, s);
  objs.cover = { n: strokes.length };
  objs.strokes = strokes;
  b.groups.push(objs.cover);
  redo.brush = [];
  showCount();
  if (mv.gl) mv.gl.draw();
}

// Undo of a path with cover: its cover goes too while it's still the brushes' last group; after other brush strokes
// it stays (and Redo won't lay it twice), and the note says so.
async function undoCover(group) {
  const b = mv.brush, pack = mv.current;
  if (b.groups[b.groups.length - 1] !== group.cover) {
    group.coverLeft = true;
    placeNote(mv.words.place_cover_left, "error");
    return;
  }
  const res = await mv.api.terrain_undo(pack, group.cover.n);
  if (pack !== mv.current) return;
  b.groups.pop();
  b.strokes.splice(b.strokes.length - res.removed, res.removed);
  reapply();
  showCount();
}

// The path being clicked, drawn over the ground (none: hidden)
function showPathLine(path) {
  const gl = mv.gl;
  if (!gl) return;
  if (!path || path.line.length < 2 || !mv.edit) {
    if (gl.pathLine && gl.pathLine.visible) { gl.pathLine.visible = false; gl.draw(); }
    return;
  }
  const { THREE } = gl, grid = makeGrid(mv.edit), pos = new Float32Array(path.line.length * 3);
  path.line.forEach(([x, y], k) => pos.set([x * SCALE, (groundAt(grid, x, y) + ROAD_LIFT) * SCALE, y * SCALE], 3 * k));
  if (!gl.pathLine) {
    gl.pathLine = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: PLACED_COLOUR, depthTest: false }));
    gl.pathLine.renderOrder = 10;
    gl.pathLine.frustumCulled = false;
    gl.scene.add(gl.pathLine);
  }
  gl.pathLine.geometry.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  gl.pathLine.visible = true;
  gl.draw();
}

// A model's material see-through, as the picked type shows at the pointer (showPlaceGhost) and in a preview
function ghostLook(mat) {
  if (mat.alphaTest || !mat.map) {  // (a picture whose alpha isn't see-through would come out patchy: it stays solid)
    Object.assign(mat, { transparent: true, opacity: GHOST_ALPHA, depthWrite: false });
    mat.alphaTest *= GHOST_ALPHA;  // the leaves' cut-out at the faded opacity (as fade does)
  }
  return mat;
}

// The objects a line, a grid or a box will place, see-through (their real model once the models are in, else gold
// shapes), MOST at most, made once per type.
function showPlacePreview(objs) {
  const gl = mv.gl, p = mv.place, lib = mv.scenery.lib;
  if (!gl) return;
  if (!objs || !objs.length || !mv.edit || !p.type) {
    if (gl.preview && gl.preview.visible) { gl.preview.visible = false; gl.draw(); }
    return;
  }
  const { THREE } = gl, t = typeNumber(p.type), group = groupOfType(p.type), model = Boolean(lib && t !== null && lib.has(t));
  const key = `${p.type}|${model}`, [shape, width, height] = SCENERY_LOOK[group];
  if (!gl.preview || gl.preview.userData.key !== key) {
    if (gl.preview) {
      gl.scene.remove(gl.preview);
      for (const o of gl.preview.children) {
        o.material.dispose();
        if (!o.userData.model) o.geometry.dispose();
        if (o.dispose) o.dispose();
      }
    }
    const g = new THREE.Group();
    if (model) {
      for (const part of lib.parts(t)) {
        const mesh = new THREE.InstancedMesh(part.geo, ghostLook(lib.material(group, part)), MOST);
        mesh.userData.model = true;
        g.add(mesh);
      }
    } else {
      const geo = shape === "cone" ? new THREE.ConeGeometry(0.5, 1, 6) : new THREE.BoxGeometry(1, 1, 1);
      geo.translate(0, 0.5, 0);
      g.add(new THREE.InstancedMesh(geo, new THREE.MeshLambertMaterial({ color: PLACED_COLOUR, transparent: true,
        opacity: GHOST_ALPHA, depthWrite: false }), MOST));
    }
    for (const o of g.children) { o.renderOrder = 9; o.frustumCulled = false; }
    g.userData.key = key;
    gl.preview = g;
    gl.scene.add(g);
  }
  const grid = makeGrid(mv.edit), m = new THREE.Matrix4(), q = new THREE.Quaternion(), at = new THREE.Vector3();
  const s = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0), n = Math.min(objs.length, MOST);
  for (const mesh of gl.preview.children) {
    for (let k = 0; k < n; k++) {
      const o = objs[k];
      at.set(o.x * SCALE, groundAt(grid, o.x, o.y) * SCALE, o.y * SCALE);
      q.setFromAxisAngle(up, -o.turn * Math.PI / 180);
      if (model) s.set(o.size * SCALE, o.size * SCALE, o.size * SCALE);
      else s.set(width * o.size * SCALE, height * o.size * SCALE, width * o.size * SCALE);
      mesh.setMatrixAt(k, m.compose(at, q, s));
    }
    mesh.count = n;
    mesh.instanceMatrix.needsUpdate = true;
  }
  gl.preview.visible = true;
  gl.draw();
}

// A box being dragged: its edges, drawn over the ground (none: hidden)
function showPlaceBox(box) {
  const gl = mv.gl;
  if (!gl) return;
  if (!box || !box.b || !mv.edit) {
    if (gl.placeBox && gl.placeBox.visible) { gl.placeBox.visible = false; gl.draw(); }
    return;
  }
  const { THREE } = gl;
  if (!gl.placeBox) {
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(new Float32Array(12), 3));
    gl.placeBox = new THREE.LineLoop(geo, new THREE.LineBasicMaterial({ color: PLACED_COLOUR, depthTest: false }));
    gl.placeBox.renderOrder = 10;
    gl.placeBox.frustumCulled = false;
    gl.scene.add(gl.placeBox);
  }
  const grid = makeGrid(mv.edit), pos = gl.placeBox.geometry.attributes.position, { a, b } = box;
  [[a.x, a.y], [b.x, a.y], [b.x, b.y], [a.x, b.y]].forEach(([x, y], k) => {
    pos.setXYZ(k, x * SCALE, (groundAt(grid, x, y) + ROAD_LIFT) * SCALE, y * SCALE);
  });
  pos.needsUpdate = true;
  gl.placeBox.visible = true;
  gl.draw();
}

// What the area brush covers, or where a line would go, drawn with the terrain brush's own ring and guide.
function showPlaceGuide(pt) {
  const gl = mv.gl, p = mv.place;
  if (!gl || !gl.ring) return;
  const r = p.area * METRE * SCALE;
  gl.ring.visible = Boolean(pt && p.on && p.how === "area");
  if (gl.ring.visible) { gl.ring.position.set(pt.x, pt.y + r * 0.02, pt.z); gl.ring.scale.set(r, r, r); }
  const start = p.on && (p.how === "line" || (p.how === "grid" && !p.grid)) ? p.lineStart : null;
  const mark = spacingOf(p.group) * METRE * SCALE;
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

// Redo puts back what Undo took, with the same call that saved it the first time. Each tool keeps its own list, as
// its Undo does; a new step in a tool empties that tool's list (what was taken back can't follow a new step), and so
// does Start over and opening another map.
const redo = { place: [], brush: [], erase: [], road: [] };

function forgetRedo() {
  redo.place = [];
  redo.brush = [];
  redo.erase = [];
  redo.road = [];
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
    redo.place.push(group);
    if (group.cover && !group.coverLeft) await undoCover(group);  // a path of trees: its cover too
    renderPlace();
    renderBridgeTray();
  } catch (err) {
    if (!redo.place.includes(group)) p.groups.push(group);  // not taken back: it stays Undo's
    placeNote((err && err.message) || String(err), "error");
  }
}

// Redo in a place tray: the last click, area or line Undo took back, placed again in one go.
async function redoPlace() {
  const p = mv.place, pack = mv.current;
  if (!p.mod || p.painting || !redo.place.length) return;
  const group = redo.place.pop();
  try {
    await mv.api.scenery_add(pack, group);
    if (pack !== mv.current) return;
    p.objects.push(...group);
    p.groups.push(group);
    if (group.cover && !group.coverLeft) {  // a path of trees: its cover laid again
      await mv.api.terrain_add(pack, group.strokes);
      if (pack !== mv.current) return;
      addCover(group, group.strokes);
    }
    drawPlaced();
    renderPlace();
    renderBridgeTray();
  } catch (err) {
    if (pack !== mv.current) return;
    if (!p.groups.includes(group)) redo.place.push(group);  // (placed but its cover not: the objects stay)
    else { group.coverLeft = true; drawPlaced(); renderPlace(); }
    placeNote((err && err.message) || String(err), "error");
  }
}

// Objects taken off the map: out of the list and the view.
function takeOff(objs) {
  const gone = new Set(objs);
  mv.place.objects = mv.place.objects.filter((o) => !gone.has(o));
  drawPlaced();
}

// --- Select, the place trays' fourth way (the owner, 2026-10-16: "select move and delete things already placed,
// including what's on the map"): a click picks what stands nearest, what this mod placed or the map's own
// (StudioApi.map_objects_at); Shift+click adds one or takes it off; a box dragged on the ground picks all in it
// (map_objects_in). Dragging a picked one moves them all, Turn and Size set theirs, Delete (the button or the key)
// takes them away. What the mod placed changes in its own rows (scenery_change); the map's own become [[own]] rows
// (scenery_own: taken away there, placed again where they went). Each step goes back with Undo and forth with Redo.
// An item: { kind: "placed", obj } (one of mv.place.objects) or { kind: "own", orig } (where the map's file has it:
// type, group, x, y, turn, size, lift). ---
const SEL_PICK = 8 * METRE;     // how far from a click an object is picked (8 m; further when zoomed out: SEL_PIXELS)
const SEL_PIXELS = 18;          // ...as far as this many pixels round the click
const SEL_RING = [90, 220, 255];
const sel = { items: [], own: [], undo: [], redo: [], drag: null, box: null, busy: false, origs: new Map() };

// The map's own object as its file has it (type, group, x, y, turn, size, lift), kept by type and place: an [[own]]
// row holds only where it was and where it went, so its first turn and size come from the map (map_objects_at)
const origKey = (o) => `${o.type}|${Math.round(o.x)}|${Math.round(o.y)}`;

function keepOrig(o) {
  sel.origs.set(origKey(o), o);
  return o;
}

async function origOf(row) {
  const kept = sel.origs.get(origKey(row));
  if (kept) return kept;
  const pack = mv.current;
  try {
    const res = await mv.api.map_objects_at(pack, Math.round(row.x), Math.round(row.y), 60);
    const o = res.objects.find((x) => sameOrig(row, x));
    if (o) return keepOrig(o);
  } catch (_) { /* below: as the row has it */ }
  return { type: row.type, group: groupOfType(row.type), x: row.x, y: row.y, turn: row.turn || 0, size: row.size || 1,
    lift: row.lift || 0 };
}

function selecting() {
  return mv.place.on && mv.place.how === "select";
}

function sameOrig(r, o) {
  return r.type === o.type && Math.abs(r.x - o.x) < 1 && Math.abs(r.y - o.y) < 1;
}

function ownRow(orig) {
  return sel.own.find((r) => sameOrig(r, orig)) || null;
}

// Where an item stands now (map units; turn in degrees, as a placed object's), or null when it's taken away
function selPose(it) {
  if (it.kind === "placed") return { x: it.obj.x, y: it.obj.y, turn: it.obj.turn, size: it.obj.size };
  const r = ownRow(it.orig);
  if (r && r.gone) return null;
  return r ? { x: r.to_x, y: r.to_y, turn: r.turn, size: r.size } : { x: it.orig.x, y: it.orig.y, turn: it.orig.turn,
    size: it.orig.size };
}

// ...and while a drag moves the picked ones, where it would put them
function shownPose(it) {
  const p = selPose(it), d = sel.drag;
  return p && d && d.moved && sel.items.includes(it) ? { ...p, x: p.x + d.dx, y: p.y + d.dy } : p;
}

function selType(it) {
  return it.kind === "placed" ? it.obj.type : it.orig.type;
}

// What the game's own editor calls a type, in the Studio's language (the palette's names), else its short name
function typeLabel(type) {
  const r = ((mv.scenery.data && mv.scenery.data.palette) || []).find((x) => x[0] === type);
  if (!r) return type.slice(type.indexOf("/") + 1);
  return (mv.lang !== "base" && r[5] && (r[5][mv.lang] || r[5].us)) || r[1];
}

// The map's own objects drawn somewhere else now: moved ones, and the ones a drag is carrying
function ownMovedObjects() {
  const out = [];
  for (const r of sel.own) if (!r.gone) out.push({ type: r.type, x: r.to_x, y: r.to_y, turn: r.turn, size: r.size, own: r });
  const d = sel.drag;
  if (d && d.moved) {
    for (const it of sel.items) {
      if (it.kind !== "own") continue;
      const p = shownPose(it), r = ownRow(it.orig);
      const at = r ? out.findIndex((o) => o.own === r) : -1;
      const o = { type: it.orig.type, x: p.x, y: p.y, turn: p.turn, size: p.size, own: r || it.orig };
      if (at >= 0) out[at] = o; else out.push(o);
    }
  }
  return out;
}

// The map's own objects not drawn where its file has them (taken away, moved, or carried by a drag): the keys
// placeScenery hides them by (its short name and place, rounded as the view's are)
function ownHidden() {
  const keys = new Set(), add = (o) => {
    const short = o.type.slice(o.type.indexOf("/") + 1), x = Math.round(o.x), y = Math.round(o.y);
    for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) keys.add(`${short}|${x + i}|${y + j}`);
  };
  for (const r of sel.own) add(r);
  if (sel.drag && sel.drag.moved) for (const it of sel.items) if (it.kind === "own") add(it.orig);
  return keys;
}

// A ring on each picked object, the colour of a selection
function drawSelection() {
  const gl = mv.gl;
  if (!gl || !gl.THREE) return;
  const { THREE } = gl, n = sel.items.length;
  if (!gl.selRings || gl.selRings.userData.most < n) {
    if (gl.selRings) forget(gl.selRings);
    const geo = new THREE.RingGeometry(0.8, 1, 32);
    geo.rotateX(-Math.PI / 2);
    const most = Math.max(64, n);
    gl.selRings = new THREE.InstancedMesh(geo, new THREE.MeshBasicMaterial({ color: new THREE.Color().setRGB(
      ...SEL_RING.map((v) => v / 255), THREE.SRGBColorSpace), transparent: true, opacity: 0.95, depthTest: false }), most);
    gl.selRings.userData.most = most;
    gl.selRings.renderOrder = 11;
    gl.selRings.frustumCulled = false;
    gl.scene.add(gl.selRings);
  }
  const rings = gl.selRings, grid = mv.edit ? heightGrid() : null, m = new THREE.Matrix4();
  let k = 0;
  for (const it of sel.items) {
    const p = shownPose(it);
    if (!p || !grid) continue;
    const r = (groupOfType(selType(it)) === "building" ? 1400 : 500) * Math.max(0.5, Math.min(p.size, 4)) * SCALE;
    m.makeScale(r, r, r);
    m.setPosition(p.x * SCALE, (groundAt(grid, p.x, p.y) + 200) * SCALE, p.y * SCALE);
    rings.setMatrixAt(k++, m);
  }
  rings.count = k;
  rings.visible = k > 0 && mv.place.on;
  rings.instanceMatrix.needsUpdate = true;
  gl.draw();
}

function selRedraw() {
  placeScenery();   // the map's own: the ones moved or taken away hidden where they were (and drawPlaced: where they went)
  drawSelection();
  renderPlace();
}

function clearSel() {
  if (!sel.items.length) return;
  sel.items = [];
  drawSelection();
  renderPlace();
}

// Forget the picks and the steps: another map, or the mod's file read again
function forgetSel(own) {
  sel.items = [];
  sel.own = own || [];
  sel.undo = [];
  sel.redo = [];
  sel.drag = null;
  sel.origs = new Map();
}

// What can be picked round (x, y), nearest first: what this mod placed, the map's own moved by it, and the map's own
// where its file has them (unless this mod moved or took them away). `reach` in map units.
async function selCandidates(x, y, reach) {
  const pack = mv.current, out = [];
  const near = (p) => p && Math.hypot(p.x - x, p.y - y) <= reach;
  for (const obj of mv.place.objects) {
    if (bridgeTypes().has(obj.type) || forestTrees.has(obj)) continue;  // bridges and a Forest's trees have their own Undo
    if (near(obj)) out.push({ it: { kind: "placed", obj }, d: Math.hypot(obj.x - x, obj.y - y) });
  }
  for (const r of sel.own) {
    if (r.gone || !near({ x: r.to_x, y: r.to_y })) continue;
    out.push({ it: { kind: "own", orig: await origOf(r) }, d: Math.hypot(r.to_x - x, r.to_y - y) });
  }
  if (!blankMap(pack)) {
    const res = await mv.api.map_objects_at(pack, Math.round(x), Math.round(y), Math.round(reach));
    if (pack !== mv.current) return [];
    for (const o of res.objects) if (!ownRow(o)) out.push({ it: { kind: "own", orig: keepOrig(o) }, d: o.distance });
  }
  return out.sort((a, b) => a.d - b.d).map((c) => c.it);
}

function sameItem(a, b) {
  return a.kind === b.kind && (a.kind === "placed" ? a.obj === b.obj : sameOrig(a.orig, b.orig));
}

// A click: the nearest thing there picked (Shift: added, or taken off when it's already picked)
async function selPickAt(ev, add) {
  const w = mv.words, hit = hitGround(ev);
  if (!hit) { placeNote(w.place_ground, "error"); return; }
  const x = hit.x / SCALE, y = hit.z / SCALE, reach = Math.min(Math.max(SEL_PICK, pixelsAt(hit, SEL_PIXELS)), 26000);
  try {
    const found = await selCandidates(x, y, reach);
    const it = found[0];
    if (!it) { if (!add) clearSel(); placeNote(w.sel_nothing); return; }
    const at = sel.items.findIndex((s) => sameItem(s, it));
    if (add) { if (at >= 0) sel.items.splice(at, 1); else sel.items.push(it); }
    else sel.items = [at >= 0 ? sel.items[at] : it];
    placeNote("");
  } catch (err) { placeNote((err && err.message) || String(err), "error"); }
  drawSelection();
  renderPlace();
}

// A box dragged on the screen: everything inside it picked (x0, y0, x1, y1 in the page's pixels)
async function selPickBox(b) {
  const gl = mv.gl, pack = mv.current, w = mv.words;
  const rect = gl.renderer.domElement.getBoundingClientRect(), v = new gl.THREE.Vector3();
  const [l, r, t, bt] = [Math.min(b.x0, b.x1), Math.max(b.x0, b.x1), Math.min(b.y0, b.y1), Math.max(b.y0, b.y1)];
  const corners = [[l, t], [r, t], [l, bt], [r, bt]].map(([cx, cy]) => hitGround({ clientX: cx, clientY: cy }))
    .filter(Boolean);
  if (corners.length < 4) { placeNote(w.sel_box_ground, "error"); return; }
  const xs = corners.map((p) => p.x / SCALE), ys = corners.map((p) => p.z / SCALE);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const grid = heightGrid();
  const onScreen = (p) => {  // its place on the ground, seen inside the box
    v.set(p.x * SCALE, groundAt(grid, p.x, p.y) * SCALE, p.y * SCALE).project(gl.camera);
    if (v.z > 1) return false;
    const sx = rect.left + (v.x + 1) / 2 * rect.width, sy = rect.top + (1 - v.y) / 2 * rect.height;
    return sx >= l && sx <= r && sy >= t && sy <= bt;
  };
  const got = [];
  for (const obj of mv.place.objects) {
    if (!bridgeTypes().has(obj.type) && !forestTrees.has(obj) && onScreen(obj)) got.push({ kind: "placed", obj });
  }
  let more = false;
  try {
    for (const row of sel.own) {
      if (!row.gone && onScreen({ x: row.to_x, y: row.to_y })) got.push({ kind: "own", orig: await origOf(row) });
    }
    if (!blankMap(pack)) {
      const res = await mv.api.map_objects_in(pack, Math.round(x0), Math.round(y0), Math.round(x1), Math.round(y1));
      if (pack !== mv.current) return;
      for (const o of res.objects) if (!ownRow(o) && onScreen(o)) got.push({ kind: "own", orig: keepOrig(o) });
      more = res.more;
    }
  } catch (err) { placeNote((err && err.message) || String(err), "error"); return; }
  const keep = b.add ? sel.items.slice() : [];
  for (const it of got) if (!keep.some((s) => sameItem(s, it))) keep.push(it);
  sel.items = keep;
  placeNote(more ? w.sel_more : got.length ? "" : w.sel_nothing);
  drawSelection();
  renderPlace();
}

// One step, saved: `placed` [[old, new or null]] for what the mod placed, `own` the [[own]] list before and after.
// forward: as made (and Redo); else back (Undo).
async function selApply(step, forward) {
  const pack = mv.current, p = mv.place;
  const pairs = step.placed.map(([a, b]) => (forward ? [a, b] : [b, a]));
  const adds = pairs.filter(([a]) => a === null).map(([, b]) => b);       // a deleted one put back (Undo of Delete)
  const changes = pairs.filter(([a]) => a !== null);
  if (changes.length) await mv.api.scenery_change(pack, changes);
  if (adds.length) await mv.api.scenery_add(pack, adds);
  const own = forward ? step.after : step.before;
  if (step.after !== step.before) {
    const res = await mv.api.scenery_own(pack, own);
    if (pack !== mv.current) return;
    sel.own = res.own;
  }
  // the view's lists: each object in its row's place, Undo's groups following it
  const swap = new Map(changes.map(([a, b]) => [a, b]));
  const turn = (o) => (swap.has(o) ? swap.get(o) : o);
  p.objects = p.objects.map(turn).filter(Boolean).concat(adds);
  p.groups = p.groups.map((g) => (Array.isArray(g) ? g.map(turn).filter(Boolean) : g)).filter((g) => !Array.isArray(g) || g.length);
  // what was picked when the step was made stays picked, each where it is now (an object taken away, not)
  sel.items = step.picked.map((it) => {
    if (it.kind !== "placed") return it;
    const pair = step.placed.find(([a, b]) => a === it.obj || b === it.obj);
    return pair ? { kind: "placed", obj: forward ? pair[1] : pair[0] } : it;
  }).filter((it) => (it.kind === "placed" ? it.obj && p.objects.includes(it.obj) : selPose(it)));
}

// A change to every picked thing: change(pose) gives its new pose, or null to take it away
async function selChange(change) {
  if (sel.busy || !sel.items.length) return;
  const w = mv.words;
  if (!mv.place.mod) { placeNote(w.no_mod, "error"); return; }
  const placed = [];
  let own = sel.own.slice();
  for (const it of sel.items) {
    const now = selPose(it);
    if (!now) continue;
    const next = change(now);
    if (it.kind === "placed") {
      placed.push([it.obj, next ? { ...it.obj, x: Math.round(next.x), y: Math.round(next.y), turn: next.turn,
        size: next.size } : null]);
      continue;
    }
    const o = it.orig;
    own = own.filter((r) => !sameOrig(r, o));
    if (!next) { own.push({ type: o.type, x: o.x, y: o.y, gone: true }); continue; }
    const back = Math.hypot(next.x - o.x, next.y - o.y) < 1 && Math.abs(next.turn - o.turn) < 0.01
      && Math.abs(next.size - o.size) < 1e-4;
    if (!back) {
      own.push({ type: o.type, x: o.x, y: o.y, to_x: Math.round(next.x), to_y: Math.round(next.y), turn: next.turn,
        size: next.size, lift: o.lift || 0 });
    }
  }
  const step = { placed, before: sel.own, after: own, picked: sel.items.slice() };
  sel.busy = true;
  try {
    await selApply(step, true);
    sel.undo.push(step);
    sel.redo = [];
    placeNote(w.brush_note);
  } catch (err) { placeNote((err && err.message) || String(err), "error"); }
  sel.busy = false;
  selRedraw();
}

function selDelete() {
  return selChange(() => null);
}

// The map's own picked objects put back as the map has them (their rows dropped); what the mod placed stays
async function selRestore() {
  if (sel.busy) return;
  const origs = sel.items.filter((it) => it.kind === "own").map((it) => it.orig);
  const own = sel.own.filter((r) => !origs.some((o) => sameOrig(r, o)));
  if (own.length === sel.own.length) return;
  const step = { placed: [], before: sel.own, after: own, picked: sel.items.slice() };
  sel.busy = true;
  try {
    await selApply(step, true);
    sel.undo.push(step);
    sel.redo = [];
  } catch (err) { placeNote((err && err.message) || String(err), "error"); }
  sel.busy = false;
  selRedraw();
}

async function selUndo() {
  if (sel.busy || !sel.undo.length) return;
  const step = sel.undo.pop();
  sel.busy = true;
  try {
    await selApply(step, false);
    sel.redo.push(step);
  } catch (err) { sel.undo.push(step); placeNote((err && err.message) || String(err), "error"); }
  sel.busy = false;
  selRedraw();
}

async function selRedo() {
  if (sel.busy || !sel.redo.length) return;
  const step = sel.redo.pop();
  sel.busy = true;
  try {
    await selApply(step, true);
    sel.undo.push(step);
  } catch (err) { sel.redo.push(step); placeNote((err && err.message) || String(err), "error"); }
  sel.busy = false;
  selRedraw();
}

// The press of the left button in Select: on a picked object a drag moves them all; elsewhere a box (or a click)
function selPointerDown(ev) {
  const hit = hitGround(ev);
  if (hit && sel.items.length && mv.place.mod) {
    const x = hit.x / SCALE, y = hit.z / SCALE, reach = Math.max(SEL_PICK, pixelsAt(hit, SEL_PIXELS));
    const on = sel.items.some((it) => { const p = selPose(it); return p && Math.hypot(p.x - x, p.y - y) <= reach; });
    if (on && !ev.shiftKey) {
      sel.drag = { x, y, dx: 0, dy: 0, moved: false };
      return true;
    }
  }
  sel.box = { x0: ev.clientX, y0: ev.clientY, x1: ev.clientX, y1: ev.clientY, add: ev.shiftKey, shown: false, ev };
  return true;
}

function selPointerMove(ev) {
  if (sel.drag) {
    const hit = hitGround(ev);
    if (!hit) return;
    const d = sel.drag;
    d.dx = hit.x / SCALE - d.x;
    d.dy = hit.z / SCALE - d.y;
    const was = d.moved;
    d.moved = d.moved || Math.hypot(d.dx, d.dy) > 0.5 * METRE;
    if (!d.moved) return;
    if (!was) placeScenery(); else drawPlaced();  // the map's own picked ones leave their place once, then follow
    drawSelection();
    return;
  }
  const b = sel.box;
  if (!b) return;
  b.x1 = ev.clientX;
  b.y1 = ev.clientY;
  if (!b.shown && Math.abs(b.x1 - b.x0) + Math.abs(b.y1 - b.y0) < 6) return;  // a click, not a box (yet)
  b.shown = true;
  let box = $("sel-box");
  if (!box) {
    box = document.createElement("div");
    box.id = "sel-box";
    box.className = "scen-box";
    document.body.append(box);
  }
  box.style.left = `${Math.min(b.x0, b.x1)}px`;
  box.style.top = `${Math.min(b.y0, b.y1)}px`;
  box.style.width = `${Math.abs(b.x1 - b.x0)}px`;
  box.style.height = `${Math.abs(b.y1 - b.y0)}px`;
}

async function selPointerUp() {
  if (sel.drag) {
    const d = sel.drag;
    if (!d.moved) { sel.drag = null; return; }
    const { dx, dy } = d;
    sel.drag = null;
    await selChange((p) => ({ ...p, x: p.x + dx, y: p.y + dy }));
    return;
  }
  const b = sel.box;
  sel.box = null;
  const box = $("sel-box");
  if (box) box.remove();
  if (!b) return;
  if (b.shown) await selPickBox(b); else await selPickAt(b.ev, b.add);
}

// The tray's part for Select: what's picked, and what can be done with it
function renderSel() {
  const w = mv.words, p = mv.place, on = selecting();
  $("place-sel").classList.toggle("hidden", !on);
  $("place-search").classList.toggle("hidden", on);
  $("place-grid").classList.toggle("hidden", on);
  if (!on) return;
  const own = sel.items.filter((it) => it.kind === "own").length, n = sel.items.length;
  $("place-sel-what").textContent = !n ? w.sel_hint
    : n === 1 ? fill(w.sel_one, { name: typeLabel(selType(sel.items[0])), whose: own ? w.sel_whose_map : w.sel_whose_mod })
      : fill(w.sel_many, { n: n.toLocaleString(), own: own.toLocaleString(), placed: (n - own).toLocaleString() });
  const moved = sel.items.some((it) => it.kind === "own" && ownRow(it.orig));
  for (const [id, text, tip, off] of [["place-sel-delete", w.sel_delete, w.tip_sel_delete, !n || !p.mod],
    ["place-sel-restore", w.sel_restore, w.tip_sel_restore, !moved || !p.mod],
    ["place-sel-clear", w.sel_clear, w.tip_sel_clear, !n]]) {
    $(id).textContent = text;
    $(id).title = tip;
    $(id).disabled = off || sel.busy;
  }
}

// --- showing one map ---
async function show(pack, keepCamera) {
  const w = mv.words, ask = ++mv.ask;
  if (mv.current !== pack && window.MissionView) window.MissionView.forget();  // another map: its own mission
  if (mv.current !== pack) forgetRedo();  // what was taken back on one map can't be put back on another
  mv.current = pack;
  renderList();
  $("map-pick").textContent = w.map_loading;
  $("map-pick").classList.remove("hidden");
  $("map-scratch").classList.add("hidden");  // a map is open: the panel's own "start from scratch" takes over
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
  dropBridges();
  showMark(null);
  forget(gl.ground);
  forget(gl.water);
  gl.ground = made.ground;
  gl.water = made.water;
  gl.water.visible = mv.water;
  gl.scene.add(gl.ground, gl.water);
  mv.edit = made.edit;
  mv.size = made.size;
  mv.brush.painting = null;
  Object.assign(mv.brush, { erase: [], eraseGroups: [], takes: null });  // this map's come with its objects (loadPlaced)
  mv.brush.takesAsk++;
  startErased();
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
  const blank = blankMap(pack);  // nothing of the map it copies is drawn: no models for its objects, no ground pictures
  loadScenery(pack, ask).then(() => loadModels(pack, ask, blank).catch((err) => {  // the shapes stay when
    $("map-ground").textContent = (err && err.message) || String(err);  // models can't be had
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
  if (blank) $("map-ground").textContent = "";  // (the last map's "loading" said nothing more)
  else realGround(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
}

// A map started blank (Duplicate map's Blank Terrain or Blank Ocean; StudioApi.maps "blank"): nothing of the map it
// copies is drawn on it, as nothing of it is in the game (the owner, 2026-10-09: "nothing should be there. This isn't
// D-Day"): not its objects (all erased), its roads (taken out), the items it took out or its ground's pictures. What
// the modder adds shows as on any map.
function blankMap(pack = mv.current) {
  const m = (mv.maps || []).find((x) => x.pack === pack);
  return Boolean(m && m.blank);
}

// --- the dock: the tools by kind along the bottom, as Cities: Skylines does it (a bar of kinds; the kind picked opens
// its tray above), drawn in the game's own HUD look (style.css). [kind, its brushes]: the three place kinds place the
// map's own types; Sectors and the scen_ kinds are the picked scenario's tools (scen.tool). ---
const DOCK = [
  ["terrain", ["hill", "raise", "lower", "crater", "plateau", "flatten", "level", "smooth", "ramp"]],
  ["water", ["water", "drain"]],
  ["cover", ["cover", "uncover", "town", "forest"]],
  ["movement", ["block", "block_infantry", "block_vehicles", "open", "open_infantry", "open_vehicles"]],
  ["roads", null], ["bridges", null],
  ["building", null], ["prop", null], ["vegetation", null], ["paint", ["paint", "stamp", "repaint"]], ["erase", ["erase"]],
  ["sectors", null], ["scen_move", null], ["scen_spawn", null], ["scen_start", null], ["scen_mark", null],
  ["scen_mission", null], ["scen_goals", null], ["scen_events", null], ["scen_cameras", null],
  ["check", null],
];
// The bar's tiles, per side (the owner, 2026-10-09: a Map / Scenario button "swaps the tool panel only"; Map is
// "terrain, roads, like making woods, making like cities", Scenario "spawning the units, choosing the sides, the camera
// angles"): kinds that go together share one (the owner, 2026-10-01: the bar was too long), its tray showing a tab per
// kind. [group, its kinds, its icon]. Map Paint holds Paint and Erase (the owner, 2026-10-03: "an editing tab or like a
// drawing tab and include the erase tool with it"). Check is on both sides.
const DOCK_GROUPS = {
  map: [
    ["ground", ["terrain", "water"], "terrain"],
    ["zones", ["cover", "movement"], "cover"],
    ["ways", ["roads", "bridges"], "roads"],
    // a town's buildings and its name together (the names are the scenario's items, placed on this side); a tile of
    // their own wrapped the bar onto two rows
    ["building", ["building", "scen_names"], "building"],
    ["nature", ["prop", "vegetation"], "vegetation"],
    ["paint", ["paint", "erase"], "paint"],
    ["sectors", ["sectors"], "sectors"],
    ["check", ["check"], "check"],
  ],
  scenario: [
    ["scen_move", ["scen_move"], "move"],
    ["scen_spawn", ["scen_spawn"], "spawn"],
    ["scen_start", ["scen_start"], "start"],
    ["scen_mark", ["scen_mark"], "mark"],
    // a new Operation's or chapter's own mission (mission.js): sides and rules, goals and events, camera moves
    ["scen_mission", ["scen_mission"], "mission"],
    ["scen_story", ["scen_goals", "scen_events"], "goals"],
    ["scen_cameras", ["scen_cameras"], "camera"],
    ["check", ["check"], "check"],
  ],
};
const MISSION_DOCK_KINDS = new Set(["scen_mission", "scen_goals", "scen_events", "scen_cameras"]);  // need a mission's map
const SCEN_KINDS = new Set(["sectors", "scen_names", "scen_move", "scen_spawn", "scen_start", "scen_mark",
  ...MISSION_DOCK_KINDS]);
const MAP_SIDE_TOOLS = new Set(["sectors", "names"]);   // the scenario's tools whose tiles are on the Map side
const scenToolOf = (kind) => (kind === "sectors" ? "sectors" : kind.slice("scen_".length));
// the mission's trays are forms: the map turns and grabs as when looking around (Camera moves takes its clicks)
const FORM_TOOLS = new Set(["mission", "goals", "events"]);
const MISSION_TOOLS = new Set(["mission", "goals", "events", "cameras"]);

// Why the open map can't have a mission of its own (a word key), or null: a new Operation's or chapter's only
function missionLocked() {
  const m = mv.maps.find((x) => x.pack === mv.current);
  if (!m || !m.copy_of) return "mission_why_copy";
  return (m.kinds || []).some((k) => k === "operation" || k === "campaign") ? null : "mission_why_battles";
}
// "Check this map" open; the last brush of each kind; the last kind open in each group
const dock = { check: false, last: {}, lastIn: {} };

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
  bridges: "M2 9h20 M5 9v11 M19 9v11 M5 20c1.5-6 12.5-6 14 0 M2 5h20",
  check: "M12 3l8 3v6c0 5-3.5 8-8 9.5C7.5 20 4 17 4 12V6z M8.5 12l2.5 2.5 4.5-5",
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
  erase: "M4 15l9-9 7 7-6 6H8z M9 10l7 7 M3 21h18",
  paint: "M14 3l7 7-8 8-4 1 1-4z M12 5l7 7 M4 21c3 0 4-1 4-3",
  stamp: "M9 3h6v5l-2 2v3h6v4H5v-4h6v-3L9 8z M4 21h16",
  repaint: "M3 19l6-9 4 5 3-4 5 8z M14 3l1 2 2 1-2 1-1 2-1-2-2-1 2-1z",  // a hill, a spark over it
  move:"M12 3v18 M3 12h18 M9 6l3-3 3 3 M9 18l3 3 3-3 M6 9l-3 3 3 3 M18 9l3 3-3 3",
  spawn: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M12 8v8 M8 12h8",
  start: "M6 21V3 M6 4h11l-3 4 3 4H6",
  mark: "M12 21s-6-6.5-6-11a6 6 0 0 1 12 0c0 4.5-6 11-6 11z M12 7.5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 1 0 0-5z",
  sectors: "M3 4h18v16H3z M3 11c4 0 5-3 9-3 M12 8v12 M12 14c3 0 5 2 9 2",
  mission: "M6 3h9l4 4v14H6z M15 3v4h4 M9 11h7 M9 15h7 M9 19h4",
  goals: "M12 3a9 9 0 1 0 0 18a9 9 0 1 0 0-18z M12 7a5 5 0 1 0 0 10a5 5 0 1 0 0-10z M12 11a1 1 0 1 0 0 2a1 1 0 1 0 0-2z",
  camera: "M3 8h12v10H3z M15 11l6-3v10l-6-3 M6 5h4",
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
    bridges: w.dock_bridges, check: w.dock_check, erase: w.brush_erase, paint: w.dock_paint, sectors: w.scen_sectors_tool,
    scen_move: w.scen_move_tool, scen_spawn: w.scen_spawn_tool, scen_start: w.scen_start_tool, scen_mark: w.scen_mark_tool,
    scen_names: w.scen_names_tool,
    scen_mission: w.scen_mission_tool, scen_goals: w.scen_goals_tool, scen_events: w.scen_events_tool,
    scen_cameras: w.scen_cameras_tool }[kind]
    || w[`scenery_${kind}`] || kind;
}

// What a kind does, one sentence (its tile's and its tray's): a scenario tool says its own (tip_scen_*)
function kindTip(kind) {
  const w = mv.words;
  return (SCEN_KINDS.has(kind) ? w[`tip_scen_${scenToolOf(kind)}`] : w[`tip_dock_${kind}`]) || "";
}

// The scenario picked in the map panel (each has its own units, HQs, names and sectors), or none
function pickedScenario() {
  return ((scen.data || {}).scenarios || [])[scen.pick] || null;
}

// The kind open: the brush's, the place kind's, or the scenario tool's; null while just looking around.
function dockKind() {
  if (mv.brush.on) return brushKind(mv.brush.name);
  if (road.on) return "roads";
  if (bridge.on) return "bridges";
  if (mv.place.on) return mv.place.group;
  if (dock.check) return "check";
  return scen.tool ? (scen.tool === "sectors" ? "sectors" : "scen_" + scen.tool) : null;
}

function openKind(kind) {
  if (dockKind() === kind) { lookAround(); return; }  // the open kind again closes it
  const brushes = (DOCK.find(([k]) => k === kind) || [])[1];
  if (brushes) { pickBrush(dock.last[kind] || brushes[0]); return; }
  if (kind === "roads") { setRoadMode(true); return; }
  if (kind === "bridges") { setBridgeMode(true); return; }
  if (kind === "check") {
    lookAround();
    dock.check = true;
    renderCheck();
    renderDock();
    return;
  }
  if (SCEN_KINDS.has(kind)) {
    if (MISSION_DOCK_KINDS.has(kind) ? missionLocked() : !pickedScenario()) return;  // its tile is locked and says why
    lookAround();
    setScenTool(scenToolOf(kind));
    return;
  }
  mv.place.group = kind;
  dropPlaceGesture();
  placeOptions();
  setPlaceMode(true);
}

const dockGroups = () => DOCK_GROUPS[mv.mode];

function groupOf(kind) {
  return (dockGroups().find(([, kinds]) => kinds.includes(kind)) || [null])[0];
}

function groupName(group) {
  const [, kinds] = dockGroups().find(([g]) => g === group);
  return kinds.length === 1 ? kindName(kinds[0]) : mv.words[`dock_group_${group}`] || kinds.map(kindName).join(" & ");
}

// A tile opens its group at the kind last used there; the open group's tile again closes it.
function openGroup(group) {
  const [, kinds] = dockGroups().find(([g]) => g === group);
  if (kinds.includes(dockKind())) { lookAround(); return; }
  openKind(dock.lastIn[group] || kinds[0]);
}

// The bar's tiles, again when the words change or the side does.
function renderDockBar() {
  const w = mv.words;
  for (const [id, mode, word, tip] of [["mode-map", "map", "mode_map", "tip_mode_map"],
    ["mode-scen", "scenario", "scen_show", "tip_mode_scenario"]]) {
    const b = $(id);
    b.textContent = w[word] || mode;
    b.title = w[tip] || "";
    b.setAttribute("aria-checked", String(mv.mode === mode));
  }
  $("dock-mode").setAttribute("aria-label", w.mode_label || "");
  iconTile($("brush-look"), "look", w.brush_look).title = w.tip_look;
  $("dock-kinds").replaceChildren(...dockGroups().map(([group, kinds, icon]) => {
    const tip = kinds.length === 1 ? kindTip(kinds[0]) : w[`tip_dock_group_${group}`];
    const tile = iconTile(el("button", { type: "button", className: "dock-tile", title: tip || "" }), icon,
      groupName(group));
    tile.dataset.group = group;
    tile.dataset.tip = tip || "";
    tile.addEventListener("click", () => openGroup(group));
    return tile;
  }));
  renderDock();
}

function renderDock() {
  const w = mv.words, kind = dockKind(), group = groupOf(kind), s = pickedScenario();
  if (group) dock.lastIn[group] = kind;
  $("brush-look").setAttribute("aria-pressed", String(!kind));
  for (const tile of $("dock-kinds").children) {
    tile.setAttribute("aria-pressed", String(tile.dataset.group === group));
    // a scenario's tools need a scenario, a mission's a new Operation or chapter: locked, saying why
    const g = tile.dataset.group;
    const kindsOf = (dockGroups().find(([x]) => x === g) || [null, []])[1];
    const why = kindsOf.some((k) => MISSION_DOCK_KINDS.has(k)) ? missionLocked() && w[missionLocked()]
      : SCEN_KINDS.has(g) && !s ? (g === "sectors" ? w.tip_scen_sectors_locked : w.tip_scen_locked) : null;
    tile.disabled = Boolean(why);
    tile.title = why || tile.dataset.tip;
  }
  // a group of two kinds: a tab for each, above the open one's tools
  const kinds = group ? dockGroups().find(([g]) => g === group)[1] : [];
  $("tray-tabs").replaceChildren(...(kinds.length > 1 ? kinds.map((k) => {
    const tab = el("button", { type: "button", className: "tray-tab", textContent: kindName(k), title: kindTip(k) });
    if (SCEN_KINDS.has(k) && !s) { tab.disabled = true; tab.title = w.tip_scen_locked; }   // Names needs a scenario
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", String(k === kind));
    tab.addEventListener("click", () => { if (k !== dockKind()) openKind(k); });
    return tab;
  }) : []));
  $("dock-tray").classList.toggle("hidden", !kind);
  $("tray-brush").classList.toggle("hidden", !(kind && (DOCK.find(([k]) => k === kind) || [])[1]));
  $("tray-place").classList.toggle("hidden", !PLACEABLE.includes(kind));
  $("tray-scen").classList.toggle("hidden", !(SCEN_KINDS.has(kind) && kind !== "sectors" && !MISSION_DOCK_KINDS.has(kind)));
  $("tray-sectors").classList.toggle("hidden", kind !== "sectors");
  $("tray-mission").classList.toggle("hidden", !MISSION_DOCK_KINDS.has(kind));
  $("tray-roads").classList.toggle("hidden", kind !== "roads");
  $("tray-bridges").classList.toggle("hidden", kind !== "bridges");
  $("tray-check").classList.toggle("hidden", kind !== "check");
  $("tray-title").textContent = kind ? groupName(group) : "";
  $("tray-tip").textContent = kind ? kindTip(kind) : "";
}

// The switch between the two sides: whatever tool was open closes, the bar takes the other side's tools, and the
// side left behind fades and locks (fadeLayers, canGrab, the hover line). Kept by the Studio (prefs "view").
function setMode(mode) {
  if (mv.mode === mode) return;
  lookAround();
  toMode(mode);
}

// The side a tool belongs to, when the tool is opened another way (a key, a button in a list): the bar follows it.
function toMode(mode) {
  if (mv.mode === mode) return;
  mv.mode = mode;
  if (mode === "map" && (scen.sel.size || scen.selected !== null)) {  // the scenario's selection doesn't stay behind
    scen.sel.clear();
    scen.selected = null;
  }
  $("scenery-hover").textContent = "";
  renderDockBar();
  if (scen.data) drawScenario();  // its hover words: "drag to move" only where it moves
  renderScenTools();
  pointerMode();
  saveView();
  if (mv.gl) mv.gl.draw();
}

// --- new roads, Cities: Skylines style (maps/<map>/roads.toml; StudioApi.road_add, rusemod.roadnet). Straight: click
// where it starts, then where it ends; Curve: the start, the bend, the end; Freeform: click along the way, then
// double-click or Enter (or Finish). An end near a road snaps onto it (a ring shows where) and joins it. New roads
// are drawn as blue ribbons, the way the game draws a supply route. Proven in the game (2026-09-30): supply routes
// follow a road added this way. Not painted on the ground yet. ---
const ROAD_TOOLS = ["straight", "curve", "free"];
const ROAD_SNAP = 15000;    // map units (about 58 m): an end this near a road snaps onto it
const ROAD_WIDTH = 1800;    // map units drawn (about 7 m)
const ROAD_SAMPLE = 2000;   // map units between the points of a road's saved line
const road = { on: false, tool: "straight", pts: [], mine: [], mod: null, mesh: null, preview: null, snap: null,
  cursor: null, cross: null, snapOn: true, keepTrees: false };  // snapOn: the tray's "Snap ends" box, keepTrees its
// "Keep the trees" box (the next roads drawn keep the trees and bushes on their path: roads.toml keep_trees), both
// kept with the view (saveView)

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

// The ends of the bridges the mod places by hand (the Bridges dock): a road's end snaps to them before any road.
function bridgeEnds() {
  const types = bridgeTypes();
  return mv.place.objects.filter((o) => types.has(o.type)).flatMap((o) => deckOf(o, types.get(o.type)));
}

// The point to use for a road's end at (x, y): the end of a bridge placed by hand within ROAD_SNAP (the owner,
// 2026-10-03: "trying to snap the road to the bridge ... It wants to snap to the road"), else the nearest road's,
// else where it was clicked. Off with the tray's "Snap ends" box (road.snapOn).
function roadSnap(x, y) {
  if (!road.snapOn) return { x, y, snapped: false };
  let best = ROAD_SNAP * ROAD_SNAP, hit = null;
  for (const [bx, by] of bridgeEnds()) {
    const d = (bx - x) ** 2 + (by - y) ** 2;
    if (d < best) { best = d; hit = { x: bx, y: by, snapped: true, bridge: true }; }
  }
  if (hit) return hit;
  if (!road.samples) road.samples = roadSamples();
  const S = road.samples;
  let at = -1;
  for (let i = 0; i < S.length; i += 2) {
    const d = (S[i] - x) ** 2 + (S[i + 1] - y) ** 2;
    if (d < best) { best = d; at = i; }
  }
  return at < 0 ? { x, y, snapped: false } : { x: S[at], y: S[at + 1], snapped: true };
}

// Whether the next click is a road's end, the only points that snap (a curve's bend and a freeform road's points on
// the way go where they're clicked; a freeform road's last point snaps as it's finished, finishRoad).
function roadEndNext() {
  const n = road.pts.length;
  return n === 0 || (road.tool === "straight" && n === 1) || (road.tool === "curve" && n === 2);
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
function roadRibbon(lines, mesh, color, opacity, width = ROAD_WIDTH, order = 5) {
  const gl = mv.gl, { THREE } = gl, grid = makeGrid(mv.edit), pos = [], half = width / 2;
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
    mesh.renderOrder = order;
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
  // where the new roads cross water, in gold over them: a bridge of the map's kind goes there (rusemod.bridges.plan)
  const spans = road.mine.flatMap((r) => (r.crossings || []).map(([x0, y0, x1, y1]) => [[x0, y0], [x1, y1]]));
  road.cross = roadRibbon(spans, road.cross, PLACED_COLOUR, 0.95, BRIDGE_WIDTH, 6);
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
  for (const k of ["mesh", "preview", "cross"]) {
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
  road.takeOut = res.take_out || [];
  road.samples = null;
  drawModRoads();
  renderRoadTray();
  renderBridgeTray();
}

// The map's own roads and bridges taken out, or kept (StudioApi.road_take_out: roads.toml take_out), one switch each.
// "crossings" (close where the old bridges stood) goes with the bridges: it turns them on, and goes when they stay.
async function setTakeOut(what) {
  const pack = mv.current, now = new Set(road.takeOut || []);
  if (now.has(what)) now.delete(what); else now.add(what);
  if (what === "crossings" && now.has("crossings")) now.add("bridges");
  if (what === "bridges" && !now.has("bridges")) now.delete("crossings");
  try {
    const res = await mv.api.road_take_out(pack, now.has("roads"), now.has("bridges"), now.has("crossings"));
    if (pack !== mv.current) return;
    road.takeOut = res.take_out || [];
    renderRoadTray();
  } catch (err) { roadNote((err && err.message) || String(err), "error"); }
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
  $("road-redo").textContent = w.brush_redo;
  $("road-redo").title = w.tip_road_redo;
  $("road-redo").disabled = !redo.road.length || !road.mod;
  $("road-snap").checked = road.snapOn;
  $("road-snap-label").textContent = w.road_snap || "Snap ends to roads and bridges";
  $("road-snap-row").title = w.tip_road_snap || "";
  $("road-trees").checked = road.keepTrees;
  $("road-trees-label").textContent = w.road_trees || "Keep the trees on new roads";
  $("road-trees-row").title = w.tip_road_trees || "";
  const taken = new Set(road.takeOut || []);
  $("road-takeout").replaceChildren(...(road.mod ? ["roads", "bridges", "crossings"].map((what) =>
    chipOf(w["road_take_out_" + what], w["tip_road_take_out_" + what], taken.has(what), () => setTakeOut(what))) : []));
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
    toMode("map");
    dock.check = false;
    stopBridge();
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
  if (road.tool === "free") {  // its last point is its end: that one snaps (roadEndNext)
    const q = roadSnap(...pts[pts.length - 1]);
    pts[pts.length - 1] = [q.x, q.y];
  }
  const line = roadLine(road.tool, pts);
  drawRoadPreview();
  try {
    const keep = road.keepTrees;
    await mv.api.road_add(pack, line, 3000, keep);
    if (pack !== mv.current) return;
    road.mine.push({ points: line, join: 3000, crossings: [], keep_trees: keep });
    redo.road = [];
    road.samples = null;  // the new road's points snap too
    drawModRoads();
    renderRoadTray();
    roadNote(mv.words.road_note);
    refreshCrossings(pack);
  } catch (err) { roadNote((err && err.message) || String(err), "error"); }
}

// The roads again from the mod, for where they cross water (found by the Studio on the map's ground).
function refreshCrossings(pack) {
  loadModRoads(pack, mv.ask).catch((err) => roadNote((err && err.message) || String(err), "error"));
}

async function undoRoad() {
  const pack = mv.current;
  if (!road.mine.length) return;
  try {
    const res = await mv.api.road_undo(pack, 1);
    if (pack !== mv.current) return;
    redo.road.push(...road.mine.splice(road.mine.length - res.removed, res.removed));
    road.samples = null;
    drawModRoads();
    renderRoadTray();
    renderBridgeTray();
  } catch (err) { roadNote((err && err.message) || String(err), "error"); }
}

// Redo in the Roads tray: the last road Undo took back, drawn again along the same line.
async function redoRoad() {
  const pack = mv.current;
  if (!road.mod || !redo.road.length) return;
  const r = redo.road.pop();
  try {
    await mv.api.road_add(pack, r.points, r.join, Boolean(r.keep_trees));
    if (pack !== mv.current) return;
    road.mine.push({ points: r.points, join: r.join, crossings: [], keep_trees: Boolean(r.keep_trees) });
    road.samples = null;
    drawModRoads();
    renderRoadTray();
    refreshCrossings(pack);
  } catch (err) {
    if (pack !== mv.current) return;
    redo.road.push(r);
    roadNote((err && err.message) || String(err), "error");
  }
}

// A click while drawing a road: the next point (snapped); Straight ends at its second, Curve at its third.
function roadPointerDown(ev) {
  if (!road.on || ev.button !== 0 || !mv.gl.ground || !mv.edit) return;
  ev.preventDefault();
  if (!road.mod) { roadNote(mv.words.no_mod, "error"); return; }
  const hit = hitGround(ev);
  if (!hit) return;
  const p = roadEndNext() ? roadSnap(hit.x / SCALE, hit.z / SCALE) : { x: hit.x / SCALE, y: hit.z / SCALE };
  road.pts.push([p.x, p.y]);
  const need = road.tool === "straight" ? 2 : road.tool === "curve" ? 3 : Infinity;
  if (road.pts.length >= need) finishRoad();
  else { renderRoadTray(); drawRoadPreview(); showRoadLength(ev); }
}

function roadPointerMove(ev) {
  const hit = hitGround(ev);
  if (!hit) { showRoadLength(null); return; }
  const p = roadEndNext() ? roadSnap(hit.x / SCALE, hit.z / SCALE) : { x: hit.x / SCALE, y: hit.z / SCALE, snapped: false };
  road.snap = p.snapped ? p : null;
  road.cursor = [p.x, p.y];
  drawRoadPreview();
  showRoadLength(ev);
}

// --- the Bridges dock (StudioApi.map_bridges, bridge_add; rusemod.bridges): the map's own bridge kinds, one placed by
// hand where the ground is clicked (its middle), at the length and turn set, saved with the placed objects in the
// mod's maps/<map>/scenery.toml (Undo here takes the last one back while it's a bridge). New roads' water crossings
// show in gold (drawModRoads): the build puts a bridge of the map's kind on each. A map with no bridge kind of its own
// says so, in the build's own words (rusemod.bridges.no_kind_note). ---
const BRIDGE_WIDTH = 2560;  // map units a deck is drawn (rusemod.bridges.DECK)
const bridge = { on: false, pack: null, kinds: null, loading: false, error: "", type: null, turn: 0, length: {},
  cursor: null, mesh: null, preview: null };

function bridgeNote(text, kind) {
  const n = $("bridge-note");
  n.textContent = text || "";
  n.className = "small" + (kind === "error" ? " error-text" : "");
}

// The map's kinds once read (null before), and the one picked.
function bridgeKinds() {
  return bridge.pack === mv.current ? bridge.kinds : null;
}

function bridgeKind() {
  return (bridgeKinds() || []).find((k) => k.type === bridge.type) || null;
}

// The bridge types this map's mod places by hand, by type: {type: kind}.
function bridgeTypes() {
  return new Map((bridgeKinds() || []).map((k) => [k.type, k]));
}

// The length set for a kind, in map units: its model's own to start with, kept within what it stretches to.
function bridgeLength(k) {
  const m = bridge.length[k.type] ?? k.length;
  return Math.min(k.most, Math.max(k.least, m));
}

// A bridge's deck as [[x0, y0], [x1, y1]]: its model's length through its size and stretch, along its turn less the
// model's own axis turn (rusemod.bridges.deck).
function deckOf(o, k) {
  const a = (o.turn - k.turn) * Math.PI / 180;
  const half = k.length * o.size * (k.turn % 180 === 90 ? (o.stretch || 1) : 1) / 2;
  return [[o.x - Math.cos(a) * half, o.y - Math.sin(a) * half], [o.x + Math.cos(a) * half, o.y + Math.sin(a) * half]];
}

// Read once per map (each kind's model is measured): when the tray first opens, or when the mod places objects.
async function loadBridges(pack) {
  if (bridge.pack === pack && (bridge.kinds || bridge.loading)) return;
  Object.assign(bridge, { pack, kinds: null, loading: true, error: "" });
  renderBridgeTray();
  try {
    const res = await mv.api.map_bridges(pack);
    if (bridge.pack !== pack) return;
    bridge.kinds = res.kinds;
    const usable = res.kinds.filter((k) => k.placed);
    if (!usable.some((k) => k.type === bridge.type)) bridge.type = usable.length ? usable[0].type : null;
  } catch (err) {
    if (bridge.pack !== pack) return;
    bridge.error = (err && err.message) || String(err);
  } finally {
    if (bridge.pack === pack) bridge.loading = false;
  }
  drawPlaced();
  renderBridgeTray();
}

function dropBridges() {
  for (const k of ["mesh", "preview"]) {
    if (bridge[k] && mv.gl) { mv.gl.scene.remove(bridge[k]); bridge[k].geometry.dispose(); bridge[k].material.dispose(); }
    bridge[k] = null;
  }
  Object.assign(bridge, { pack: null, kinds: null, loading: false, error: "", cursor: null });
}

// The bridges the mod places by hand, as gold decks; and while placing, the next one under the pointer.
function drawBridges() {
  const gl = mv.gl;
  if (!gl) return;
  if (!mv.edit) { gl.draw(); return; }
  const types = bridgeTypes();
  const decks = mv.place.objects.filter((o) => types.has(o.type)).map((o) => deckOf(o, types.get(o.type)));
  bridge.mesh = roadRibbon(decks, bridge.mesh, PLACED_COLOUR, 0.95, BRIDGE_WIDTH, 6);
  const k = bridgeKind(), c = bridge.on && bridge.cursor;
  let next = [];
  if (k && c) {
    const a = bridge.turn * Math.PI / 180, half = bridgeLength(k) / 2;
    next = [[[c[0] - Math.cos(a) * half, c[1] - Math.sin(a) * half], [c[0] + Math.cos(a) * half, c[1] + Math.sin(a) * half]]];
  }
  bridge.preview = roadRibbon(next, bridge.preview, 0xf3dc8a, 0.6, BRIDGE_WIDTH, 7);
  gl.draw();
}

function renderBridgeTray() {
  const w = mv.words, kinds = bridgeKinds(), k = bridgeKind();
  $("bridge-help").textContent = w.bridges_help;
  const crossings = road.mine.reduce((n, r) => n + (r.crossings || []).length, 0);
  let note = "";
  if (kinds && !kinds.length) note = crossings ? fill(w.bridges_none, { n: crossings }) : w.bridges_none_map;
  else if (crossings) note = fill(w.bridges_crossings, { n: crossings });
  $("bridge-map-note").textContent = bridge.error || (bridge.loading || (!kinds && bridge.on) ? w.bridges_loading : note);
  $("bridge-map-note").className = "small" + (bridge.error || (kinds && !kinds.length) ? " error-text" : "");
  $("bridge-kinds").replaceChildren(...(kinds || []).map((kind) => {
    const b = el("button", { type: "button", className: "kind-row", disabled: !kind.placed,
      title: kind.placed ? kind.type : w.bridges_no_floor });
    b.setAttribute("aria-pressed", String(kind.type === bridge.type));
    b.append(el("b", {}, kind.name));
    if (kind.roads) b.append(el("span", { className: "tag" }, w.bridges_roads_kind));
    b.append(el("span", { className: "muted small" }, kind.placed
      ? fill(w.bridges_kind_info, { n: kind.placed, least: Math.round(kind.least / METRE), most: Math.round(kind.most / METRE) })
      : w.bridges_no_floor));
    b.addEventListener("click", () => { bridge.type = kind.type; if (!bridge.on) setBridgeMode(true); else renderBridgeTray(); });
    return b;
  }));
  const len = $("bridge-length");
  len.disabled = !k;
  if (k) {
    len.min = Math.round(k.least / METRE);
    len.max = Math.round(k.most / METRE);
    len.value = Math.round(bridgeLength(k) / METRE);
  }
  $("bridge-length-label").textContent = fill(w.bridges_length, { m: k ? Math.round(bridgeLength(k) / METRE) : "–" });
  len.title = w.tip_bridges_length;
  $("bridge-turn").value = bridge.turn;
  $("bridge-turn").title = w.tip_bridges_turn;
  $("bridge-turn-label").textContent = `${w.place_turn} ${bridge.turn}°`;
  const types = bridgeTypes(), mine = mv.place.objects.filter((o) => types.has(o.type)).length;
  const last = mv.place.objects[mv.place.objects.length - 1];
  $("bridge-undo").textContent = w.brush_undo;
  $("bridge-undo").title = w.tip_bridges_undo;
  $("bridge-undo").disabled = !(last && types.has(last.type)) || !mv.place.mod;
  $("bridge-redo").textContent = w.brush_redo;
  $("bridge-redo").title = w.tip_bridges_redo;
  $("bridge-redo").disabled = !bridgeRedoNext() || !mv.place.mod;
  $("bridge-count").textContent = mine ? fill(w.bridges_count, { n: mine }) : "";
  if (bridge.on) $("map-help").textContent = w.bridges_help;
}

function stopBridge() {
  if (!bridge.on) return;
  bridge.on = false;
  bridge.cursor = null;
  drawBridges();
}

function setBridgeMode(on) {
  if (on) {
    if (mv.brush.on) setBrushMode(false);
    if (mv.place.on) setPlaceMode(false);
    if (scen.tool) { scen.tool = null; scen.selected = null; renderScenTools(); drawScenario(); }
    toMode("map");
    dock.check = false;
    stopRoad();
    bridge.on = true;
    loadBridges(mv.current);
    bridgeNote(mv.place.mod ? "" : mv.words.no_mod, "error");
  } else stopBridge();
  pointerMode();
  renderBridgeTray();
  renderDock();
  if (!on) $("map-help").textContent = mv.words.map_help;
}

// A click while placing a bridge: one of the kind picked, its middle there.
async function bridgeAt(ev) {
  const w = mv.words, pack = mv.current, k = bridgeKind();
  if (!mv.place.mod) { bridgeNote(w.no_mod, "error"); return; }
  if (!k) { bridgeNote(bridge.error || (bridgeKinds() ? (bridgeKinds().length ? w.place_pick : w.bridges_none_map) : w.bridges_loading), "error"); return; }
  const hit = hitGround(ev);
  if (!hit) { bridgeNote(w.place_ground, "error"); return; }
  try {
    const res = await mv.api.bridge_add(pack, k.type, Math.round(hit.x / SCALE), Math.round(hit.z / SCALE), bridge.turn,
      bridgeLength(k));
    if (pack !== mv.current) return;
    mv.place.objects.push(res.object);
    mv.place.groups.push([res.object]);  // a group is the objects Undo takes back (a bare count took nothing back)
    redo.place = [];
    drawPlaced();
    renderPlace();
    bridgeNote(w.brush_note);
  } catch (err) {
    if (pack !== mv.current) return;
    bridgeNote((err && err.message) || String(err), "error");
  }
  renderBridgeTray();
}

// Undo in the Bridges tray: the last object placed, while it's a bridge (Undo in a place tray takes any).
async function undoBridge() {
  const last = mv.place.objects[mv.place.objects.length - 1];
  if (!last || !bridgeTypes().has(last.type)) return;
  await undoPlace();
  renderBridgeTray();
}

// Redo in the Bridges tray: the last bridge Undo took back (while what's next to redo is a bridge).
function bridgeRedoNext() {
  const group = redo.place[redo.place.length - 1];
  return Boolean(group && group.length === 1 && bridgeTypes().has(group[0].type));
}

async function redoBridge() {
  if (!bridgeRedoNext()) return;
  await redoPlace();
  renderBridgeTray();
}

function bridgePointerMove(ev) {
  const hit = hitGround(ev);
  bridge.cursor = hit ? [hit.x / SCALE, hit.z / SCALE] : null;
  drawBridges();
}

// --- "Check this map" (StudioApi.map_check; rusemod.mapcheck): the mod built on this map in the background, and
// what would go wrong listed in plain words; one with a place centres the map on it, a ring marking the spot. ---
const check = { job: null, pack: null, lines: 0, findings: null, error: "", made: "", mark: null };

// What the mod changes on the map, roughly: a result from before a change says so.
function checkMade() {
  return [mv.current, mv.brush.strokes.length, mv.place.objects.length, road.mine.length].join("|");
}

function findingText(f) {
  const w = mv.words, data = { ...f.data };
  if (data.units) data.units = w["mc_units_" + data.units] || data.units;
  if (f.say === "mc_mission_link") {  // a link of a mission's chain: the mission by its menu name, the link in words
    const s = ((scen.data || {}).scenarios || []).find((x) => x.file.toLowerCase() === String(data.mission).toLowerCase());
    data.mission = s ? scenarioLabel(s) : data.mission;
    data.why = w["mission_why_" + data.why] || data.why;
  }
  for (const k of ["metres", "n"]) if (typeof data[k] === "number") data[k] = data[k].toLocaleString();  // (x, y) as they are
  return fill(w[f.say] || f.say, data);
}

async function runCheck() {
  const pack = mv.current, w = mv.words;
  if (!pack || check.job) return;
  Object.assign(check, { pack, findings: null, error: "", lines: 0 });
  showMark(null);
  try {
    check.job = (await mv.api.map_check(pack)).job;
  } catch (err) {
    check.error = (err && err.message) || String(err);
    renderCheck();
    return;
  }
  check.made = checkMade();
  renderCheck();
  $("check-status").textContent = w.check_running;
  for (;;) {
    await new Promise((done) => setTimeout(done, 700));
    let res;
    try { res = await mv.api.job(check.job, check.lines); } catch (err) { res = { state: "failed", message: (err && err.message) || String(err) }; }
    if (res.lines && res.lines.length) {
      check.lines = res.count;
      $("check-status").textContent = `${w.check_running} ${res.lines[res.lines.length - 1].trim()}`;
    }
    if (res.state === "running") continue;
    check.job = null;
    if (res.state === "done" && res.result) check.findings = res.result.findings;
    else check.error = res.message || "";
    break;
  }
  renderCheck();
}

function renderCheck() {
  const w = mv.words, mine = check.pack === mv.current;
  const run = $("check-run");
  run.textContent = w.check_run;
  run.title = w.tip_check_run;
  run.disabled = Boolean(check.job) || !mv.place.mod;
  const status = $("check-status");
  status.className = "small" + (mine && check.error ? " error-text" : " muted");
  if (!mv.place.mod) { status.textContent = w.no_mod; status.className = "small error-text"; }
  else if (check.job && mine) status.textContent ||= w.check_running;
  else if (mine && check.error) status.textContent = check.error;
  else if (mine && check.findings) {
    const real = check.findings.filter((f) => f.level !== "ok");
    status.textContent = real.length ? fill(w.check_found, { n: real.length }) : "";
    if (check.made !== checkMade()) status.textContent += (status.textContent ? " " : "") + w.check_stale;
  } else status.textContent = w.tip_dock_check;
  const list = $("check-list");
  list.replaceChildren(...(mine && check.findings && !check.job ? check.findings : []).map((f) => {
    const placed = typeof f.data.x === "number" && typeof f.data.y === "number";
    const item = el(placed ? "button" : "div", { className: `finding level-${f.level}` });
    if (placed) {
      item.type = "button";
      item.addEventListener("click", () => {
        for (const b of list.children) b.removeAttribute("aria-current");
        item.setAttribute("aria-current", "true");
        lookAt(f.data.x, f.data.y);
      });
    }
    item.append(el("span", { className: "finding-dot" }), el("span", {}, findingText(f)));
    return item;
  }));
}

// Centre the map on (x, y), closer in when far out, with a ring on the spot.
function lookAt(x, y) {
  const gl = mv.gl;
  if (!gl || !mv.edit) return;
  const { camera, controls } = gl, grid = makeGrid(mv.edit);
  const at = new gl.THREE.Vector3(x * SCALE, groundAt(grid, x, y) * SCALE, y * SCALE);
  const offset = camera.position.clone().sub(controls.target);
  const near = mv.size * 0.12;
  if (offset.length() > near) offset.setLength(near);
  controls.target.copy(at);
  camera.position.copy(at).add(offset);
  controls.update();
  showMark(at);
}

function showMark(at) {
  const gl = mv.gl;
  if (!gl) return;
  if (!check.mark) {
    const { THREE } = gl;
    check.mark = new THREE.Mesh(new THREE.RingGeometry(0.8, 1, 48),
      new THREE.MeshBasicMaterial({ color: 0xe0533d, transparent: true, opacity: 0.95, depthTest: false, side: THREE.DoubleSide }));
    check.mark.rotation.x = -Math.PI / 2;
    check.mark.renderOrder = 11;
    gl.scene.add(check.mark);
  }
  check.mark.visible = Boolean(at);
  if (at) {
    const r = 5000 * SCALE;
    check.mark.position.set(at.x, at.y + r * 0.05, at.z);
    check.mark.scale.set(r, r, r);
  }
  gl.draw();
}

// --- the brush tools ---
function settingsOf(name) {
  if (!mv.brush.settings[name]) {
    mv.brush.settings[name] = { size: BRUSHES[name][4], strength: BRUSHES[name][5], shape: "round", edge: "soft", angle: 0 };
  }
  return mv.brush.settings[name];
}

// Which brush types a brush offers: the shapes (a ramp is a line already; Town and Forest work round the click) and
// whether its edge can be hard (only the ground brushes fall off: cover, movement, water and Erase take whole cells).
function tipChoices(name) {
  const kind = BRUSHES[name][0];
  const shapes = ["ramp", "town", "forest"].includes(kind) ? [] : ["round", "square", "line"];
  const edges = ["add", "level", "smooth", "ramp", "paint", "stamp"].includes(kind) && shapes.length ? ["soft", "hard"] : [];
  return { shapes, edges };
}

// The picked brush's shape as a stroke's fields (rusemod/brush.py): a square's turn as its direction, a line's end.
function tipFields(name, end) {
  const set = settingsOf(name), { shapes, edges } = tipChoices(name), out = {};
  const shape = shapes.includes(set.shape) ? set.shape : "round";
  if (shape === "square") {
    const a = set.angle * Math.PI / 180;
    out.shape = "square";
    out.dx = Math.round(Math.cos(a) * 1e6) / 1e6;  // the Studio turns the angle into the direction; the build needs no
    out.dy = Math.round(Math.sin(a) * 1e6) / 1e6;  // sines (every PC must build the same bytes)
    if (out.dx === 0 && out.dy === 0) out.dx = 1;
  } else if (shape === "line" && end) {
    Object.assign(out, { shape: "line", x2: end.x, y2: end.y });
  }
  if (edges.includes(set.edge) && set.edge === "hard") out.edge = "hard";
  return out;
}

// The brush row: its shapes, its edges and a square's angle (whichever the picked brush offers).
function renderBrushTip() {
  const w = mv.words, name = mv.brush.name, set = settingsOf(name), { shapes, edges } = tipChoices(name);
  const shapeOf = shapes.includes(set.shape) ? set.shape : "round";
  $("brush-shape").replaceChildren(...shapes.map((s) => chipOf(w[`brush_shape_${s}`] || s, w[`tip_brush_shape_${s}`],
    shapeOf === s, () => { set.shape = s; cancelRamp(); renderBrushTip(); if (s === "line") brushNote(w.brush_line_help); })));
  $("brush-edge").replaceChildren(...edges.map((e) => chipOf(w[`brush_edge_${e}`] || e, w[`tip_brush_edge_${e}`],
    (set.edge || "soft") === e, () => { set.edge = e; renderBrushTip(); })));
  $("brush-shape").classList.toggle("hidden", !shapes.length);
  $("brush-edge").classList.toggle("hidden", !edges.length);
  $("brush-angle-row").classList.toggle("hidden", shapeOf !== "square");
  $("brush-angle").value = set.angle;
  $("brush-angle-label").textContent = fill(w.brush_angle || "{deg}", { deg: set.angle });
}

// The brush picked draws a line: two clicks, where it starts and where it ends (as the ramp).
function drawsLine() {
  const name = mv.brush.name;
  return BRUSHES[name][0] === "ramp" || (tipChoices(name).shapes.length && settingsOf(name).shape === "line");
}

function brushNote(text, kind) {
  const note = $("brush-note");
  note.textContent = text || "";
  note.className = "small" + (kind === "error" ? " error-text" : "");
}

// The Erase brush is picked: Undo, Start over and the count then work on its circles, not on the strokes.
function erasing() {
  return BRUSHES[mv.brush.name][0] === "erase";
}

function showCount() {
  const w = mv.words, n = (erasing() ? mv.brush.erase : mv.brush.strokes).length;
  $("brush-count").textContent = n ? fill(erasing() ? w.erase_count : w.brush_count, { n: n.toLocaleString() }) : "";
  $("brush-undo").disabled = !n || !mv.brush.mod;
  $("brush-redo").disabled = !(erasing() ? redo.erase : redo.brush).length || !mv.brush.mod;
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
  if (mv.brush.on && erasing()) showTakes();
  else brushNote(res.mod ? (res.strokes.length ? mv.words.brush_note : "") : mv.words.no_mod);
}

// The size slider's name; the Erase brush's says how wide its circle is.
function sizeLabel() {
  const w = mv.words;
  // every brush's size in metres across on this map (the slider's number is a share of the map's width)
  $("brush-size-label").textContent = mv.edit
    ? fill(w.erase_size, { m: Math.round(2 * brushRadius(mv.brush.name) / METRE).toLocaleString() }) : w.brush_size;
}

// The strength slider in what it does: Map Paint's opacity; for Hill, Raise, Lower, Crater, Plateau and Water a
// height on this map (lift(): its share of the map's height range); for Flatten, Level, Smooth and Ramp how much of the
// way to the level one stroke goes
function strengthLabel() {
  const w = mv.words, name = mv.brush.name, [kind] = BRUSHES[name] || [], set = settingsOf(name);
  const label = $("brush-strength-label"), slider = $("brush-strength");
  const bounds = mv.edit && mv.edit.bounds;
  if (PAINT_KINDS.has(kind)) {
    label.textContent = fill(w.brush_opacity, { n: set.strength });
    slider.title = w.tip_brush_opacity;
  } else if ((kind === "add" || kind === "water" || name === "plateau") && bounds) {
    const m = lift(set.strength, bounds[2], bounds[5]) / METRE;
    label.textContent = fill(w.brush_strength_m || w.brush_strength,
      { m: (m >= 10 ? Math.round(m) : Math.round(m * 10) / 10).toLocaleString() });
    slider.title = w.tip_brush_strength_m || w.tip_brush_strength;
  } else if (kind === "level" || kind === "smooth" || kind === "ramp") {
    label.textContent = fill(w.brush_strength_pct || w.brush_strength, { n: set.strength });
    slider.title = w.tip_brush_strength_pct || w.tip_brush_strength;
  } else {
    label.textContent = w.brush_strength;
    slider.title = w.tip_brush_strength;
  }
}

// What the circles take when the mod is built, counted by the Studio the way the build erases
// (StudioApi.scenery_erased), again after each change; the last count asked for is the one said. Asked once the
// painting pauses (TAKES_WAIT), so a run of strokes costs one count, not one each (the Studio counts one at a time
// and stops an older count for a newer one: a count per stroke over a whole big map once ran it out of memory).
const TAKES_WAIT = 400;  // ms after the last change
async function countTakes(pack) {
  const b = mv.brush, ask = ++b.takesAsk;
  b.takes = b.erase.length ? "counting" : null;
  showTakes();
  if (!b.takes) return;
  await new Promise((done) => setTimeout(done, TAKES_WAIT));
  if (ask !== b.takesAsk || pack !== mv.current) return;  // another change came: its own count follows
  try {
    const res = await mv.api.scenery_erased(pack);
    if (ask !== b.takesAsk || pack !== mv.current || (res && res.superseded)) return;
    b.takes = res;
  } catch (err) {
    if (ask !== b.takesAsk || pack !== mv.current) return;
    b.takes = { failed: (err && err.message) || String(err) };
  }
  showTakes();
}

// The count, in the brush's note while the Erase brush is picked: "Trees 1,234 · Props 56", or why the build would
// refuse the circles (a map's scenery holds 16 MB at most, and erasing copies the blocks it changes).
const TAKES_ORDER = ["vegetation", "prop", "building", "decal", "bridge", "other"];
function showTakes() {
  const w = mv.words, b = mv.brush, t = b.takes;
  if (!b.on || !erasing()) return;
  if (!b.mod) { brushNote(w.no_mod, "error"); return; }
  if (!t) { brushNote(""); return; }
  if (t === "counting") { brushNote(w.erase_counting); return; }
  if (t.failed) { brushNote(t.failed, "error"); return; }
  if (t.error) { brushNote(fill(w.erase_refused, { why: t.error }), "error"); return; }
  const label = { vegetation: w.scenery_vegetation, prop: w.scenery_prop, building: w.scenery_building,
    decal: w.scenery_decal, bridge: w.dock_bridges, other: w.group_other };
  const list = TAKES_ORDER.filter((g) => t.takes[g]).map((g) => `${label[g]} ${t.takes[g].toLocaleString()}`).join(" · ");
  brushNote(list ? fill(w.erase_takes, { list }) : w.erase_takes_none);
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
  const set = settingsOf(b.name), erase = erasing(), painting = PAINT_KINDS.has(BRUSHES[b.name][0]);
  $("brush-size").value = set.size;
  typedBeside("brush-size", painting ? TYPED.paint : TYPED.size, () => settingsOf(b.name).size,
    (n) => { settingsOf(b.name).size = n; sizeLabel(); }, w.tip_brush_size);
  $("brush-strength").value = set.strength;
  $("brush-strength-row").classList.toggle("hidden",
    ["cover", "town", "block", "open", "forest", "erase"].includes(BRUSHES[b.name][0]));
  strengthLabel();  // (Map Paint's strength is how much each dab covers the ground's picture)
  sizeLabel();
  renderPaintPanel();
  $("brush-erase").classList.toggle("hidden", !erase);  // what the Erase brush's new circles take
  if (erase) {
    $("brush-erase-what").replaceChildren(...["vegetation", "prop", "building"].map((g) => chipOf(w[`scenery_${g}`],
      w.tip_erase_what, b.eraseWhat[g], () => { b.eraseWhat[g] = !b.eraseWhat[g]; renderBrushes(); })));
    $("brush-erase-whole").textContent = w.erase_whole;
    $("brush-erase-whole").title = w.tip_erase_whole;
    $("brush-erase-whole").disabled = !b.mod;
    $("brush-erase-trees").textContent = w.erase_trees_note;
    $("brush-erase-trees").classList.toggle("hidden", !b.eraseWhat.vegetation);
    $("brush-erase-buildings").textContent = w.erase_buildings_note;
    $("brush-erase-buildings").classList.toggle("hidden", !b.eraseWhat.building);
  }
  $("brush-water").classList.toggle("hidden", b.name !== "water");  // Water: a thin layer over the whole map
  $("brush-water-whole").textContent = w.water_whole;
  $("brush-water-whole").title = w.tip_water_whole;
  $("brush-water-whole").disabled = !b.mod;
  $("brush-repaint").classList.toggle("hidden", b.name !== "repaint");  // Paint by shape: a sandy shore or not
  $("brush-repaint-beach").textContent = w.repaint_beach;
  $("brush-repaint-beach").title = w.tip_repaint_beach;
  $("brush-repaint-beach").setAttribute("aria-pressed", String(paint.beach));
  $("brush-undo").title = erase ? w.tip_erase_undo : w.tip_brush_undo;
  $("brush-redo").title = erase ? w.tip_erase_redo : w.tip_brush_redo;
  $("brush-clear").title = erase ? w.tip_erase_clear : w.tip_brush_clear;
  renderBrushTip();
  sizeLabel();
  showOverlays();
  $("map-help").textContent = b.on ? w.brush_help : w.map_help;
  showCount();
}

function pickBrush(name) {
  const b = mv.brush, wasErasing = erasing();
  if (b.name !== name) { cancelRamp(); $("brush-sure").classList.add("hidden"); }  // its question was for the other
  b.name = name;
  dock.last[brushKind(name)] = name;
  setBrushMode(true);
  if (!b.mod) brushNote(mv.words.no_mod, "error");
  else if (name === "ramp") brushNote(mv.words.ramp_help);
  else if (erasing()) showTakes();
  else if (wasErasing) brushNote("");
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
  if (on) { toMode("map"); dock.check = false; stopRoad(); stopBridge(); }
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
  const busy = mv.brush.on || mv.place.on || (Boolean(scen.tool) && !FORM_TOOLS.has(scen.tool)) || road.on || bridge.on,
    M = gl.THREE.MOUSE;
  // the middle button turns the view in every mode (the wheel zooms), so the hand never has to change buttons
  gl.controls.mouseButtons = busy ? { LEFT: null, MIDDLE: M.ROTATE, RIGHT: M.PAN }
                                  : { LEFT: M.ROTATE, MIDDLE: M.ROTATE, RIGHT: M.PAN };
  if (!mv.brush.on && gl.ring) { gl.ring.visible = false; gl.squareRing.visible = false; gl.draw(); }
  if (gl.ring) gl.ring.material.color.setHex(mv.brush.on && erasing() ? 0xe0533d : 0xc8a64b);  // Erase's ring in red
  if (gl.ring && mv.brush.on && mv.brush.name === "paint") gl.ring.material.color.set(paint.colour);  // Colour's in its colour
  const zone = mv.brush.on && ZONE_RING[mv.brush.name];  // a zone brush's in the colour it paints
  if (gl.ring && zone) gl.ring.material.color.setRGB(...zone.slice(0, 3).map((v) => v / 255), gl.THREE.SRGBColorSpace);
  if (gl.townRings && !(mv.brush.on && mv.brush.name === "town") && gl.townRings.visible) { gl.townRings.visible = false; gl.draw(); }
  if (!mv.brush.on || mv.brush.name === "town") pointerTag(null, "");
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
  if (kind === "paint") { s.colour = paint.colour; s.weight = set.strength / 100; s.clear = paint.clear; }
  if (kind === "stamp" && paint.from !== "spot") {  // a texture picked: laid repeating (rusemod.groundtex)
    s.brush = "texture";
    s.texture = paint.texture;
    if (paint.texScale) s.size = Math.round(texturePeriod(paint.texture) * Math.pow(2, paint.texScale));
    if (paint.texTurn) s.turn = paint.texTurn;
    if (!paint.decals && paint.texture.startsWith("game:")) s.decals = false;
    s.weight = set.strength / 100;
    s.clear = paint.clear;
  } else if (kind === "stamp") {
    s.sx = paint.offset.sx; s.sy = paint.offset.sy; s.weight = set.strength / 100; s.clear = paint.clear;
  }
  if ((kind === "paint" || kind === "stamp") && paint.mask) s.mask = paint.mask;  // a brush that is a picture
  if ((kind === "paint" || kind === "stamp") && paint.dither) s.dither = true;    // a speckled edge
  if (kind === "repaint" && paint.beach) s.beach = true;   // sand round the new lakes (rusemod.repaint)
  if (kind !== "ramp") Object.assign(s, tipFields(name, end));
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
  const name = mv.brush.name, r = brushRadius(name) * SCALE, lift = r * 0.02;
  const square = tipChoices(name).shapes.length > 0 && settingsOf(name).shape === "square";
  gl.ring.visible = Boolean(p) && !square && name !== "town";  // Town rings the buildings it would cover instead
  gl.squareRing.visible = Boolean(p) && square;
  if (p) {
    gl.ring.position.set(p.x, p.y + lift, p.z);
    gl.ring.scale.set(r, r, r);
    gl.squareRing.position.set(p.x, p.y + lift, p.z);
    gl.squareRing.scale.set(r * Math.SQRT2, r * Math.SQRT2, r * Math.SQRT2);  // its corners are 1 out: its sides r
    // the scene's Z is the map's y (south): turning the drawing by -angle runs its sides along (cos a, sin a)
    gl.squareRing.rotation.set(-Math.PI / 2, 0, -settingsOf(name).angle * Math.PI / 180);
  }
  const start = mv.brush.rampStart;
  gl.startRing.visible = Boolean(start);
  gl.guide.visible = Boolean(start && p);
  if (start) {
    gl.startRing.position.set(start.sx, start.sy + lift, start.sz);
    gl.startRing.scale.set(r, r, r);
  } else if (name === "stamp" && p && paint.from === "spot" && (paint.offset || paint.source)) {  // where it copies from
    const sx = paint.offset ? p.x + paint.offset.sx * SCALE : paint.source.x * SCALE;
    const sz = paint.offset ? p.z + paint.offset.sy * SCALE : paint.source.y * SCALE;
    gl.startRing.visible = true;
    gl.startRing.position.set(sx, p.y + lift, sz);
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
  if (group.erase) {  // an Erase drag: a circle taking what's picked, shown on the overlays and on what it takes
    const r = Math.min(ERASE_MAX, Math.max(1, Math.round(brushRadius(mv.brush.name))));
    const a = { x: Math.round(x), y: Math.round(y), radius: r, what: group.what };
    const tip = tipFields(mv.brush.name, group.end && { x: Math.round(group.end.x), y: Math.round(group.end.y) });
    if (tip.shape) Object.assign(a, tip);  // a square turned any way, or a line to where the second click was
    group.erase.push(a);
    group.last = [x, y];
    mv.brush.erase.push(a);
    eraseDab(a);
    tintSoon();
    return;
  }
  const s = newStroke(x, y, group.level, group.end);
  if (!group.strokes.length && PAINTS[s.brush]) countZone(s.brush);  // a zone stroke: what it changes is said at its end
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
  // dabs along the drag: closer for the ground brushes (a smooth ridge); Map Paint's at half their radius, as each
  // dab builds the colour up where they overlap
  const first = g.erase ? g.erase[0] : g.strokes[0];
  const x = p.x / SCALE, y = p.z / SCALE, spacing = g.erase || PAINT_KINDS.has(first.brush) ? first.radius / 2 : first.radius / 3;
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
  const zone = zoneCount;  // what a zone stroke changed, counted now (another stroke may start while this one saves)
  zoneCount = null;
  if (g && g.erase) { finishErase(g); return; }
  if (!g || !g.strokes.length) return;
  const said = zone ? zoneSaid(zone) : "";
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
    redo.brush = [];
    // cover or movement painted where an Erase circle clears a wood: the build clears it after, so the view does too
    if (g.strokes.some((s) => PAINTS[s.brush]) && mv.brush.erase.some(clearsWood)) refreshErased();
    showCount();
    // what it did, in the tray and at the pointer: a zone stroke's change for units (Town's buildings, Forest's
    // trees first), else that it's saved
    const lead = g.town ? fill(mv.words.town_done, { n: g.town.toLocaleString() })
      : g.objects ? fill(mv.words.forest_done, { n: trees.length.toLocaleString() }) : "";
    const text = [lead, said].filter(Boolean).join(" ");
    brushNote(text ? `${text} ${mv.words.brush_note}` : mv.words.brush_note);
    if (text) pointerTag(null, text, false, 5000);
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

// An Erase drag's circles, saved after the others in the mod's scenery file (StudioApi.scenery_erase), its objects
// kept; not saved, they leave the view again.
async function finishErase(g) {
  const b = mv.brush, pack = mv.current;
  if (!g.erase.length) return;
  try {
    await mv.api.scenery_erase(pack, g.erase);
    if (pack !== mv.current) return;
    b.eraseGroups.push(g.erase.length);
    redo.erase = [];
    showCount();
    countTakes(pack);
  } catch (err) {
    if (pack !== mv.current) return;
    const gone = new Set(g.erase);
    b.erase = b.erase.filter((a) => !gone.has(a));
    refreshErased();
    showCount();
    brushNote((err && err.message) || String(err), "error");
  }
}

// "Erase the whole map": one square over all of it, taking what's picked (the owner, 2026-10-04: "a simple optimized
// way to just erase the whole map in one button"), saved like a drag's circles, so Undo takes it back. The build and
// the count take a whole-map area at once (rusemod.scenery.erase_plan's bulk): seconds, even on M04_Cotentin.
async function eraseWhole() {
  const b = mv.brush;
  if (!b.mod || b.painting || !mv.edit) return;
  const what = ["vegetation", "prop", "building"].filter((g) => b.eraseWhat[g]);
  if (!what.length) { brushNote(mv.words.erase_none, "error"); return; }
  const [x0, y0, , x1, y1] = mv.edit.bounds;
  const radius = Math.min(ERASE_MAX, Math.ceil(Math.max(x1 - x0, y1 - y0) / 2) + 1000);
  const a = { x: Math.round((x0 + x1) / 2), y: Math.round((y0 + y1) / 2), radius, what, shape: "square", dx: 1, dy: 0 };
  b.erase.push(a);
  eraseDab(a);
  tintSoon();
  await finishErase({ erase: [a] });
}

// "Water over the whole map": one square of water over all of it, its surface Strength above the ground's middle
// height (the median of the ground as the view has it, the mod's strokes on it), a thin layer units go under (block =
// false: the build takes its place for dry ground). The owner's navy, 2026-10-05: "spread the water across the whole
// map". Saved like a drag's stroke, so Undo takes it back.
async function waterWhole() {
  const b = mv.brush, ed = mv.edit;
  if (!b.mod || b.painting || !ed) return;
  const [x0, y0, z0, x1, y1, z1] = ed.bounds;
  const zs = Float64Array.from(ed.z).sort();
  const level = zs[Math.floor(zs.length / 2)] + lift(settingsOf("water").strength, z0, z1);
  const s = { brush: "water", x: Math.round((x0 + x1) / 2), y: Math.round((y0 + y1) / 2),
    radius: Math.ceil(Math.max(x1 - x0, y1 - y0) / 2) + 1000, shape: "square", dx: 1, dy: 0, level, block: false };
  b.painting = { strokes: [s], last: null, start: b.strokes.length };
  b.strokes.push(s);
  reapply();
  await finishStroke();
}

// Undo under the Erase brush: the last drag's circles (one circle, for those saved before this session).
async function undoErase() {
  const b = mv.brush, pack = mv.current;
  if (!b.mod || !b.erase.length || b.painting) return;
  const n = b.eraseGroups.length ? b.eraseGroups.pop() : 1;
  try {
    const res = await mv.api.scenery_erase_undo(pack, n);
    if (pack !== mv.current) return;
    const gone = b.erase.splice(b.erase.length - res.removed, res.removed);
    if (gone.length) redo.erase.push(gone);
    refreshErased();
    showCount();
    countTakes(pack);
  } catch (err) { brushNote((err && err.message) || String(err), "error"); }
}

// Redo under the Erase brush: the last drag's circles Undo took back, saved again.
async function redoErase() {
  const b = mv.brush, pack = mv.current;
  if (!b.mod || b.painting || !redo.erase.length) return;
  const circles = redo.erase.pop();
  try {
    await mv.api.scenery_erase(pack, circles);
    if (pack !== mv.current) return;
    b.erase.push(...circles);
    b.eraseGroups.push(circles.length);
    refreshErased();
    showCount();
    countTakes(pack);
  } catch (err) {
    if (pack !== mv.current) return;
    redo.erase.push(circles);
    brushNote((err && err.message) || String(err), "error");
  }
}

// "Start over" under the Erase brush: every circle on this map goes; the map keeps all its own scenery.
async function clearErase() {
  const b = mv.brush, pack = mv.current;
  if (!b.mod || !b.erase.length || b.painting) return;
  try {
    await mv.api.scenery_erase_undo(pack, b.erase.length);
    if (pack !== mv.current) return;
    b.erase = [];
    b.eraseGroups = [];
    redo.erase = [];
    refreshErased();
    showCount();
    countTakes(pack);
  } catch (err) { brushNote((err && err.message) || String(err), "error"); }
}

// Undo takes back the last stroke or drag; a Forest stroke's trees go with its cover.
async function undoStroke() {
  const b = mv.brush, pack = mv.current;
  if (erasing()) { undoErase(); return; }
  if (!b.mod || !b.strokes.length || b.painting) return;
  const last = b.groups.length ? b.groups.pop() : 1, n = typeof last === "number" ? last : last.n;
  try {
    const res = await mv.api.terrain_undo(pack, n);
    if (pack !== mv.current) return;
    const strokes = b.strokes.splice(b.strokes.length - res.removed, res.removed);
    const trees = last.objects && last.objects.length ? last.objects : null;
    if (trees) {
      await mv.api.scenery_undo(pack, trees.length, trees);
      if (pack !== mv.current) return;
      takeOff(trees);
      renderPlace();
    }
    if (strokes.length) redo.brush.push({ strokes, objects: trees });
    reapply();
    showCount();
  } catch (err) { brushNote((err && err.message) || String(err), "error"); }
}

// Redo under a brush: the last stroke or drag Undo took back, saved again (a Forest stroke's trees with its cover,
// both or neither, as when it was painted).
async function redoStroke() {
  const b = mv.brush, pack = mv.current;
  if (erasing()) { redoErase(); return; }
  if (!b.mod || b.painting || !redo.brush.length) return;
  const g = redo.brush.pop(), trees = g.objects || [];
  let placed = false;
  try {
    if (trees.length) {
      await mv.api.scenery_add(pack, trees);
      placed = true;
    }
    await mv.api.terrain_add(pack, g.strokes);
    if (pack !== mv.current) return;
    b.strokes.push(...g.strokes);
    if (trees.length) {
      for (const o of trees) forestTrees.add(o);
      mv.place.objects.push(...trees);
      b.groups.push({ n: g.strokes.length, objects: trees });
      drawPlaced();
      renderPlace();
    } else {
      b.groups.push(g.strokes.length);
    }
    reapply();
    showCount();
  } catch (err) {
    if (placed) { try { await mv.api.scenery_undo(pack, trees.length, trees); } catch (_) { /* said below */ } }
    if (pack !== mv.current) return;
    redo.brush.push(g);
    brushNote((err && err.message) || String(err), "error");
  }
}

// "Start over": every stroke on this map goes (after the question under the button).
async function clearStrokes() {
  const b = mv.brush, pack = mv.current;
  $("brush-sure").classList.add("hidden");
  if (erasing()) { clearErase(); return; }
  if (!b.mod || !b.strokes.length || b.painting) return;
  try {
    await mv.api.terrain_undo(pack, b.strokes.length);
    if (pack !== mv.current) return;
    b.strokes = [];
    b.groups = [];
    redo.brush = [];
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
    const was = mv.brush.lastPointer;
    if (!was || Math.hypot(pending.clientX - was.clientX, pending.clientY - was.clientY) > HOLD_STILL) {
      mv.brush.movedAt = performance.now();  // (holding still builds the dab up: holdBuildUp)
    }
    mv.brush.lastPointer = { clientX: pending.clientX, clientY: pending.clientY };  // where a stroke's count is said
    showRing(p);
    showShade(p);
    if (mv.brush.name === "town") showTownPreview(p, pending);
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
    if (paintPick(x, y, ev.altKey, ev)) return;  // Map Paint: the eyedropper, or Texture's spot to copy from (or Alt+click)
    if (kind === "stamp" && paint.from !== "spot") {  // Texture with a texture picked
      if (!paint.texture) { brushNote(mv.words.tex_none_picked, "error"); return; }
      textureUsed(paint.texture);
    } else if (kind === "stamp") {  // Texture copies from the spot picked: the first stroke after picking fixes the offset
      if (!paint.offset && !paint.source) { brushNote(mv.words.stamp_from_none, "error"); return; }
      if (!paint.offset || paint.source) {
        const start = drawsLine() && mv.brush.rampStart ? mv.brush.rampStart : { x, y };
        paint.offset = { sx: Math.round(paint.source.x - start.x), sy: Math.round(paint.source.y - start.y) };
        paint.source = null;
        if (!paint.offset.sx && !paint.offset.sy) { paint.offset = null; brushNote(mv.words.stamp_same, "error"); return; }
        renderPaintPanel();
      }
    }
    if (kind === "paint") rememberColour(paint.colour);
    if (kind === "town") {  // one click: cover circles around the town's buildings, saved as one group
      const strokes = townStrokes(x, y, pixelsAt(p, TOWN_POINTER));
      if (!strokes.length) { brushNote(mv.words.town_none, "error"); pointerTag(ev, mv.words.town_none, true, 4000); return; }
      const group = { strokes: [], last: null, stamp: true, start: mv.brush.strokes.length, town: strokes.length };
      if (gl.townRings) gl.townRings.visible = false;  // the cover it makes shows instead (showTownPreview)
      mv.brush.townClicked = { clientX: ev.clientX, clientY: ev.clientY };
      countZone("town");
      for (const s of strokes) { group.strokes.push(s); mv.brush.strokes.push(s); overlayDab(s); }
      mv.brush.painting = group;
      finishStroke();
      return;
    }
    const what = ["vegetation", "prop", "building"].filter((g) => mv.brush.eraseWhat[g]);
    if (kind === "erase" && !what.length) { brushNote(mv.words.erase_none, "error"); return; }
    if (drawsLine()) {  // two clicks: where it starts (the ground's height there), then where it ends: a ramp, or any
      const start = mv.brush.rampStart;  // brush drawn as a line (a ridge, a ditch, a hedge of cover, a wall, a strip)
      if (!start) {
        mv.brush.rampStart = { x, y, z, level, sx: p.x, sy: p.y, sz: p.z };
        showRing(p);
        if (kind !== "ramp") brushNote(mv.words.brush_line_next);
        return;
      }
      if (start.x === x && start.y === y) return;
      mv.brush.rampStart = null;
      showRing(p);
      const end = { x, y, z };
      const line = kind === "erase" ? { strokes: [], erase: [], what, last: null, stamp: true, end }
        : { strokes: [], last: null, level: kind === "ramp" ? start.z : start.level, stamp: true,
            start: mv.brush.strokes.length, end };
      mv.brush.painting = line;
      dab(line, start.x, start.y);
      finishStroke();
      return;
    }
    if (kind === "erase") {  // circles along the drag, each taking what's picked (trees and props to start with)
      mv.brush.painting = { strokes: [], erase: [], what, last: null, stamp: false };
      dab(mv.brush.painting, x, y);
      canvas.setPointerCapture(ev.pointerId);
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
    if (!stamp && (kind === "paint" || kind === "stamp")) {  // Map Paint: holding still lays more (holdBuildUp)
      mv.brush.movedAt = performance.now();
      holdBuildUp(group);
      showShade(null);
    }
  });
  for (const type of ["pointerup", "pointercancel"]) {
    canvas.addEventListener(type, () => { if (mv.brush.painting) finishStroke(); });
  }
  canvas.addEventListener("pointerdown", scenPointerDown);
  watchSectorPointer(canvas);  // the Sectors brush's drag and ring
  // Drag to move: listened for on the map's frame, before the view's own handlers (capture), so a press on an item
  // grabs it instead of turning the view; the frame keeps the pointer until the button's let go.
  const host = canvas.parentElement;
  host.addEventListener("pointerdown", (ev) => { grabStart(ev); }, { capture: true });
  let dragEv = null, dragFrame = 0;
  host.addEventListener("pointermove", (ev) => {
    if (scen.box) { boxMove(ev); return; }  // a selection box being dragged (Move, on the ground)
    if (!scen.camDrag && !scen.itemDrag) {  // over something it could grab: the hand
      if (canGrab() && !ev.buttons) canvas.style.cursor = grabAt(ev) ? "grab" : (scen.tool ? "crosshair" : "");
      return;
    }
    dragEv = ev;
    if (!dragFrame) dragFrame = requestAnimationFrame(() => {
      dragFrame = 0;
      if (scen.camDrag && dragEv) camDragMove(dragEv);
      else if (scen.itemDrag && dragEv) itemDragMove(dragEv);
    });
  });
  for (const type of ["pointerup", "pointercancel"]) {
    host.addEventListener(type, () => {
      if (scen.box) boxEnd();
      else if (scen.camDrag) camDragEnd();
      else if (scen.itemDrag) itemDragEnd();
    });
  }
  canvas.addEventListener("pointerdown", roadPointerDown);
  canvas.addEventListener("pointerdown", (ev) => {
    if (!bridge.on || ev.button !== 0 || !gl.ground || !mv.edit) return;
    ev.preventDefault();
    bridgeAt(ev);
  });
  let bridgeMove = null, bridgeFrame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    if (!bridge.on) return;
    bridgeMove = ev;
    if (!bridgeFrame) bridgeFrame = requestAnimationFrame(() => { bridgeFrame = 0; if (bridge.on && bridgeMove) bridgePointerMove(bridgeMove); });
  });
  canvas.addEventListener("pointerleave", () => { if (bridge.on && bridge.cursor) { bridge.cursor = null; drawBridges(); } });
  let roadMove = null, roadFrame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    if (!road.on) return;
    roadMove = ev;
    if (!roadFrame) roadFrame = requestAnimationFrame(() => { roadFrame = 0; if (road.on && roadMove) roadPointerMove(roadMove); });
  });
  canvas.addEventListener("dblclick", () => {  // a place tray's Path ends with a double-click (its clicks: one point)
    const pp = mv.place.on && mv.place.how === "path" && mv.place.path;
    if (!pp) return;
    const q = pp.pts;
    if (q.length >= 2 && Math.hypot(q[q.length - 1][0] - q[q.length - 2][0], q[q.length - 1][1] - q[q.length - 2][1]) < ROAD_SAMPLE) q.pop();
    finishPath();
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
    if (p.how === "select") { if (selPointerDown(ev)) canvas.setPointerCapture(ev.pointerId); return; }
    if (p.how === "one") { placeAt(ev); return; }
    const w = mv.words;
    if (!p.mod) { placeNote(w.no_mod, "error"); return; }
    if (!p.type) { placeNote(whyNoType(), "error"); return; }
    const hit = hitGround(ev);
    if (!hit) { placeNote(w.place_ground, "error"); return; }
    const x = hit.x / SCALE, y = hit.z / SCALE;
    if (p.how === "line" || p.how === "grid") {  // where it starts, where it ends (a grid: then how far its rows go)
      if (!p.lineStart) {
        p.lineStart = { x, y, sx: hit.x, sy: hit.y, sz: hit.z };
        p.seed = newSeed();
        placeNote(p.how === "grid" ? w.place_grid_next : w.place_line_next);
        showPlaceGhost(null);
        showPlaceGuide(hit);
        placePreview(hit);
        return;
      }
      if (p.how === "grid" && !p.grid) {
        p.grid = { b: { x, y } };
        showPlaceGuide(hit);
        placePreview(hit);
        placeNote(w.place_grid_rows);
        return;
      }
      const objs = p.how === "grid" ? gridOf(p.lineStart, p.grid.b, { x, y }) : lineOf(p.lineStart, { x, y });
      dropPlaceGesture();
      placeMany(objs);
      return;
    }
    if (p.how === "path") {  // a path: a point each click, until a double-click, Enter or Finish
      if (!p.path) { p.path = { pts: [] }; p.seed = newSeed(); }
      p.path.pts.push([Math.round(x), Math.round(y)]);
      showPlaceGhost(null);
      placePreview(hit);
      placeNote(w.place_path_next);
      renderPlace();
      return;
    }
    if (p.how === "box") {  // a box: from here to where the button's let go
      p.box = { a: { x, y }, b: { x, y } };
      p.seed = newSeed();
      placePreview(hit);
      canvas.setPointerCapture(ev.pointerId);
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
    if (!p.on) return;
    placeMove = ev;
    if (placeFrame) return;
    placeFrame = requestAnimationFrame(() => {
      placeFrame = 0;
      if (p.how === "select") { if (placeMove) selPointerMove(placeMove); return; }  // a drag moving, or a box
      const hit = placeMove && hitGround(placeMove);
      showPlaceGhost(hit);  // what a click places, where it would stand
      if (p.how === "one") return;
      showPlaceGuide(hit);
      if (p.lineStart || p.box || p.path) { if (hit) placePreview(hit); return; }  // a line, path, grid or box under way
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
      if (sel.drag || sel.box) { selPointerUp(); return; }  // Select's drag or box ends
      const p = mv.place, stroke = p.painting;
      if (p.box) {  // a box let go: filled
        const objs = fillBox(p.box.a, p.box.b);
        dropPlaceGesture();
        placeMany(objs);
        return;
      }
      if (!stroke) return;
      p.painting = null;
      placeMany(stroke.objects);
    });
  }
  let spawnMove = null, spawnFrame = 0;
  canvas.addEventListener("pointermove", (ev) => {
    if (!spawningNow()) return;
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
      // the side the bar is on is said first; a locked object of the map says where to go to change it
      const said = () => {
        const t = sceneryAt(hoverEv);
        return t ? `${t[0]} · ${t[2] || t[1]}` + (mv.mode !== "map" && mv.words.locked_map ? ` · ${mv.words.locked_map}` : "") : "";
      };
      $("scenery-hover").textContent = mv.mode === "map" ? said() || scenarioAt(hoverEv) : scenarioAt(hoverEv) || said();
    });
  });
  canvas.addEventListener("pointerleave", () => {
    if (mv.brush.on && gl.ring) { gl.ring.visible = false; gl.squareRing.visible = false; gl.draw(); }
    if (gl.townRings && gl.townRings.visible) { gl.townRings.visible = false; pointerTag(null, ""); gl.draw(); }
    if (gl.ghost && gl.ghost.visible) showPlaceGhost(null);
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
  // "New map: start from scratch…" shows once the game's maps are known and no map is open (its words: renderWords)
  $("map-scratch").classList.toggle("hidden", Boolean(mv.current) || !shippedMaps().length);
  const shown = mv.kind && mv.kind !== "all" ? mv.maps.filter((m) => (m.kinds || []).includes(mv.kind)) : mv.maps;
  $("map-list").replaceChildren(...shown.map((m) => {
    const names = menuNames(m);
    const sub = m.copy_of ? fill(mv.words.map_copy_of || "{map}", { map: mapName(m.copy_of) })
      : (names.length ? names.slice(1) : m.names).join(" · ");
    const b = el("button", { type: "button", title: fill(mv.words.tip_open_map || "{file}", { file: m.file }) },
      el("span", { className: "name" }, ...nameLine(m)),
      el("span", { className: "sub", textContent: sub }));
    b.setAttribute("aria-current", String(m.pack === mv.current));
    b.addEventListener("click", () => show(m.pack));
    return el("li", null, b);
  }));
}

function showTitle() {
  const m = mv.maps.find((x) => x.pack === mv.current);
  if (mv.current) $("map-title").replaceChildren(...(m ? nameLine(m) : [mv.current]));
  renderDelete();
}

// --- Delete map: a new map's folder to the Recycle Bin (StudioApi.delete_map) after one "are you sure"; the game's own
// maps have no such button. The map it copied opens in its place. ---
function renderDelete() {
  const w = mv.words, m = mv.maps.find((x) => x.pack === mv.current);
  const mine = Boolean(m && m.copy_of), asking = mine && mv.deleteAsk === mv.current;
  $("map-picture").classList.toggle("hidden", !mv.current);  // its pictures in the menus (openMenuPictures)
  $("map-picture").textContent = w.map_picture;
  $("map-picture").title = w.tip_map_picture;
  $("map-size-open").classList.toggle("hidden", !mine);  // a new map's size (openMapSize: it says when it can't)
  $("map-size-open").textContent = w.map_size_btn;
  $("map-size-open").title = w.tip_map_size_btn;
  $("map-sound").classList.toggle("hidden", !mv.current || !window.SoundView);  // its background sound (sound.js)
  $("map-sound").textContent = w.map_sound_btn;
  $("map-sound").title = w.tip_map_sound;
  $("map-delete").classList.toggle("hidden", !mine || asking);
  $("map-delete-sure").classList.toggle("hidden", !asking);
  $("map-delete").textContent = w.delete_map;
  $("map-delete").title = w.tip_delete_map;
  if (!$("map-delete-yes").disabled) $("map-delete-ask").textContent = fill(w.really_delete_map, { name: m ? mapName(m.pack) : "" });
  $("map-delete-yes").textContent = w.delete_map;
  $("map-delete-yes").title = w.tip_delete_map;
  $("map-delete-no").textContent = w.cancel;
  $("map-delete-no").title = w.tip_cancel;
}

// --- Menu pictures: the map's two pictures in the game's menus (map.toml picture, wide_picture, start_dots;
// rusemod.menupicture): the big one, and the 3D map with a white dot where each player starts, which the build draws
// where the starting points are. A PNG picked for either, both made in Blender from the map's own 3D model, or the
// game's own; any map's, a shipped one's too (a themed mod). The owner, 2026-10-05: "the option for a custom PNG or
// model and then also being able to make your own". ---
const mp = { pack: null, busy: false };

async function openMenuPictures() {
  const w = mv.words, pack = mv.current;
  if (!pack) return;
  mp.pack = pack;
  $("mp-title").textContent = w.menu_pics_title;
  $("mp-lead").textContent = fill(w.menu_pics_lead, { map: mapName(pack) });
  $("mp-big-title").textContent = w.menu_big;
  $("mp-wide-title").textContent = w.menu_wide;
  for (const k of ["big", "wide"]) {
    $(`mp-${k}-pick`).textContent = w.menu_pick;
    $(`mp-${k}-pick`).title = w.tip_menu_pick;
    $(`mp-${k}-game`).textContent = w.menu_back;
    $(`mp-${k}-game`).title = w.tip_menu_back;
  }
  $("mp-dots-label").textContent = w.menu_dots;
  $("mp-dots").parentElement.title = w.tip_menu_dots;
  $("mp-blender-title").textContent = w.menu_blender_title;
  $("mp-blender-how").textContent = w.menu_blender_how;
  $("mp-blender").textContent = w.menu_blender;
  $("mp-bring").textContent = w.menu_bring_back;
  $("mp-bring").title = w.tip_menu_bring_back;
  $("mp-fresh").textContent = w.menu_fresh;
  $("mp-fresh").title = w.tip_menu_fresh;
  $("mp-close").textContent = w.close;
  $("mp-note").textContent = "";
  $("mp-shared").textContent = "";
  for (const id of ["mp-big-img", "mp-wide-img"]) $(id).removeAttribute("src");
  $("menu-pics").showModal();
  await menuPicturesCall(() => mv.api.menu_pictures(pack));
}

// One call of the window's (StudioApi.menu_pictures and the calls that change the pictures), the buttons held while
// it runs, its answer shown; a ground picture still being made for Blender is waited for, then asked again.
async function menuPicturesCall(call, again) {
  const w = mv.words, pack = mp.pack;
  if (mp.busy) return;
  mp.busy = true;
  renderMenuPicturesBusy(true);
  try {
    let res = await call();
    while (res && res.job && again) {  // the map's ground picture for Blender, made once (about half a minute)
      let view, since = 0;
      do {
        await wait(700);
        view = await mv.api.job(res.job, since);
        since = view.count;
        if (view.lines.length) $("mp-note").textContent = fill(w.ground_loading, { progress: view.lines[view.lines.length - 1] });
      } while (view.state === "running");
      if (view.state !== "done") throw new Error(view.message);
      res = await again();
    }
    if (pack === mp.pack && res && res.pictures) renderMenuPictures(res);
    $("mp-note").textContent = (res && res.message) || "";
  } catch (err) {
    $("mp-note").textContent = (err && err.message) || String(err);
  }
  mp.busy = false;
  renderMenuPicturesBusy(false);
}

function renderMenuPicturesBusy(busy) {
  for (const id of ["mp-big-pick", "mp-big-game", "mp-wide-pick", "mp-wide-game", "mp-dots", "mp-blender", "mp-bring",
    "mp-fresh"]) $(id).disabled = busy || $(id).dataset.off === "1";
}

function renderMenuPictures(res) {
  const w = mv.words;
  mp.res = res;
  for (const p of res.pictures) {
    const k = p.key === "picture" ? "big" : "wide";
    if (p.url) $(`mp-${k}-img`).src = p.url; else $(`mp-${k}-img`).removeAttribute("src");
    $(`mp-${k}-img`).alt = k === "big" ? w.menu_big : w.menu_wide;
    $(`mp-${k}-file`).textContent = p.own ? fill(w.menu_own_file, { file: p.file }) : w.menu_game_own;
    $(`mp-${k}-game`).dataset.off = p.own ? "0" : "1";
  }
  const wide = res.pictures.find((p) => p.key === "wide_picture");
  $("mp-dots").checked = Boolean(res.start_dots);
  $("mp-dots").dataset.off = wide && wide.own ? "0" : "1";
  $("mp-blender").dataset.off = res.blender ? "0" : "1";
  $("mp-blender").title = res.blender ? w.tip_menu_blender : w.menu_no_blender;
  $("mp-bring").dataset.off = res.saved ? "0" : "1";
  $("mp-fresh").dataset.off = res.scene && res.blender ? "0" : "1";
  $("mp-shared").textContent = res.shared && res.shared.length ? fill(w.menu_shared, { entries: res.shared.join(", ") }) : "";
  renderMenuPicturesBusy(false);
}

function wireMenuPictures() {
  const pack = () => mp.pack;
  $("mp-big-pick").addEventListener("click", () => menuPicturesCall(() => mv.api.pick_menu_picture(pack(), "picture")));
  $("mp-wide-pick").addEventListener("click", () => menuPicturesCall(() => mv.api.pick_menu_picture(pack(), "wide_picture")));
  $("mp-big-game").addEventListener("click", () => menuPicturesCall(() => mv.api.clear_menu_picture(pack(), "picture")));
  $("mp-wide-game").addEventListener("click", () => menuPicturesCall(() => mv.api.clear_menu_picture(pack(), "wide_picture")));
  $("mp-dots").addEventListener("change", (e) => menuPicturesCall(() => mv.api.set_start_dots(pack(), e.target.checked)));
  const blender = (fresh) => menuPicturesCall(() => mv.api.menu_pictures_blender(pack(), fresh),
    () => mv.api.menu_pictures_blender(pack(), false));
  $("mp-blender").addEventListener("click", () => blender(false));
  $("mp-fresh").addEventListener("click", () => blender(true));
  $("mp-bring").addEventListener("click", () => menuPicturesCall(() => mv.api.menu_pictures_bring_back(pack())));
  $("mp-close").addEventListener("click", () => $("menu-pics").close());
  $("menu-pics").addEventListener("keydown", (e) => e.stopPropagation());  // keys never move the map behind it
}

// --- Map size (StudioApi.map_size / set_map_size, map.toml size; rusemod.bigmap grows the map in the build): a blank
// new map made bigger or smaller a strip at a time, on any side (the owner, 2026-10-17: "add a tile in like a
// direction", the way Cities: Skylines buys land). A strip is two of the game's squares wide (the far view draws them
// two by two). The sides are drawn as the top view shows the map: its first x side on the left, its first y side at
// the top; a strip there moves everything the mod placed, so it stays on the same ground. Made at once, on Make it. ---
const msz = { pack: null, data: null, left: 0, top: 0, right: 0, bottom: 0, busy: false, note: "", bad: false };
const SQUARE_KM = 327680 / 260 / 1000;   // one of the game's squares (rusemod.bigmap.CASE), in km
const SIZE_SIDES = ["left", "top", "right", "bottom"];

async function openMapSize() {
  const pack = mv.current;
  if (!pack) return;
  Object.assign(msz, { pack, data: null, left: 0, top: 0, right: 0, bottom: 0, busy: false, note: "", bad: false });
  renderMapSize();
  $("map-size").showModal();
  try {
    const got = await mv.api.map_size(pack);
    if (msz.pack !== pack) return;
    msz.data = got;
  } catch (err) {
    msz.note = (err && err.message) || String(err);
    msz.bad = true;
  }
  renderMapSize();
}

function sizeWanted(extra) {   // [across, down] with the strips asked for (and `extra` {side: strips} more)
  const d = msz.data, e = extra || {}, t = d.tile;
  const n = (k) => msz[k] + (e[k] || 0);
  return [d.cells[0] + t * (n("left") + n("right")), d.cells[1] + t * (n("top") + n("bottom"))];
}

function sizeFits(extra) {
  const d = msz.data, [a, b] = sizeWanted(extra);
  return a >= d.tile && b >= d.tile && a <= d.most && b <= d.most;
}

function sizeWords(cells) {
  return fill(mv.words.size_now, { a: cells[0], b: cells[1], x: (cells[0] * SQUARE_KM).toFixed(1),
    y: (cells[1] * SQUARE_KM).toFixed(1) });
}

function renderMapSize() {
  const w = mv.words, d = msz.data, can = Boolean(d && d.can) && Boolean(mv.brush.mod) && !msz.busy;
  const why = d && d.why ? w[`size_why_${d.why}`] || d.why : "";   // why it can't change size (StudioApi.map_size)
  const strip = d ? d.tile * SQUARE_KM : 2 * SQUARE_KM;
  $("size-title").textContent = w.size_title;
  $("size-lead").textContent = fill(w.size_lead, { km: SQUARE_KM.toFixed(2), strip: strip.toFixed(1) });
  $("size-how").textContent = w.size_how;
  const changed = Boolean(d) && SIZE_SIDES.some((k) => msz[k]);
  for (const k of SIZE_SIDES) {
    for (const [what, by] of [["add", 1], ["cut", -1]]) {
      const b = $(`size-${k}-${what}`), fits = Boolean(d) && sizeFits({ [k]: by });
      b.textContent = by > 0 ? "+" : "−";
      b.disabled = !can || !fits;
      b.title = !d || can ? (fits || !d ? fill(w[`tip_size_${what}`], { km: strip.toFixed(1) })
        : fill(by > 0 ? w.tip_size_most : w.tip_size_least, { most: d.most, tile: d.tile })) : (why || w.no_mod);
      b.onclick = () => { msz[k] += by; msz.note = ""; renderMapSize(); };
    }
  }
  const all = (id, word, tip, by) => {
    const b = $(id), fits = Boolean(d) && sizeFits(Object.fromEntries(SIZE_SIDES.map((k) => [k, by])));
    b.textContent = word;
    b.title = tip;
    b.disabled = !can || !fits;
    b.onclick = () => { for (const k of SIZE_SIDES) msz[k] += by; msz.note = ""; renderMapSize(); };
  };
  all("size-all-add", w.size_all_add, w.tip_size_all_add, 1);
  all("size-all-cut", w.size_all_cut, w.tip_size_all_cut, -1);
  const back = $("size-back");
  back.textContent = w.size_back;
  back.title = w.tip_size_back;
  back.disabled = !changed || msz.busy;
  back.onclick = () => { for (const k of SIZE_SIDES) msz[k] = 0; msz.note = ""; renderMapSize(); };
  $("size-readout").textContent = !d ? w.size_reading : changed
    ? fill(w.size_change, { now: sizeWords(d.cells), then: sizeWords(sizeWanted()) }) : sizeWords(d.cells);
  const apply = $("size-apply");
  apply.textContent = w.size_apply;
  apply.title = !mv.brush.mod ? w.no_mod : why || w.tip_size_apply;
  apply.disabled = !can || !changed;
  $("size-close").textContent = w.close;
  const note = $("size-note");
  const said = msz.note || why || (!mv.brush.mod ? w.no_mod : "");
  note.textContent = said;
  note.className = "small" + (msz.bad || (d && !d.can) || !mv.brush.mod ? " error-text" : "");
  drawMapSize();
}

// The map as it is (a dashed outline) and as it will be (the ground, with a faint line every strip), both fitted in.
function drawMapSize() {
  const c = $("size-canvas"), ctx = c.getContext("2d"), d = msz.data;
  ctx.clearRect(0, 0, c.width, c.height);
  if (!d) return;
  const t = d.tile, [a, b] = sizeWanted();
  const nx0 = -t * msz.left, ny0 = -t * msz.top;             // the new map's corner, in the old map's squares
  const ux0 = Math.min(0, nx0), uy0 = Math.min(0, ny0);
  const ux1 = Math.max(d.cells[0], nx0 + a), uy1 = Math.max(d.cells[1], ny0 + b);
  const pad = 16, k = Math.min((c.width - 2 * pad) / (ux1 - ux0), (c.height - 2 * pad) / (uy1 - uy0));
  const ox = (c.width - k * (ux1 - ux0)) / 2 - k * ux0, oy = (c.height - k * (uy1 - uy0)) / 2 - k * uy0;
  const X = (x) => ox + k * x, Y = (y) => oy + k * y;
  ctx.fillStyle = "#4b6a3c";
  ctx.fillRect(X(nx0), Y(ny0), k * a, k * b);
  if (k * t >= 3) {   // a line every strip, while they're far enough apart to see
    ctx.strokeStyle = "rgba(255, 255, 255, 0.12)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let i = t; i < a; i += t) { ctx.moveTo(Math.round(X(nx0 + i)) + 0.5, Y(ny0)); ctx.lineTo(Math.round(X(nx0 + i)) + 0.5, Y(ny0 + b)); }
    for (let j = t; j < b; j += t) { ctx.moveTo(X(nx0), Math.round(Y(ny0 + j)) + 0.5); ctx.lineTo(X(nx0 + a), Math.round(Y(ny0 + j)) + 0.5); }
    ctx.stroke();
  }
  ctx.strokeStyle = "#f3f7fc";
  ctx.lineWidth = 2;
  ctx.setLineDash([6, 4]);
  ctx.strokeRect(X(0), Y(0), k * d.cells[0], k * d.cells[1]);
  ctx.setLineDash([]);
}

async function applyMapSize() {
  const d = msz.data, pack = msz.pack;
  if (!d || msz.busy) return;
  const [a, b] = sizeWanted(), t = d.tile;
  msz.busy = true;
  msz.bad = false;
  msz.note = fill(mv.words.size_making, { a, b });
  renderMapSize();
  try {
    const got = await mv.api.set_map_size(pack, a, b, t * msz.left, t * msz.top);
    if (msz.pack !== pack) return;
    Object.assign(msz, { data: got, left: 0, top: 0, right: 0, bottom: 0 });
    msz.note = fill(mv.words.size_made, { a: got.cells[0], b: got.cells[1] });
    if (mv.current === pack) show(pack);   // the map again, its ground and scenarios at the new size
  } catch (err) {
    msz.note = (err && err.message) || String(err);
    msz.bad = true;
  } finally {
    msz.busy = false;
    renderMapSize();
  }
}

function wireMapSize() {
  $("map-size-open").addEventListener("click", openMapSize);
  $("size-apply").addEventListener("click", applyMapSize);
  $("size-close").addEventListener("click", () => $("map-size").close());
  $("map-size").addEventListener("keydown", (e) => e.stopPropagation());  // keys never move the map behind it
}

// --- a mission's three steps (StudioApi.mission_steps, rusemod.missionsteps: LittleGroove's Menu Entry, Load & Files
// and Text): where the game's menus list it, the files the game needs to start it, link by link, and its texts ---
const mission = { data: null, tab: "menu", pack: null, file: null, note: null };
const MISSION_TABS = ["menu", "files", "texts"];
const MISSION_KINDS = { operation: "operation", campaign: "campaign", mp: "skirmish" };  // his kinds -> scen_kind_*
const MISSION_MARKS = { ok: "✓", missing: "✗", mismatch: "✗", optional: "–", unknown: "?" };

async function openMission() {
  const w = mv.words, s = ((scen.data || {}).scenarios || [])[scen.pick];
  if (!s || !mv.current) return;
  Object.assign(mission, { pack: mv.current, file: s.file, data: null, note: null });
  $("mission-title").textContent = fill(w.mission_title, { name: scenarioLabel(s) });
  $("mission-close").textContent = w.close;
  $("mission-close").title = w.tip_close;
  renderMission();
  $("mission-box").showModal();
  await refreshMission();
}

async function refreshMission() {
  const asked = `${mission.pack}|${mission.file}`;
  let data;
  try { data = await mv.api.mission_steps(mission.pack, mission.file, mv.lang); } catch (err) { data = { error: String(err.message || err) }; }
  if (asked !== `${mission.pack}|${mission.file}`) return;  // another mission was opened meanwhile
  mission.data = data;
  renderMission();
}

function renderMission() {
  const w = mv.words, d = mission.data;
  $("mission-tabs").replaceChildren(...MISSION_TABS.map((t) => {
    const tab = el("button", { type: "button", className: "tray-tab", role: "tab", textContent: w["mission_tab_" + t],
      title: w["tip_mission_tab_" + t] });
    tab.setAttribute("aria-selected", String(t === mission.tab));
    tab.addEventListener("click", () => { mission.tab = t; renderMission(); });
    return tab;
  }));
  const body = $("mission-body");
  if (!d) { body.replaceChildren(el("p", { className: "muted small", textContent: w.mission_loading })); return; }
  if (d.error) { body.replaceChildren(el("p", { className: "notice warn", textContent: d.error })); return; }
  if (d.new) { body.replaceChildren(el("p", { className: "small", textContent: w.mission_new_map })); return; }
  body.replaceChildren(...(mission.tab === "menu" ? missionMenu(d) : mission.tab === "files" ? missionFiles(d) : missionTexts(d)));
}

// In the menus: whether the game lists it, the menu as the player sees it, the entry's values and texts
function missionMenu(d) {
  const w = mv.words, m = d.menu;
  if (!m) return [el("p", { className: "small", textContent: w.mission_unbound })];
  const at = m.order.findIndex((o) => o.this);
  const menu = w["scen_kind_" + (MISSION_KINDS[d.kind] || d.kind)] || d.kind;
  const values = el("dl", { className: "mission-values small" });
  for (const v of m.values) {
    values.append(el("dt", { textContent: w["mission_v_" + v.prop] || v.label, title: w.tip_mission_values }),
      el("dd", { textContent: String(v.value) }));
  }
  const change = el("button", { type: "button", className: "small", textContent: w.mission_values_change,
    title: m.address ? w.tip_mission_values_change : w.mission_values_cannot,
    disabled: !m.address || typeof window.openAllValues !== "function" });
  change.addEventListener("click", () => { $("mission-box").close(); window.openAllValues(m.address); });
  const note = mission.note;
  mission.note = null;
  return [
    el("p", { className: m.listed ? "small" : "notice warn", textContent: m.listed
      ? fill(w.mission_listed, { menu, n: at + 1, total: m.order.length }) : w.mission_not_listed }),
    el("h3", { className: "dup-how-title", textContent: w.mission_order_head, title: w.tip_mission_order }),
    missionOrder(d),
    ...(m.listed ? [missionMoves(m)] : []),
    ...(m.mine ? [el("p", { className: "muted small", textContent: w.mission_order_mine })] : []),
    ...(note ? [el("p", { className: note.bad ? "notice warn" : "notice", textContent: note.text })] : []),
    el("h3", { className: "dup-how-title", textContent: w.mission_values_head, title: w.tip_mission_values }),
    values,
    el("div", { className: "actions" }, change),
    el("h3", { className: "dup-how-title", textContent: w.mission_menu_texts_head, title: w.tip_mission_menu_texts }),
    ...m.texts.map((t) => missionTextRow(w["mission_t_" + t.prop] || t.label, t.key, t.words,
      (d.texts.find((x) => x.key === t.key) || {}).mine)),
  ];
}

// The menu as the player sees it, in its groups under the menu's own headings (CategoryId): a mission moves among its
// group's missions from its own list of the game's (LittleGroove's Move up / Move down)
function missionOrder(d) {
  const w = mv.words, m = d.menu, order = m.order, box = el("div", { className: "mission-order small" });
  for (let s = 0; s < order.length;) {
    let e = s + 1;
    while (e < order.length && order[e].group === order[s].group) e++;
    const members = order.slice(s, e);
    const label = (m.headings || {})[String(members[0].group)] || fill(w.mission_group, { n: members[0].group });
    const list = el("ol", { start: s + 1 }, ...members.map((o) => el("li", { className: o.this ? "this" : "",
      textContent: o.title || o.tracking || "?" })));
    box.append(el("div", { className: "mission-run" },  // a group stays whole in one column
      el("div", { className: "mission-group", title: w.tip_mission_group, textContent: label }), list));
    s = e;
  }
  return box;
}

// Move up, Move down and Game's order, saved in the mod's menus.toml (each locked with its reason when it can't)
function missionMoves(m) {
  const w = mv.words, can = !!mv.brush.mod;
  const button = (text, why, tip, call) => {
    const b = el("button", { type: "button", className: "small", textContent: text, disabled: !can || !!why,
      title: !can ? w.no_mod : why ? w[why] : tip });
    b.addEventListener("click", async () => {
      b.disabled = true;
      try {
        mission.data = await call();
        mission.note = { text: w.mission_moved };
      } catch (err) {
        mission.note = { text: String(err.message || err), bad: true };
      }
      renderMission();
    });
    return b;
  };
  return el("div", { className: "actions" },
    button(w.mission_move_up, m.up && "tip_mission_move_" + m.up, w.tip_mission_move_up,
      () => mv.api.mission_move(mission.pack, mission.file, -1, mv.lang)),
    button(w.mission_move_down, m.down && "tip_mission_move_" + m.down, w.tip_mission_move_down,
      () => mv.api.mission_move(mission.pack, mission.file, 1, mv.lang)),
    button(w.mission_order_reset, !m.mine && "tip_mission_order_reset_none", w.tip_mission_order_reset,
      () => mv.api.mission_order_reset(mission.pack, mission.file, mv.lang)));
}

// Files check: the chain from the menu entry to the mission, each link fine, missing or not matching, and why
function missionFiles(d) {
  const w = mv.words, c = d.chain;
  const list = el("ul", { className: "mission-chain small" });
  for (const l of c.links) {
    let why = w["mission_why_" + l.why] || l.why;
    if (l.why === "dico_langs_ok") why = fill(why, { n: l.detail.split(",").filter(Boolean).length });
    const li = el("li", { className: "chain-" + l.state, title: w["mission_state_" + l.state] || l.state },
      el("span", { className: "chain-mark", textContent: MISSION_MARKS[l.state] || "?" }), " ", why);
    li.style.marginLeft = `${l.depth * 18}px`;
    list.append(li);
  }
  return [
    el("p", { className: c.broken ? "notice warn" : "small", textContent: c.broken
      ? fill(w.mission_files_broken, { n: c.broken }) : w.mission_files_ok }),
    list,
    el("p", { className: "muted small", textContent: w.mission_files_note }),
  ];
}

// Texts: every text the mission owns, its menu entry's and its script's, each changed in every language at once
function missionTexts(d) {
  const w = mv.words, out = [];
  if (d.script === false) out.push(el("p", { className: "notice warn", textContent: w.mission_texts_no_script }));
  out.push(el("p", { className: "muted small", textContent: fill(w.mission_texts_count, { n: d.texts.length }) }));
  for (const t of d.texts) {
    const where = t.where === "menu" ? (w["mission_t_" + t.prop] || t.prop)
      : t.line ? fill(w.mission_texts_line, { line: t.line }) : w.mission_texts_script;
    out.push(missionTextRow(where, t.key, t.words, t.mine));
  }
  return out;
}

function missionTextRow(label, key, words, mine) {
  const w = mv.words, box = el("div", { className: "mission-text" + (mine ? " edited" : "") });
  const edit = el("button", { type: "button", className: "link small", textContent: w.values_words_edit,
    title: w.tip_mission_words, disabled: typeof window.wordsPanel !== "function" });
  let panel = null;
  edit.addEventListener("click", () => {
    if (panel) { panel.remove(); panel = null; return; }
    panel = window.wordsPanel(key, refreshMission, "mod");  // saved in the mod, every language at once
    box.append(panel);
  });
  box.append(el("div", { className: "small" }, el("span", { className: "muted", textContent: `${label}: ` }),
    el("span", { textContent: words ? `“${words}”` : w.values_words_none }), " ", edit));
  return box;
}

function wireMission() {
  $("scen-mission").addEventListener("click", openMission);
  $("mission-close").addEventListener("click", () => $("mission-box").close());
  $("mission-box").addEventListener("keydown", (e) => e.stopPropagation());  // keys never move the map behind it
}

async function deleteMap() {
  const w = mv.words, pack = mv.current, name = mapName(pack);
  $("map-delete-yes").disabled = true;
  try {
    const res = await mv.api.delete_map(pack);
    mv.maps = res.maps;
    mv.deleteAsk = null;
    $("map-delete-yes").disabled = false;
    window.dispatchEvent(new CustomEvent("map-deleted", { detail: { text: fill(w.map_deleted, { name }) } }));
    await show(res.copy_of);
  } catch (err) {
    $("map-delete-yes").disabled = false;
    $("map-delete-ask").textContent = (err && err.message) || String(err);
  }
}

// What players call a map in the Studio's language (its own name when the menus have none)
function mapName(pack) {
  const m = mv.maps.find((x) => x.pack === pack);
  return m ? (menuNames(m)[0] || m.names[0] || m.pack) : pack;
}

// --- Duplicate map: a new map, a full copy of the one open with a name of its own, listed in BATTLES next to it
// (StudioApi.duplicate_map; MOD_FORMAT §8 "A new map"). The window says what that is and how it works before asking
// for the name; the copy opens once it's made, and its edits are its own. ---
function packName(name) {  // the folder and file name the Studio gives it (api.py _pack_name), before any number
  const words = name.normalize("NFKD").replace(/[̀-ͯ]/g, "").match(/[A-Za-z0-9]+/g) || [];
  let base = words.map((x) => x[0].toUpperCase() + x.slice(1)).join("");
  if (!base || !/^[A-Za-z]/.test(base)) base = "NewMap" + base;
  return base.slice(0, 36);
}

// The three kinds of new map, in the order the window shows them (StudioApi._menu_entries' kinds)
const DUP_KINDS = ["battles", "operation", "campaign"];
// What a new map starts from: a full copy, or blank (StudioApi.duplicate_map's preset; rusemod.presets). The owner,
// 2026-10-05: "a preset, like want to start a Navy map ... D-Day, but ocean" and "a flat basic terrain version";
// "Blank Terrain, Blank Ocean". Blank ones start from a Battles map only (a mission's script needs its own items).
// Blank Ocean taken out, then back the same day with a warning of its own (the owner, 2026-10-08: "blank oceans stay
// in with a warning label"): a map of separate islands crashes the game when a land unit is sent across.
const DUP_STARTS = ["copy", "blank_terrain", "blank_ocean"];
// scratch: opened from "New map: start from scratch…" before any map is open (2026-10-06, the owner: a blank map had
// to be found under Duplicate map, "it needs to explicitly say that"); base: the game map it then sits on
const dup = { entries: [], kind: null, typed: false, start: "copy", scratch: false, base: null };

function dupPack() {  // the map the new one is made from: the open one, or from scratch the chosen game map
  return dup.scratch ? dup.base : mv.current;
}

function shippedMaps() {  // the game's own maps (a new map can't sit on another new map)
  return (mv.maps || []).filter((m) => !m.copy_of);
}

function mapTitle(m) {  // what the menus call a map in the Studio's language, else its map-list name
  const t = m.titles || {};
  const names = (mv.lang !== "base" && (t[mv.lang] || t.us)) || m.names || [];
  return names[0] || m.pack;
}

function defaultBase() {  // D-Day when the game has it (the blank presets were tested on it), else the first map
  const maps = shippedMaps();
  return ((maps.find((m) => /cotentin/i.test(m.pack)) || maps[0] || {}).pack) || null;
}

function entryTitle(e) {  // what the menus call an entry in the Studio's language, else its map-list name
  const t = e.titles || {};
  return (mv.lang !== "base" && (t[mv.lang] || t.us)) || e.name;
}

function renderDupKinds() {
  const w = mv.words;
  $("dup-kind").textContent = w.dup_kind;
  $("dup-kind").classList.toggle("hidden", dup.scratch);  // from scratch it's a Battles map: nothing to choose
  $("dup-kinds").classList.toggle("hidden", dup.scratch);
  $("dup-kinds").replaceChildren(...DUP_KINDS.map((k) => {
    const has = dup.entries.some((e) => e.kind === k);
    const b = el("button", { type: "button", className: "dup-kind", disabled: !has },
      el("span", { className: "kind-name", textContent: w[`dup_kind_${k}`] }),
      el("span", { className: "kind-what", textContent: has ? w[`dup_kind_${k}_what`] : w.dup_kind_none }));
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(dup.kind === k));
    b.addEventListener("click", () => {
      dup.kind = k;
      if (k !== "battles") dup.start = "copy";
      renderDupKinds();
      renderDupStarts();
      fillDupEntries();
    });
    return b;
  }));
}

function renderDupStarts() {
  const w = mv.words, map = mapName(dupPack()), battles = dup.kind === "battles";
  const story = dup.kind === "operation" || dup.kind === "campaign";  // Blank Terrain starts its own mission there
  const starts = dup.scratch ? DUP_STARTS.filter((k) => k !== "copy") : DUP_STARTS;  // from scratch: blank only
  $("dup-start").textContent = w.dup_start;
  $("dup-starts").replaceChildren(...starts.map((k) => {
    const open = k === "copy" || battles || (story && k === "blank_terrain");
    const b = el("button", { type: "button", className: "dup-kind", disabled: !open },
      el("span", { className: "kind-name", textContent: w[`dup_start_${k}`] }),
      el("span", { className: "kind-what", textContent: fill(w[`dup_start_${k}_what`], { map }) }),
      ...(w[`dup_start_${k}_warn`] ? [el("span", { className: "kind-warn", textContent: "⚠ " + w[`dup_start_${k}_warn`] })] : []));
    b.setAttribute("role", "radio");
    b.setAttribute("aria-checked", String(dup.start === k));
    b.addEventListener("click", () => { dup.start = k; renderDupStarts(); dupSuggestName(); });
    return b;
  }));
  $("dup-start-note").textContent = story ? w.dup_start_own_mission : w.dup_start_battles_only;
  $("dup-start-note").classList.toggle("hidden", battles || !dup.entries.length);
  $("dup-how-edits").classList.toggle("hidden", dup.start !== "copy");  // a blank start takes none of them along
}

function renderDupBase() {  // from scratch: the game map the new one sits on (its size, players, starting points)
  const w = mv.words;
  $("dup-base-label").textContent = w.dup_base;
  $("dup-base-what").textContent = w.dup_base_what;
  $("dup-base").replaceChildren(...shippedMaps().map((m) => el("option", { value: m.pack, textContent: mapTitle(m),
                                                                            title: m.pack })));
  $("dup-base").value = dup.base || "";
  $("dup-base-row").classList.toggle("hidden", !dup.scratch);
}

async function loadDupOptions() {  // what the chosen map offers: its menu entries, where the copy goes, or why not
  const w = mv.words, pack = dupPack();
  $("dup-go").disabled = true;
  $("dup-note").textContent = "";
  let opts;
  try {
    opts = await mv.api.duplicate_options(pack);
  } catch (err) {
    $("dup-note").textContent = (err && err.message) || String(err);
    return;
  }
  $("dup-how-where").textContent = opts.folder ? fill(w.dup_how_where, { folder: opts.folder }) : w.dup_how_new;
  if (opts.why) { $("dup-note").textContent = opts.why; return; }
  dup.entries = opts.entries || [];
  const battles = dup.entries.some((e) => e.kind === "battles");
  dup.kind = dup.scratch ? (battles ? "battles" : null) : (DUP_KINDS.find((k) => dup.entries.some((e) => e.kind === k)) || null);
  renderDupKinds();
  renderDupStarts();
  fillDupEntries();
  if (dup.scratch && !battles) { $("dup-note").textContent = w.dup_start_battles_only; return; }  // pick another base
  $("dup-go").disabled = false;
}

function fillDupEntries() {
  const mine = dup.entries.filter((e) => e.kind === dup.kind);
  $("dup-entry").replaceChildren(...mine.map((e) => el("option", { value: e.name, textContent: entryTitle(e), title: e.name })));
  $("dup-entry-row").classList.toggle("hidden", mine.length < 2);
  dupSuggestName();
}

function dupSuggestName() {  // "<what the copied entry is called> 2" (or "... Blank Ocean"), until a name is typed
  if (dup.typed) return;
  const e = dup.entries.find((x) => x.name === $("dup-entry").value);
  const tail = dup.start === "copy" ? "2" : mv.words[`dup_start_${dup.start}`];
  $("dup-name").value = e ? `${entryTitle(e).replace(/^\d+\.\s*/, "")} ${tail}` : "";  // a chapter's number left out
  dupNameChanged();
}

async function openDuplicate(scratch = false) {
  const w = mv.words;
  dup.scratch = Boolean(scratch);
  dup.base = dup.scratch ? defaultBase() : null;
  const pack = dupPack();
  if (!pack) return;
  const map = mapName(pack);
  dup.entries = [];
  dup.kind = dup.scratch ? "battles" : null;
  dup.typed = false;
  dup.start = dup.scratch ? "blank_terrain" : "copy";
  renderDupKinds();
  renderDupStarts();
  renderDupBase();
  $("dup-title").textContent = dup.scratch ? w.dup_scratch_title : w.duplicate_map;
  $("dup-lead").textContent = dup.scratch ? w.dup_scratch_lead : fill(w.dup_lead, { map });
  $("dup-how").textContent = w.dup_how;
  $("dup-how-own").textContent = w.dup_how_own;
  $("dup-how-edits").textContent = fill(w.dup_how_edits, { map });
  $("dup-how-where").textContent = "";
  $("dup-how-tested").textContent = w.dup_how_tested;
  $("dup-name-label").textContent = w.dup_name;
  $("dup-entry-label").textContent = w.dup_entry;
  $("dup-go").textContent = dup.scratch ? w.dup_scratch_go : w.dup_go;
  $("dup-cancel").textContent = w.cancel;
  $("dup-note").textContent = "";
  $("dup-name").value = "";
  $("dup-file").textContent = "";
  $("dup-long").classList.add("hidden");
  $("dup-entry-row").classList.add("hidden");
  $("dup-go").disabled = true;
  $("duplicate").showModal();
  await loadDupOptions();
  $("dup-name").focus();
  $("dup-name").select();
}

function dupBaseChanged() {  // another game map to sit on: its entries, its suggested name
  dup.base = $("dup-base").value || null;
  dup.typed = false;
  loadDupOptions();
}

function dupNameChanged() {
  const w = mv.words, name = $("dup-name").value.trim();
  $("dup-file").textContent = name ? fill(w.dup_file, { file: packName(name) }) : "";
  $("dup-long").textContent = w.dup_long;
  $("dup-long").classList.toggle("hidden", name.length <= 35);  // longer names get cut off in game
}

async function duplicate(e) {
  e.preventDefault();
  const w = mv.words, pack = dupPack(), name = $("dup-name").value.trim();
  if (!name || !pack) return;
  const entry = $("dup-entry").value || null;  // the server leaves the map's one BATTLES map out of map.toml
  $("dup-go").disabled = true;
  $("dup-note").textContent = "";
  try {
    const map = mapName(pack);
    const res = await mv.api.duplicate_map(pack, name, entry, dup.start === "copy" ? null : dup.start);
    mv.maps = res.maps;
    $("duplicate").close();
    // the map project may be new: the header's menu shows it (app.js), and the status line says what was made
    const done = dup.start === "copy" ? fill(w.dup_done, { name, map })  // a blank start isn't "a copy of"
      : fill(w.dup_done_blank, { name, map, start: w[`dup_start_${dup.start}`] });
    window.dispatchEvent(new CustomEvent("map-duplicated", { detail: { text: done } }));
    await show(res.pack);
  } catch (err) {
    $("dup-note").textContent = (err && err.message) || String(err);
    $("dup-go").disabled = false;
  }
}

function renderWords() {
  const w = mv.words;
  renderLayers();
  renderLegend();
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
  if (mv.brush.name && BRUSHES[mv.brush.name]) { sizeLabel(); strengthLabel(); }  // (in the new language, with numbers)
  $("brush-angle").title = w.tip_brush_angle;
  $("brush-undo").textContent = w.brush_undo;
  $("brush-undo").title = w.tip_brush_undo;
  $("brush-redo").textContent = w.brush_redo;
  $("brush-redo").title = w.tip_brush_redo;
  $("brush-clear").textContent = w.brush_clear;
  $("brush-clear").title = w.tip_brush_clear;
  $("brush-clear-yes").textContent = w.remove_all;
  $("brush-clear-yes").title = w.tip_remove_all;
  $("brush-clear-no").textContent = w.cancel;
  $("brush-clear-no").title = w.tip_cancel;
  if (!mv.current) $("map-pick").textContent = w.pick_map;
  $("map-new-scratch").textContent = w.new_map_scratch;
  $("map-new-scratch").title = w.tip_new_map_scratch;
  $("map-scratch-what").textContent = w.scratch_what;
  $("map-scratch").classList.toggle("hidden", Boolean(mv.current) || !shippedMaps().length);
  $("map-scratch-hud").textContent = w.new_map_scratch;
  $("map-scratch-hud").title = w.tip_new_map_scratch;
  $("map-duplicate").textContent = w.duplicate_map;
  $("map-duplicate").title = w.tip_duplicate_map;
  renderDelete();
  foldMaps(Boolean(mv.folded));
  renderBrushes();
  renderScenTools();
  renderRoadTray();
  renderBridgeTray();
  renderCheck();
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
const keys = { down: new Set(), shift: false, frame: 0, at: 0, map: loadKeys(), by: {}, arming: null, clash: null };
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
      textContent: keys.arming === action ? w.keys_press : keyName(codeOf(action)), title: w.tip_key_button });
    key.setAttribute("aria-label", w["key_" + action]);
    key.addEventListener("click", () => { keys.arming = keys.arming === action ? null : action; keys.clash = null; renderKeys(); });
    rows.append(el("span", { className: "small", textContent: w["key_" + action] }), key);
  }
  const reset = el("button", { type: "button", className: "small ghost", textContent: w.keys_reset, title: w.tip_keys_defaults });
  reset.addEventListener("click", () => {
    keys.map = { ...KEY_DEFAULTS };
    keys.arming = null;
    keys.clash = null;
    saveKeys();
    rebuildKeys();
    renderKeys();
  });
  panel.append(el("div", { className: "muted small", textContent: w.keys_fixed }), rows);
  if (keys.clash) panel.append(keysClash());
  panel.append(el("div", { className: "actions" }, reset));
}

// A key pressed for one action that another already has (armKey): Swap gives the other one this action's key, Take
// it leaves the other one without a key, Cancel changes nothing.
function keysClash() {
  const w = mv.words, { action, code, other } = keys.clash, old = codeOf(action);
  const names = { key: keyName(code), action: w["key_" + action], other: w["key_" + other], old: keyName(old) };
  const done = (otherGets) => {
    keys.map[other] = otherGets;
    keys.map[action] = code;
    keys.clash = null;
    saveKeys();
    rebuildKeys();
    renderKeys();
  };
  const button = (word, tip, act, className = "small") => {
    const b = el("button", { type: "button", className, textContent: fill(word, names), title: fill(tip || "", names) });
    b.addEventListener("click", act);
    return b;
  };
  return el("div", { className: "keys-clash small", role: "alert" },
    el("span", { textContent: fill(w.keys_clash, names) }),
    button(w.keys_swap, old ? w.tip_keys_swap : w.tip_keys_swap_none, () => done(old), "small primary"),
    button(w.keys_take, w.tip_keys_take, () => done(null)),
    button(w.cancel, w.tip_cancel, () => { keys.clash = null; renderKeys(); }, "small ghost"));
}

function armKey(e) {
  const action = keys.arming;
  if (e.type !== "keydown") return;
  e.preventDefault();
  if (e.key === "Escape") { keys.arming = null; renderKeys(); return; }
  if (/^(Shift|Control|Alt|Meta)/.test(e.code) || !e.code) return;  // a modifier alone isn't a key
  const other = keys.by[e.code];
  if (other && other !== action) {   // another action's key: asked, Swap or take it (the owner's Studio 1.0 list, item
    keys.clash = { action, code: e.code, other };   // 11: "key rebinding that offers a swap"), never taken quietly
    keys.arming = null;
    renderKeys();
    return;
  }
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
  if (bridge.on) {  // a bridge's length (5 m a step) and turn
    const k = bridgeKind();
    if (what === "size" && k) bridge.length[k.type] = Math.min(k.most, Math.max(k.least, bridgeLength(k) + dir * 5 * METRE));
    else if (what !== "size") bridge.turn = (bridge.turn + dir * 5 + 360) % 360;
    renderBridgeTray();
    drawBridges();
    return;
  }
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
  dock.check = false;
  stopRoad();
  stopBridge();
  if (scen.tool) { scen.tool = null; scen.selected = null; pointerMode(); renderScenTools(); drawScenario(); drawMissionCameras(); }
  cancelRamp();
  dropPlaceGesture();
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
  if (ctrl && !e.altKey && (e.code === "KeyY" || (e.code === "KeyZ" && e.shiftKey))) {  // Redo, as other editors
    if (fieldFocused(false)) return;                                                   // have it
    e.preventDefault();
    if (mv.brush.on) redoStroke(); else if (selecting()) selRedo(); else if (mv.place.on) redoPlace();
    else if (road.on) redoRoad(); else if (bridge.on) redoBridge();
    return;
  }
  if (ctrl && !e.altKey && e.code === "KeyZ") {  // the one shortcut that works with a modifier
    if (fieldFocused(false)) return;              // a text box has its own undo
    e.preventDefault();
    if (mv.brush.on) undoStroke(); else if (selecting()) selUndo(); else if (mv.place.on) undoPlace();
    else if (road.on) undoRoad(); else if (bridge.on) undoBridge();
    return;
  }
  if (ctrl || e.altKey) return;
  if ((e.key === "Delete" || e.key === "Backspace") && selecting() && sel.items.length && !fieldFocused(false)) {
    e.preventDefault();  // Select: what's picked goes, as the game's editor and every other one does it
    selDelete();
    return;
  }
  if (e.key === "Escape") {
    if (fieldFocused(true)) { document.activeElement.blur(); return; }  // first out of the box, then back to Look
    if (road.on && road.pts.length) {  // then the road being drawn
      road.pts = [];
      showRoadLength(null);
      renderRoadTray();
      drawRoadPreview();
      return;
    }
    if (mv.place.on && (mv.place.lineStart || mv.place.box || mv.place.path)) {  // then a line, path, grid or box half made
      dropPlaceGesture();
      placeNote("");
      return;
    }
    if (scen.sel.size) { clearSelection(); return; }  // then what's selected, as in the game
    if (selecting() && sel.items.length) { clearSel(); return; }  // (Select's picks the same)
    lookAround();
    return;
  }
  if (e.key === "Enter" && road.on && road.tool === "free" && !fieldFocused(false)) { finishRoad(); return; }
  if (e.key === "Enter" && mv.place.on && mv.place.path && !fieldFocused(false)) { finishPath(); return; }  // a Path
  if (held) {
    if (fieldFocused(e.code.startsWith("Arrow"))) return;  // arrows in a slider are the slider's; letters in a box, the box's
    e.preventDefault();  // the arrows would scroll the page
    keys.down.add(e.code);
    if (!keys.frame) { keys.at = performance.now(); keys.frame = requestAnimationFrame(moveStep); }
    return;
  }
  if (fieldFocused(false)) return;
  // the Map side's keys pick its tools on the Map side only: on the Scenario side a slip of a finger would turn the
  // next click into a hill instead of a unit
  const onMap = mv.mode === "map";
  const digit = /^Digit([0-9])$/.exec(e.code);
  if (digit) { const b = Object.keys(BRUSHES)[(Number(digit[1]) + 9) % 10]; if (b && onMap) pickBrush(b); return; }
  const action = keys.by[e.code];
  if (action === "brush") { if (mv.brush.on) lookAround(); else if (onMap) pickBrush(mv.brush.name); }
  else if (action === "place") { if (onMap) setPlaceMode(!mv.place.on); }
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

// A panel's size (the owner, 2026-10-05: "make it all shrinkable and make it look nice at every shrinkable level ...
// customizable for the user"): its size handle drags it from 40% to 125%, everything in it with it (CSS zoom, so the
// text is drawn again at its new size, not blurred); its grip row stays full size, always easy to reach. Small, the
// tools show their pictures only (their names on hover).
const PANEL_SCALE = [0.4, 1.25];
const panelScale = (s) => Math.min(PANEL_SCALE[1], Math.max(PANEL_SCALE[0], Number(s.scale) || 1));

function placePanel(key) {
  const { el: panel, state: s, fold, size, row } = panels[key], st = panel.style, k = panelScale(s);
  st.zoom = k === 1 ? "" : String(k);
  row.style.zoom = k === 1 ? "" : String(1 / k);  // the grip, the fold and the size handle keep their size
  if (key === "hud") st.paddingRight = k === 1 ? "" : `${70 / k}px`;  // so does the room kept for them (style.css)
  if (s.left == null) {
    st.left = st.top = st.right = st.bottom = st.transform = "";
    panel.classList.remove("moved");
  } else {  // kept in screen pixels: a zoomed panel's own left and top are scaled by its zoom
    panel.classList.add("moved");
    Object.assign(st, { left: s.left / k + "px", top: s.top / k + "px", right: "auto", bottom: "auto", transform: "none" });
  }
  panel.classList.toggle("folded", Boolean(s.folded));
  panel.classList.toggle("compact", k < 0.7);
  const w = mv.words;
  fold.textContent = s.folded ? "▸" : "▾";
  fold.title = (s.folded ? w.tip_panel_unfold : w.tip_panel_fold) || "";
  size.title = `${fill(w.tip_panel_size || "{n}%", { n: Math.round(k * 100) })}`;
}

function makePanels() {
  for (const [id, key] of PANELS) {
    const panel = $(id), stage = panel.parentElement;
    const grip = el("span", { className: "grip", textContent: "⠿" });
    const fold = el("button", { type: "button", className: "panel-fold" });
    const size = el("span", { className: "panel-size", textContent: "◢" });
    const row = el("div", { className: "panel-grip" }, grip, fold, size);
    panel.prepend(row);
    panels[key] = { el: panel, grip, fold, size, row, state: panelState(key) };
    placePanel(key);
    fold.addEventListener("click", () => {
      panels[key].state.folded = !panels[key].state.folded;
      placePanel(key);
      savePanel(key);
    });
    grip.addEventListener("dblclick", () => {  // back where it started (its fold, size and Show more stay)
      const { folded, scale, more } = panels[key].state;
      panels[key].state = { folded, scale, more };
      placePanel(key);
      savePanel(key);
    });
    // the size handle: drag down to make the panel smaller, up to make it bigger; the wheel over it too; a
    // double-click puts it back to its normal size
    const setScale = (k) => {
      panels[key].state.scale = Math.round(Math.min(PANEL_SCALE[1], Math.max(PANEL_SCALE[0], k)) * 100) / 100;
      placePanel(key);
    };
    size.addEventListener("dblclick", () => { setScale(1); savePanel(key); });
    size.addEventListener("wheel", (ev) => {
      ev.preventDefault();
      setScale(panelScale(panels[key].state) + (ev.deltaY > 0 ? -0.05 : 0.05));
      savePanel(key);
    }, { passive: false });
    size.addEventListener("pointerdown", (ev) => {
      ev.preventDefault();
      try { size.setPointerCapture(ev.pointerId); } catch { /* the drag still follows the handle without it */ }
      const y0 = ev.clientY, k0 = panelScale(panels[key].state);
      const move = (e) => setScale(k0 - (e.clientY - y0) / 300);  // 300 px down: from full size to 0
      const up = () => {
        size.removeEventListener("pointermove", move);
        size.removeEventListener("pointerup", up);
        savePanel(key);
      };
      size.addEventListener("pointermove", move);
      size.addEventListener("pointerup", up);
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
  renderHudMore();
}

// The map panel starts short: Show more opens its wordier parts (the counts, what the colours mean, the see-through
// layers, where the scenario is in the game, the keys), Show less closes them; kept with the panel's place
function renderHudMore() {
  const w = mv.words, more = Boolean((panels.hud || { state: {} }).state.more), b = $("map-more");
  $("map-hud-more").classList.toggle("hidden", !more);
  b.textContent = more ? w.map_less : w.map_more;
  b.title = more ? w.tip_map_less : w.tip_map_more;
}

let wired = false;
function wire() {
  if (wired) return;
  wired = true;
  makePanels();
  $("map-more").addEventListener("click", () => {
    panels.hud.state.more = !panels.hud.state.more;
    savePanel("hud");
    renderHudMore();
  });
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
    renderLegend();
    renderSelection();
  });
  $("scen-pick").addEventListener("change", (e) => {
    scen.pick = Number(e.target.value) || 0;
    scen.selected = null;
    scen.sel.clear();
    renderScenarioPick();
    drawScenario();
    renderScenTools();
  });
  $("scen-gap").addEventListener("input", (e) => { scen.gap[scen.kind] = Number(e.target.value); renderScenTools(); });
  $("mode-map").addEventListener("click", () => setMode("map"));
  $("mode-scen").addEventListener("click", () => setMode("scenario"));
  $("scen-size").addEventListener("input", (e) => {  // the icons' size, live
    scen.iconSize = Number(e.target.value) / 100;
    saveScenView();
    $("scen-size-label").textContent = fill(mv.words.scen_icon_size || "Icon size {pct} %", { pct: Number(e.target.value) });
    fitIcons();
    if (mv.gl) mv.gl.draw();
  });
  $("scen-snap").addEventListener("change", (e) => {
    snapRoads = e.target.checked;
    try { localStorage.setItem("studio.snaproads", snapRoads ? "1" : "0"); } catch { /* not kept: fine */ }
    saveView();
  });
  $("scen-unit").addEventListener("change", spawnDesc);  // the picked unit's own line from the game
  $("road-snap").addEventListener("change", (e) => {  // a road's ends onto roads and placed bridges, or not
    road.snapOn = e.target.checked;
    road.snap = null;
    drawRoadPreview();
    saveView();
  });
  $("road-trees").addEventListener("change", (e) => {  // the next roads keep the trees on their path, or clear them
    road.keepTrees = e.target.checked;
    saveView();
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
  $("brush-size").addEventListener("input", (e) => { settingsOf(mv.brush.name).size = Number(e.target.value); sizeLabel(); });
  $("brush-strength").addEventListener("input", (e) => {
    settingsOf(mv.brush.name).strength = Number(e.target.value);
    strengthLabel();  // (says what it comes to as it moves: an opacity, a height in metres, a share of the way)
  });
  // Map Paint: the colour wheel (drag round the ring for the colour, in the square for how strong and how light), the
  // colour as #rrggbb, the eyedropper, and Texture's spot to copy from
  let wheelPart = null;
  $("paint-wheel").addEventListener("pointerdown", (e) => {
    const rect = e.currentTarget.getBoundingClientRect(), c = WHEEL / 2;
    const x = (e.clientX - rect.left) * WHEEL / rect.width - c, y = (e.clientY - rect.top) * WHEEL / rect.height - c;
    const d = Math.hypot(x, y);
    wheelPart = d >= WHEEL_IN - 2 && d <= WHEEL_OUT + 3 ? "hue"
      : Math.abs(x) <= WHEEL_HALF + 3 && Math.abs(y) <= WHEEL_HALF + 3 ? "square" : null;
    if (!wheelPart) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    wheelPick(e, wheelPart);
  });
  $("paint-wheel").addEventListener("pointermove", (e) => { if (wheelPart && e.buttons) wheelPick(e, wheelPart); });
  for (const type of ["pointerup", "pointercancel"]) {
    $("paint-wheel").addEventListener(type, () => { if (wheelPart) rememberColour(paint.colour); wheelPart = null; renderPaintPanel(); });
  }
  $("paint-hex").addEventListener("change", (e) => {
    const v = e.target.value.trim(), hex = v.startsWith("#") ? v : "#" + v;
    if (/^#[0-9a-fA-F]{6}$/.test(hex)) setPaintColour(hex, true);
    else { e.target.value = paint.colour; brushNote(mv.words.paint_hex_bad, "error"); }
  });
  $("paint-dropper").addEventListener("click", () => {
    paint.picking = paint.picking === "colour" ? null : "colour";
    renderPaintPanel();
    brushNote(paint.picking ? mv.words.paint_pick_help : "");
  });
  $("stamp-pick").addEventListener("click", () => {
    paint.picking = paint.picking === "source" ? null : "source";
    renderPaintPanel();
    brushNote(paint.picking ? mv.words.stamp_pick_help : "");
  });
  // the Texture brush's library: find, size, a map to take ground from, your own pictures
  $("tex-search").addEventListener("input", (e) => { paint.texSearch = e.target.value; renderGameTextures(); });
  $("tex-size").addEventListener("input", (e) => { paint.texScale = Number(e.target.value); renderPaintPanel(); });
  $("tex-turn").addEventListener("input", (e) => { paint.texTurn = Number(e.target.value); renderPaintPanel(); });
  $("tex-map-list").addEventListener("change", (e) => chooseMapToPick(e.target.value));
  $("tex-map-pic").addEventListener("click", (ev) => takeMapSquare(ev));
  $("tex-add").addEventListener("click", () => $("tex-file").click());
  $("tex-file").addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    e.target.value = "";
    addOwnPicture(file);
  });
  // Online (free): find (ambientCG's site is asked once typing stops), the US photos' size, a typed place
  $("tex-online-search").addEventListener("input", (e) => {
    const o = paint.online;
    o.search[o.from] = e.target.value;
    if (o.from !== "ambientcg") { renderOnline(); return; }
    clearTimeout(o.timer);
    o.timer = setTimeout(() => { o.asked = o.search.ambientcg.trim().replace(/\s+/g, " "); renderPaintPanel(); }, 700);
  });
  $("tex-online-metres").addEventListener("change", (e) => { paint.online.metres = Number(e.target.value); renderOnline(); });
  $("tex-online-where").addEventListener("input", (e) => { paint.online.where = e.target.value; });
  $("tex-online-where").addEventListener("keydown", (e) => { if (e.key === "Enter") takeOnline("usgs", "", ""); });
  $("tex-online-take").addEventListener("click", () => takeOnline("usgs", "", ""));
  $("paint-clear").addEventListener("click", () => {  // for the strokes painted from now on
    paint.clear = !paint.clear;
    renderPaintPanel();
  });
  $("paint-decals").addEventListener("click", () => {  // for the strokes painted from now on
    paint.decals = !paint.decals;
    renderPaintPanel();
  });
  $("paint-dither").addEventListener("click", () => {  // for the strokes painted from now on
    paint.dither = !paint.dither;
    renderPaintPanel();
  });
  $("brush-angle").addEventListener("input", (e) => {  // a square brush's turn: its outline follows at once
    settingsOf(mv.brush.name).angle = Number(e.target.value);
    $("brush-angle-label").textContent = fill(mv.words.brush_angle || "{deg}", { deg: e.target.value });
    if (mv.gl && mv.gl.squareRing && mv.gl.squareRing.visible) {
      mv.gl.squareRing.rotation.z = -Number(e.target.value) * Math.PI / 180;
      mv.gl.draw();
    }
  });
  $("brush-look").addEventListener("click", () => lookAround());
  $("place-undo").addEventListener("click", () => (selecting() ? selUndo() : undoPlace()));
  $("place-redo").addEventListener("click", () => (selecting() ? selRedo() : redoPlace()));
  $("place-sel-delete").addEventListener("click", () => selDelete());
  $("place-sel-restore").addEventListener("click", () => selRestore());
  $("place-sel-clear").addEventListener("click", () => clearSel());
  // in Select, Turn and Size set every picked one's when let go (the first picked one's shown on the label)
  $("place-turn").addEventListener("change", (e) => {
    if (selecting() && sel.items.length) selChange((p) => ({ ...p, turn: Number(e.target.value) }));
  });
  $("place-size").addEventListener("change", (e) => {
    if (selecting() && sel.items.length) selChange((p) => ({ ...p, size: Number(e.target.value) }));
  });
  $("brush-redo").addEventListener("click", () => redoStroke());
  $("road-redo").addEventListener("click", () => redoRoad());
  $("bridge-redo").addEventListener("click", () => redoBridge());
  $("place-search").addEventListener("input", () => { placeOptions(); if (mv.place.on) placeNote(mv.place.type ? "" : whyNoType(), "error"); });
  $("place-turn").addEventListener("input", (e) => { mv.place.turn = Number(e.target.value); renderPlace(); });
  $("place-size").addEventListener("input", (e) => { mv.place.size = Number(e.target.value); renderPlace(); });
  $("place-solid").addEventListener("change", (e) => { mv.place.solid = e.target.checked; });
  $("place-spacing").addEventListener("input", (e) => { mv.place.spacing[mv.place.group] = Number(e.target.value); renderPlace(); });
  $("place-area").addEventListener("input", (e) => { mv.place.area = Number(e.target.value); renderPlace(); });
  $("place-rows").addEventListener("input", (e) => { mv.place.rows[mv.place.group] = Number(e.target.value); renderPlace(); });
  $("place-roads").addEventListener("change", (e) => { mv.place.roads = e.target.checked; saveView(); });
  $("place-width").addEventListener("input", (e) => { mv.place.width[mv.place.group] = Number(e.target.value); renderPlace(); });
  $("place-cover").addEventListener("change", (e) => { mv.place.cover = e.target.checked; });
  $("place-finish").addEventListener("click", () => finishPath());
  $("place-again").addEventListener("click", () => placeAgain());
  $("brush-undo").addEventListener("click", () => undoStroke());
  $("brush-erase-whole").addEventListener("click", () => eraseWhole());
  $("brush-water-whole").addEventListener("click", () => waterWhole());
  $("brush-repaint-beach").addEventListener("click", () => {  // for the Paint by shape strokes made from now on
    paint.beach = !paint.beach;
    renderBrushes();
  });
  $("road-finish").addEventListener("click", () => finishRoad());
  $("road-undo").addEventListener("click", () => undoRoad());
  $("bridge-undo").addEventListener("click", () => undoBridge());
  $("bridge-length").addEventListener("input", (e) => {
    const k = bridgeKind();
    if (k) bridge.length[k.type] = Number(e.target.value) * METRE;
    renderBridgeTray();
    drawBridges();
  });
  $("bridge-turn").addEventListener("input", (e) => { bridge.turn = Number(e.target.value); renderBridgeTray(); drawBridges(); });
  $("check-run").addEventListener("click", () => runCheck());
  $("maps-fold").addEventListener("click", () => { foldMaps(!mv.folded); saveView(); });
  $("map-duplicate").addEventListener("click", () => openDuplicate(false));
  $("map-new-scratch").addEventListener("click", () => openDuplicate(true));
  $("map-scratch-hud").addEventListener("click", () => openDuplicate(true));
  $("dup-base").addEventListener("change", dupBaseChanged);
  $("map-picture").addEventListener("click", openMenuPictures);
  wireMenuPictures();
  wireMapSize();
  wireAsset();
  wireMission();
  $("map-sound").addEventListener("click", () => {  // the map's background sound (sound.js; StudioApi.map_sound)
    if (mv.current) window.SoundView.openAmbience(mv.current, mapName(mv.current), mv.words, mv.lang);
  });
  $("map-delete").addEventListener("click", () => { mv.deleteAsk = mv.current; renderDelete(); $("map-delete-yes").focus(); });
  $("map-delete-no").addEventListener("click", () => { mv.deleteAsk = null; renderDelete(); });
  $("map-delete-yes").addEventListener("click", deleteMap);
  $("dup-form").addEventListener("submit", duplicate);
  $("dup-name").addEventListener("input", () => { dup.typed = true; dupNameChanged(); });
  $("dup-entry").addEventListener("change", dupSuggestName);
  $("dup-cancel").addEventListener("click", () => $("duplicate").close());
  $("duplicate").addEventListener("keydown", (e) => e.stopPropagation());  // typing a name never moves the map
  $("brush-clear").addEventListener("click", () => {
    const w = mv.words, n = (erasing() ? mv.brush.erase : mv.brush.strokes).length.toLocaleString();
    $("brush-sure-text").textContent = fill(erasing() ? w.erase_really_clear : w.really_clear, { n });
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
  if (mv.api && mv.api.set_pref) mv.api.set_pref("view", { map_kind: mv.kind, maps_folded: Boolean(mv.folded),
    scen_layers: scen.layers, icon_size: scen.iconSize, zone_fill: zoneFill, stick_roads: snapRoads,
    road_snap: road.snapOn, road_trees: road.keepTrees, place_roads: mv.place.roads, map_mode: mv.mode }).catch(() => {});
}

// app.js opens the view when its tab is picked, and passes the words and the language on every language change.
window.MapView = {
  // a stroke, an area or a Select step not saved yet (app.js unsavedReasons: closing the Studio asks first)
  busy() { return Boolean(mv.brush.painting || mv.place.painting || sel.busy || sel.drag); },
  async open(api, words, lang) {
    mv.api = api;
    mv.words = words;
    mv.lang = lang || "base";
    wire();
    loadKeptKeys();
    renderWords();
    try { mv.nationNames = await api.nations(mv.lang); } catch { mv.nationNames = []; }  // the spawns' countries
    if (!mv.maps.length) {
      try {
        try {
          const view = (await api.prefs()).view || {};
          mv.kind = view.map_kind || mv.kind;
          foldMaps(Boolean(view.maps_folded));
          keptScenView(view);  // the Scenario tray's kinds shown and icon size, and the side the bar was on
          renderDockBar();
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
    if ((lang || "base") !== mv.lang) {
      scen.units = null;  // the Add unit tool's names (and the map's spawn names): loaded again in the new language
      scen.unitByAddress = null;
      scen.unitsFailed = false;
      if (mv.api) mv.api.nations(lang || "base").then((n) => { mv.nationNames = n; }).catch(() => {});
    }
    mv.lang = lang || "base";
    renderWords();
    renderScenTools();
    if (scen.data) drawScenario();  // the spawns' names (hover line, selection strip) in the new language
    renderList();
    if (mv.scenery.data) placeOptions();  // the props, trees and buildings to place, named in the new language
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
  // another mod was picked: its strokes on this map (or none) replace the ones drawn, and its new maps the list's
  modChanged() {
    if (mv.api && mv.maps.length) mv.api.maps().then((res) => { mv.maps = res.maps; renderList(); showTitle(); })
      .catch(() => {});
    if (mv.current && mv.edit) loadStrokes(mv.current, mv.ask).catch((err) => brushNote((err && err.message) || String(err), "error"));
    if (mv.current && mv.edit) loadPlaced(mv.current, mv.ask).catch((err) => placeNote((err && err.message) || String(err), "error"));
    if (mv.current && mv.edit) loadModRoads(mv.current, mv.ask).catch((err) => roadNote((err && err.message) || String(err), "error"));
  },
};
window.dispatchEvent(new Event("mapview-ready"));
