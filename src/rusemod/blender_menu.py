"""Run by Blender, not by Python (`blender --python blender_menu.py -- <scene.json>`): a map's two pictures in the
game's menus (map.toml picture and wide_picture, docs/MOD_FORMAT.md §8) as two Blender scenes, the way the game's own
are made:

- "Big picture" (16:9): a view across the map's land or sea under a sky with clouds;
- "3D map" (680:200): the map as a slab seen from its front edge, its soil along the sides, nothing round it.

The Studio's Make in Blender writes scene.json (rusemod.menuscene: the map's ground, water, sea level, starting
points and both cameras) and starts Blender with this file; the modder changes anything, then clicks Save menu
pictures (the 3D view's header): both scenes are rendered into the files scene.json names, and the Studio's Bring
back takes them into the map. The scene is saved as scene.blend beside scene.json, and opening it again keeps the
modder's changes. Uses only Blender's own modules, so it never imports rusemod.

scene.json (rusemod.menuscene.write_scene) holds:
    kind            "map" (the map's own ground: ground.f32 / .u32, water.f32 / .u32 beside it) or "ocean" / "land"
                    (a blank map: flat sea or grass)
    size, top       the map's width and depth, and the height of its top (metres; x east, y north, z up)
    surroundings    "sea" or "land": what reaches from the map's edges to the horizon in the big picture
    starts          the starting points (x, y, z): markers in the 3D map, not rendered (the build draws the dots)
    big_camera, wide_camera, big_size, wide_size, picture, wide_picture, ground_picture
    background      true: build, render both, save and quit (no window): how the Studio's blank pictures are made
    samples, threads, exposure, look   (optional) Cycles' samples and threads, and the look's numbers (TUNABLE)

Everything the scene is made of is drawn by Blender from its own textures, or from the map's own ground picture, so a
render of a blank map is ours to give away. Anything that goes wrong is printed to Blender's console (Window > Toggle
System Console)."""
import json
import math
import os
import sys
import time
import traceback

import bpy
from mathutils import Vector

SUN_ELEVATION, SUN_TURN = 34.0, 125.0  # degrees: the sun high behind the viewer's right (a blue sky ahead)
SKY_STRENGTH = 0.16
DUST = 0.5                             # the air's haze (Blender's sky: dust density)
CLOUD_SIZE = 0.8                       # the clouds' noise scale on their layer (1 / a cloud's width over its height)
COVER = (0.5, 0.6)                     # the noise from where cloud starts to where it's solid: higher, less cloud
CLOUD_LIGHT = 1.4                      # how bright the clouds are
CLOUD_DETAIL = 5.0                     # the noise's layers of detail: fewer, rounder clouds
TUNABLE = ("SUN_ELEVATION", "SUN_TURN", "SKY_STRENGTH", "DUST", "CLOUD_SIZE", "COVER", "CLOUD_LIGHT", "CLOUD_DETAIL")
FAR = 200000.0                         # the surroundings' side (m): past the horizon either way
HAZE = {"sea": 26000.0, "land": 14000.0}  # how far off the ground has half faded into the horizon's sky (m)
BIG, WIDE = "Big picture", "3D map"    # the two scenes' names
SAVED = "saved.json"                   # written beside scene.json when both pictures are saved (the Studio reads it)
HINT = ("Two scenes (top bar, right): Big picture and 3D map. Change anything you like.",
        "Then click Save menu pictures (top of this view), and Bring back in the R.U.S.E. Studio.",
        "The white dots for the start points are added by the Studio's build, where they really are.")
CFG: dict = {}
FOLDER = ""


# --- small helpers for node trees ---
def nodes_of(owner):
    owner.use_nodes = True
    tree = owner.node_tree
    for n in list(tree.nodes):
        tree.nodes.remove(n)
    return tree.nodes, tree.links


def _noise(nodes, links, coord, scale: float, detail: float, roughness: float, distortion: float = 0.0):
    n = nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = roughness
    n.inputs["Distortion"].default_value = distortion
    links.new(coord, n.inputs["Vector"])
    return n


def _math(nodes, links, op: str, a, b):
    """a (op) b, each a socket or a number."""
    m = nodes.new("ShaderNodeMath")
    m.operation = op
    for i, x in enumerate((a, b)):
        if isinstance(x, (int, float)):
            m.inputs[i].default_value = x
        else:
            links.new(x, m.inputs[i])
    return m.outputs["Value"]


def _sum(nodes, links, parts):
    """Σ weight × value over (output socket, weight) pairs: a chain of multiply-adds."""
    total = None
    for socket, weight in parts:
        m = nodes.new("ShaderNodeMath")
        m.operation = "MULTIPLY_ADD"
        links.new(socket, m.inputs[0])
        m.inputs[1].default_value = weight
        if total is None:
            m.inputs[2].default_value = 0.0
        else:
            links.new(total, m.inputs[2])
        total = m.outputs["Value"]
    return total


def _range(nodes, links, value, lo: float, hi: float, to_lo: float = 0.0, to_hi: float = 1.0):
    """value mapped from lo..hi to to_lo..to_hi, held inside that."""
    m = nodes.new("ShaderNodeMapRange")
    m.clamp = True
    m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = lo, hi
    m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = to_lo, to_hi
    links.new(value, m.inputs["Value"])
    return m.outputs["Result"]


# --- the sky and the sun ---
def sun_direction() -> Vector:
    """Toward the sun: SUN_TURN degrees right of straight ahead (+Y), SUN_ELEVATION up."""
    e, a = math.radians(SUN_ELEVATION), math.radians(SUN_TURN)
    return Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))


def sky_texture(nodes):
    """The sky (Blender's own, from the sun's place and the air), the same wherever it's used."""
    tex = nodes.new("ShaderNodeTexSky")
    tex.sky_type = "NISHITA"
    tex.sun_disc = False                  # the sun lamp lights the scene; the sky only glows round it
    tex.sun_elevation = math.radians(SUN_ELEVATION)
    d = sun_direction()
    tex.sun_rotation = math.atan2(d.x, d.y)
    tex.air_density, tex.dust_density, tex.ozone_density = 1.0, DUST, 1.0
    return tex


def sky_world():
    """The sky with a layer of clouds painted on it: each way up is a point on a flat layer overhead (its distance
    out over its height), cloud where a noise there is high, lit on the side toward the sun and fading into the haze
    near the horizon. The sea reflects it."""
    world = bpy.data.worlds.new("Sky")
    nodes, links = nodes_of(world)
    tex = sky_texture(nodes)
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = SKY_STRENGTH
    links.new(tex.outputs["Color"], bg.inputs["Color"])
    way = nodes.new("ShaderNodeTexCoord").outputs["Generated"]       # the direction looked in
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(way, split.inputs[0])
    up = _math(nodes, links, "MAXIMUM", split.outputs["Z"], 0.01)
    on_layer = nodes.new("ShaderNodeCombineXYZ")
    links.new(_math(nodes, links, "DIVIDE", split.outputs["X"], up), on_layer.inputs["X"])
    links.new(_math(nodes, links, "DIVIDE", split.outputs["Y"], up), on_layer.inputs["Y"])
    d = sun_direction()
    toward = Vector((d.x, d.y, 0.0)).normalized() * 0.06
    shifted = nodes.new("ShaderNodeVectorMath")
    shifted.operation = "ADD"
    shifted.inputs[1].default_value = (toward.x, toward.y, 0.0)
    links.new(on_layer.outputs["Vector"], shifted.inputs[0])
    here = _noise(nodes, links, on_layer.outputs["Vector"], CLOUD_SIZE, CLOUD_DETAIL, 0.55, 0.3)
    sunward = _noise(nodes, links, shifted.outputs["Vector"], CLOUD_SIZE, CLOUD_DETAIL, 0.55, 0.3)
    cover = _math(nodes, links, "MULTIPLY", _range(nodes, links, here.outputs["Fac"], *COVER),
                  _range(nodes, links, split.outputs["Z"], 0.02, 0.22))
    lit = _range(nodes, links, _math(nodes, links, "SUBTRACT", here.outputs["Fac"], sunward.outputs["Fac"]),
                 -0.06, 0.06)
    shade = nodes.new("ShaderNodeMixRGB")
    shade.inputs["Color1"].default_value = (0.42, 0.45, 0.52, 1.0)    # the side away from the sun
    shade.inputs["Color2"].default_value = (1.0, 0.97, 0.92, 1.0)     # the side the sun lights
    links.new(lit, shade.inputs["Fac"])
    cloud = nodes.new("ShaderNodeBackground")
    cloud.inputs["Strength"].default_value = CLOUD_LIGHT
    links.new(shade.outputs["Color"], cloud.inputs["Color"])
    both = nodes.new("ShaderNodeMixShader")
    links.new(cover, both.inputs["Fac"])
    links.new(bg.outputs["Background"], both.inputs[1])
    links.new(cloud.outputs["Background"], both.inputs[2])
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(both.outputs["Shader"], out.inputs["Surface"])
    return world


def studio_world():
    """The 3D map's soft light all round (nothing of it shows: the render's background is see-through)."""
    world = bpy.data.worlds.new("Soft light")
    nodes, links = nodes_of(world)
    bg = nodes.new("ShaderNodeBackground")
    bg.inputs["Color"].default_value = (0.62, 0.68, 0.76, 1.0)
    bg.inputs["Strength"].default_value = 0.55
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(bg.outputs["Background"], out.inputs["Surface"])
    return world


def sun_lamp(name: str, direction: Vector, energy: float):
    light = bpy.data.lights.new(name, "SUN")
    light.energy, light.angle = energy, math.radians(0.6)
    light.color = (1.0, 0.94, 0.86)
    obj = bpy.data.objects.new(name, light)
    obj.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    return obj


# --- materials ---
def fogged(nodes, links, shader, reach: float):
    """`shader` fading with its distance into the sky's colour just over the horizon behind it (half gone at
    `reach` m): the far ground melts into the sky as seen through air, and the sky itself stays as it is."""
    look = nodes.new("ShaderNodeNewGeometry").outputs["Incoming"]   # toward the camera
    away = nodes.new("ShaderNodeVectorMath")
    away.operation = "SCALE"
    away.inputs["Scale"].default_value = -1.0
    links.new(look, away.inputs[0])
    split = nodes.new("ShaderNodeSeparateXYZ")
    links.new(away.outputs["Vector"], split.inputs[0])
    flat = nodes.new("ShaderNodeCombineXYZ")
    links.new(split.outputs["X"], flat.inputs["X"])
    links.new(split.outputs["Y"], flat.inputs["Y"])
    flat.inputs["Z"].default_value = 0.02
    unit = nodes.new("ShaderNodeVectorMath")
    unit.operation = "NORMALIZE"
    links.new(flat.outputs["Vector"], unit.inputs[0])
    tex = sky_texture(nodes)
    links.new(unit.outputs["Vector"], tex.inputs["Vector"])
    glow = nodes.new("ShaderNodeEmission")
    glow.inputs["Strength"].default_value = SKY_STRENGTH
    links.new(tex.outputs["Color"], glow.inputs["Color"])
    dist = nodes.new("ShaderNodeCameraData").outputs["View Distance"]
    kept = _math(nodes, links, "EXPONENT", _math(nodes, links, "MULTIPLY", dist, -math.log(2.0) / reach), 0.0)
    gone = _math(nodes, links, "SUBTRACT", 1.0, kept)
    mix = nodes.new("ShaderNodeMixShader")
    links.new(gone, mix.inputs["Fac"])
    links.new(shader, mix.inputs[1])
    links.new(glow.outputs["Emission"], mix.inputs[2])
    return mix.outputs["Shader"]


def _surface(nodes, links, bsdf, out, haze: str | None) -> None:
    """The material's surface: `bsdf`, faded into the sky with distance as HAZE[`haze`] says (the big picture's),
    or not at all (None)."""
    shader = bsdf.outputs["BSDF"]
    links.new(fogged(nodes, links, shader, HAZE[haze]) if haze else shader, out.inputs["Surface"])


def sea_material(name: str = "Sea", haze: str | None = "sea"):
    mat = bpy.data.materials.new(name)
    nodes, links = nodes_of(mat)
    pos = nodes.new("ShaderNodeTexCoord").outputs["Object"]
    swell = nodes.new("ShaderNodeTexWave")            # long swells across the view
    swell.wave_type, swell.bands_direction = "BANDS", "Y"
    swell.inputs["Scale"].default_value = 0.02
    swell.inputs["Distortion"].default_value = 9.0
    swell.inputs["Detail"].default_value = 4.0
    links.new(pos, swell.inputs["Vector"])
    waves = _noise(nodes, links, pos, 0.09, 6.0, 0.58, 0.4)   # the waves on them
    chop = _noise(nodes, links, pos, 0.8, 8.0, 0.62)           # the chop on the waves
    height = _sum(nodes, links, [(swell.outputs["Fac"], 0.25), (waves.outputs["Fac"], 0.55),
                                 (chop.outputs["Fac"], 0.3)])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.65
    bump.inputs["Distance"].default_value = 1.4
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Base Color"].default_value = (0.005, 0.03, 0.055, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["IOR"].default_value = 1.333
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(height, bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    _surface(nodes, links, bsdf, out, haze)
    return mat


def grass_material(name: str = "Grass", haze: str | None = "land"):
    mat = bpy.data.materials.new(name)
    nodes, links = nodes_of(mat)
    pos = nodes.new("ShaderNodeTexCoord").outputs["Object"]
    fields = _noise(nodes, links, pos, 0.004, 6.0, 0.58)        # big patches of lighter and darker grass
    tufts = _noise(nodes, links, pos, 0.03, 4.0, 0.5)           # and smaller ones in them
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.38, 0.62
    ramp.color_ramp.elements[0].color = (0.06, 0.15, 0.012, 1.0)
    ramp.color_ramp.elements[1].color = (0.16, 0.26, 0.02, 1.0)
    links.new(_sum(nodes, links, [(fields.outputs["Fac"], 0.75), (tufts.outputs["Fac"], 0.25)]), ramp.inputs["Fac"])
    blades = _noise(nodes, links, pos, 3.0, 10.0, 0.7)          # the grass up close
    shade = nodes.new("ShaderNodeMixRGB")
    shade.blend_type = "MULTIPLY"
    shade.inputs["Fac"].default_value = 0.35
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    bump.inputs["Distance"].default_value = 0.2
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.92
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(ramp.outputs["Color"], shade.inputs["Color1"])
    links.new(blades.outputs["Color"], shade.inputs["Color2"])
    links.new(shade.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(blades.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    _surface(nodes, links, bsdf, out, haze)
    return mat


def ground_material(picture: str | None, name: str = "Ground", haze: str | None = "land"):
    """The map's ground: its own picture (the Studio's, from its texture tiles) on it, else plain grass."""
    if not picture or not os.path.isfile(picture):
        return grass_material(name, haze)
    mat = bpy.data.materials.new(name)
    nodes, links = nodes_of(mat)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(picture, check_existing=True)
    tex.extension = "EXTEND"
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.9
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    _surface(nodes, links, bsdf, out, haze)
    return mat


def soil_material():
    """The slab's sides: dark earth in thin layers, as the game's own 3D maps."""
    mat = bpy.data.materials.new("Soil")
    nodes, links = nodes_of(mat)
    pos = nodes.new("ShaderNodeTexCoord").outputs["Object"]
    layers = nodes.new("ShaderNodeTexWave")
    layers.wave_type, layers.bands_direction = "BANDS", "Z"
    layers.inputs["Scale"].default_value = 0.004
    layers.inputs["Distortion"].default_value = 3.0
    layers.inputs["Detail"].default_value = 6.0
    links.new(pos, layers.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.018, 0.012, 0.007, 1.0)
    ramp.color_ramp.elements[1].color = (0.05, 0.036, 0.022, 1.0)
    links.new(layers.outputs["Fac"], ramp.inputs["Fac"])
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


def marker_material():
    mat = bpy.data.materials.new("Start point")
    nodes, links = nodes_of(mat)
    glow = nodes.new("ShaderNodeEmission")
    glow.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    glow.inputs["Strength"].default_value = 2.0
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(glow.outputs["Emission"], out.inputs["Surface"])
    return mat


# --- the map ---
def mesh_object(name: str, verts, faces, material, uvs=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    if uvs is not None:
        layer = mesh.uv_layers.new(name="UVMap")
        flat = [c for f in faces for i in f for c in uvs[i]]
        layer.data.foreach_set("uv", flat)
    mesh.materials.append(material)
    mesh.validate()
    mesh.update()
    return bpy.data.objects.new(name, mesh)


def read_mesh(stem: str, width: int):
    """(points as rows of `width` numbers, triangles) from <stem>.f32 / <stem>.u32 beside scene.json."""
    import numpy as np
    pts = np.fromfile(os.path.join(FOLDER, stem + ".f32"), dtype="<f4").reshape(-1, width)
    tri = np.fromfile(os.path.join(FOLDER, stem + ".u32"), dtype="<u4").reshape(-1, 3)
    return pts, tri


def twin(obj, name: str, material):
    """Another object on `obj`'s mesh with a material of its own (in the object's slot, not the mesh's)."""
    other = bpy.data.objects.new(name, obj.data)
    other.material_slots[0].link = "OBJECT"
    other.material_slots[0].material = material
    return other


def map_objects(kind: str) -> tuple[list, list]:
    """The map itself, twice over the same meshes: for the big picture (fading into the sky with distance) and for
    the 3D map (seen from tens of kilometres off, so not fading): its ground (the map's own, or a blank map's flat
    top) and the water over it."""
    w, d = CFG["size"]
    top = CFG["top"]
    if kind != "map":
        h, k = w / 2, d / 2
        near, far = ((sea_material("Map sea"), sea_material("Map sea (3D map)", None)) if kind == "ocean" else
                     (grass_material("Map grass"), grass_material("Map grass (3D map)", None)))
        ground = mesh_object("Ground", [(-h, -k, top), (h, -k, top), (h, k, top), (-h, k, top)], [(0, 1, 2, 3)], near)
        return [ground], [twin(ground, "Ground (3D map)", far)]
    pts, tri = read_mesh("ground", 5)
    picture = CFG.get("ground_picture")
    ground = mesh_object("Ground", pts[:, :3].tolist(), tri.tolist(), ground_material(picture),
                         uvs=pts[:, 3:5].tolist())
    bigs, wides = [ground], [twin(ground, "Ground (3D map)", ground_material(picture, "Ground (3D map)", None))]
    wpts, wtri = read_mesh("water", 3)
    if len(wtri):
        water = mesh_object("Water", wpts.tolist(), wtri.tolist(), sea_material("Map water"))
        bigs.append(water)
        wides.append(twin(water, "Water (3D map)", sea_material("Map water (3D map)", None)))
    return bigs, wides


def surroundings_object(material, z: float, hole: bool):
    """From the map's edges (or, with no map, from under the camera) to past the horizon, at height `z`."""
    w, d = CFG["size"]
    h, a, b = FAR / 2, w / 2, d / 2
    if not hole:
        return mesh_object("Surroundings", [(-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z)], [(0, 1, 2, 3)], material)
    verts = [(-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z), (-a, -b, z), (a, -b, z), (a, b, z), (-a, b, z)]
    return mesh_object("Surroundings", verts, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material)


def edge_heights(kind: str):
    """The map's top along its four edges, for the slab's sides: {side: [(along, z)]} in order, each side's ends
    included."""
    w, d = CFG["size"]
    top = CFG["top"]
    if kind != "map":
        return {s: [(-1.0, top), (1.0, top)] for s in ("south", "east", "north", "west")}
    import numpy as np
    pts, _tri = read_mesh("ground", 5)
    x, y, z = pts[:, 0], pts[:, 1], pts[:, 2]
    eps = 1e-4 * max(w, d)
    sides = {"south": (np.abs(y + d / 2) < eps, x / (w / 2)), "north": (np.abs(y - d / 2) < eps, -x / (w / 2)),
             "east": (np.abs(x - w / 2) < eps, y / (d / 2)), "west": (np.abs(x + w / 2) < eps, -y / (d / 2))}
    out = {}
    for side, (on, along) in sides.items():
        a, h = along[on], z[on]
        order = np.argsort(a)
        out[side] = list(zip(a[order].tolist(), h[order].tolist())) or [(-1.0, top), (1.0, top)]
    return out


def slab_sides(kind: str):
    """The slab's four sides and its bottom: from the map's top along its edges down to the soil's depth."""
    w, d = CFG["size"]
    bottom = CFG["top"] - CFG["wide_camera"]["soil"]
    corner = {"south": lambda a: (a * w / 2, -d / 2), "north": lambda a: (-a * w / 2, d / 2),
              "east": lambda a: (w / 2, a * d / 2), "west": lambda a: (-w / 2, -a * d / 2)}
    verts, faces = [], []
    for side, line in edge_heights(kind).items():
        start = len(verts)
        for a, z in line:
            px, py = corner[side](a)
            verts += [(px, py, z), (px, py, bottom)]
        for i in range(len(line) - 1):
            j = start + 2 * i
            faces.append((j, j + 1, j + 3, j + 2))
    b = len(verts)
    verts += [(-w / 2, -d / 2, bottom), (w / 2, -d / 2, bottom), (w / 2, d / 2, bottom), (-w / 2, d / 2, bottom)]
    faces.append((b + 3, b + 2, b + 1, b))
    return mesh_object("Slab sides", verts, faces, soil_material())


def start_markers() -> list:
    """A white disc on each starting point: seen in Blender, not rendered (the build draws the dots, where the
    starting points are when the map is built)."""
    import bmesh
    w, _d = CFG["size"]
    r = 0.0086 * w
    mat = marker_material()
    out = []
    for i, (x, y, z) in enumerate(CFG.get("starts", [])):
        mesh = bpy.data.meshes.new(f"Start point {i + 1}")
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=24, radius=r)
        bm.to_mesh(mesh)
        bm.free()
        mesh.materials.append(mat)
        obj = bpy.data.objects.new(f"Start point {i + 1}", mesh)
        obj.location = (x, y, max(z, CFG["top"]) + 0.002 * w)
        obj.hide_render = True
        out.append(obj)
    return out


def camera_object(name: str, spec: dict, size, clip: float):
    cam = bpy.data.cameras.new(name)
    cam.lens, cam.sensor_width, cam.sensor_fit = spec["lens"], 36.0, "HORIZONTAL"
    cam.clip_start, cam.clip_end = 1.0, clip
    obj = bpy.data.objects.new(name, cam)
    obj.location = spec["location"]
    obj.rotation_euler = spec["rotation"]
    return obj


def render_settings(scene, size, samples: int, see_through: bool) -> None:
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    if CFG.get("threads"):
        scene.render.threads_mode, scene.render.threads = "FIXED", int(CFG["threads"])
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = size[0], size[1], 100
    scene.render.film_transparent = see_through
    scene.view_settings.view_transform = "AgX"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:  # a Blender without that look: AgX's own
        pass
    scene.view_settings.exposure = float(CFG.get("exposure", 0.2))
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA" if see_through else "RGB"


def link(scene, objects) -> None:
    for obj in objects:
        scene.collection.objects.link(obj)


def build() -> None:
    """Both scenes from scene.json, Blender's starting scene cleared away first."""
    for name, value in (CFG.get("look") or {}).items():  # the look's numbers changed for this scene
        if name not in TUNABLE:
            raise ValueError(f"look: no {name!r} ({', '.join(TUNABLE)})")
        globals()[name] = tuple(value) if isinstance(value, list) else value
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    kind = CFG.get("kind", "ocean")
    if kind == "map":  # seen from high up over tens of kilometres: thinner air, or the map fades away
        HAZE.update(sea=90000.0, land=60000.0)
    if "size" not in CFG:  # a blank map's big picture alone (how the Studio's own were made)
        CFG.update(size=[39321.6, 26214.4], top=0.0, starts=[],
                   big_camera={"location": [0.0, 0.0, 9.0 if kind == "ocean" else 24.0],
                               "rotation": [math.radians(95.0 if kind == "ocean" else 94.5), 0.0, 0.0], "lens": 28.0},
                   surroundings="sea" if kind == "ocean" else "land", only_big=True)
    big = bpy.context.scene
    big.name = BIG
    big.world = sky_world()
    render_settings(big, CFG.get("big_size", [CFG.get("width", 1280), CFG.get("height", 720)]),
                    int(CFG.get("samples", 48)), False)
    sea_z = CFG.get("ground", {}).get("sea", CFG["top"])
    around = sea_material() if CFG.get("surroundings") == "sea" else grass_material()
    surroundings = surroundings_object(around, sea_z, hole=not CFG.get("only_big"))
    sun = sun_lamp("Sun", sun_direction(), 3.2)
    big_cam = camera_object("Big picture camera", CFG["big_camera"], None, FAR)
    mine, mine_far = ([], []) if CFG.get("only_big") else map_objects(kind)
    link(big, [surroundings, sun, big_cam] + mine)
    big.camera = big_cam
    if CFG.get("only_big"):
        return
    wide = bpy.data.scenes.new(WIDE)
    wide.world = studio_world()
    render_settings(wide, CFG.get("wide_size", [1360, 400]), int(CFG.get("wide_samples", 32)), True)
    w, d = CFG["size"]
    key = sun_lamp("Key light", Vector((-0.45, -0.6, 0.66)).normalized(), 3.0)
    wide_cam = camera_object("3D map camera", CFG["wide_camera"], None, 10 * (w + d))
    link(wide, mine_far + [slab_sides(kind), key, wide_cam] + start_markers())
    wide.camera = wide_cam


# --- saving the pictures ---
def save_pictures() -> list:
    """Render both scenes into the files scene.json names; returns them."""
    done = []
    for name, key in ((BIG, "picture"), (WIDE, "wide_picture")):
        scene = bpy.data.scenes.get(name)
        if scene is None or not CFG.get(key):
            continue
        scene.render.filepath = CFG[key]
        bpy.ops.render.render(write_still=True, scene=name)
        done.append(CFG[key])
    with open(os.path.join(FOLDER, SAVED), "w", encoding="utf-8") as f:
        json.dump({"saved": done, "time": time.time()}, f)
    return done


class RUSE_OT_save_menu_pictures(bpy.types.Operator):
    """Render both scenes and save them as the map's menu pictures"""
    bl_idname = "ruse.save_menu_pictures"
    bl_label = "Save menu pictures"

    def execute(self, context):
        try:
            if bpy.data.filepath:
                bpy.ops.wm.save_mainfile()           # the scene as changed, for the next time
            saved = save_pictures()
        except Exception as exc:  # noqa: BLE001
            traceback.print_exc()
            self.report({"ERROR"}, f"Couldn't save the pictures: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Saved {len(saved)} picture(s). Now click Bring back in the R.U.S.E. Studio.")
        return {"FINISHED"}


def header_button(self, context):
    self.layout.operator(RUSE_OT_save_menu_pictures.bl_idname, text="Save menu pictures", icon="FILE_TICK")


def draw_hint():
    try:
        scale = bpy.context.preferences.system.ui_scale
        top = bpy.context.region.height
        import blf
        blf.size(0, 14 * scale)
        blf.enable(0, blf.SHADOW)
        blf.shadow(0, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(0, 1, -1)
        blf.color(0, 1.0, 0.95, 0.75, 1.0)
        for i, line in enumerate(HINT):
            blf.position(0, 60 * scale, top - (128 + 20 * i) * scale, 0)
            blf.draw(0, line)
        blf.disable(0, blf.SHADOW)
    except Exception:  # noqa: BLE001
        pass


def add_saving() -> None:
    bpy.utils.register_class(RUSE_OT_save_menu_pictures)
    bpy.types.VIEW3D_HT_header.prepend(header_button)
    bpy.types.SpaceView3D.draw_handler_add(draw_hint, (), "WINDOW", "POST_PIXEL")


def look_through_camera() -> None:
    """Each 3D view looking through the big picture's camera, shaded with its materials."""
    try:
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    space = area.spaces.active
                    space.shading.type = "MATERIAL"
                    space.region_3d.view_perspective = "CAMERA"
                    space.clip_end = FAR
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    return None


def save_blend(path: str) -> None:
    """The new scene saved as scene.blend, so the Studio opens it as it was left the next time."""
    try:
        bpy.ops.wm.save_as_mainfile(filepath=path)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
    return None


def main() -> None:
    global FOLDER
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not args:
        print("blender_menu.py: give the scene's json file after --")
        return
    with open(args[0], encoding="utf-8") as f:
        CFG.update(json.load(f))
    FOLDER = os.path.dirname(os.path.abspath(args[0]))
    blend = os.path.join(FOLDER, "scene.blend")
    if not bpy.data.filepath:  # a new scene (Blender opened scene.blend itself when it was there)
        build()
        if not CFG.get("background") and not CFG.get("only_big"):
            bpy.app.timers.register(lambda: save_blend(blend), first_interval=1.0)  # once the window is up
    if CFG.get("background"):
        saved = save_pictures()
        print("blender_menu.py: wrote", ", ".join(saved))
        return
    add_saving()
    bpy.app.timers.register(look_through_camera, first_interval=0.5)


try:
    main()
except Exception:  # noqa: BLE001  (shown in Blender's console, and the run's exit says it failed)
    traceback.print_exc()
    if "-b" in sys.argv or "--background" in sys.argv:
        sys.exit(1)
