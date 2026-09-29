// The Maps view: the game's maps on the left, one map's ground in 3D on the right. Read-only for now; the terrain
// editor's brushes come next (PLAN.md milestone MT). The ground is the map's own visual mesh, lit by the game's own
// normals and draped with the map's overview picture (StudioApi.map_view, rusemod/terrain.py). three.js is loaded
// from the internet (see index.html) the first time the view opens.
const $ = (id) => document.getElementById(id);
const SCALE = 1 / 1000;  // world units to scene units: a standard map is about 1,300 scene units wide
const mv = { api: null, words: {}, maps: [], current: null, lod: "lowdef", water: true, gl: null, ask: 0,
  stats: null, groundTex: {} };

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
  mv.gl = { THREE, renderer, scene, camera, controls, draw, ground: null, water: null };
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
  for (let i = 0; i < n; i++) {
    const qx = q[3 * i], qy = q[3 * i + 1];
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
  return { ground, water, center: [(x0 + x1) / 2 * SCALE, (z0 + z1) / 2 * SCALE, (y0 + y1) / 2 * SCALE],
    size: Math.max(x1 - x0, y1 - y0) * SCALE };
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
  realGround(pack, ask).catch((err) => { $("map-ground").textContent = (err && err.message) || String(err); });
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
  $("map-help").textContent = w.map_help;
  if (!mv.current) $("map-pick").textContent = w.pick_map;
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
};
window.dispatchEvent(new Event("mapview-ready"));
