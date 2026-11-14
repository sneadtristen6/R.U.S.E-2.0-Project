"""Model files a player brings to Import model…, made here as the tools players use write them (Blender's glTF export:
y up, metres, one buffer, PNG pictures inside; tests/test_ownrig.py's little_glb for one with bones of its own and
animations): no tests of its own.

FOR: the models and Blender scenarios (release 0.9.8.20, overnight 2026-11-14,
D:/RUSE-2.0/scratch/release-0920/scenarios/models).
USED-BY: tests/test_scenarios_models_import.py, tests/test_scenarios_models_blender.py."""
import home_guard  # noqa: F401  (first: this test run's Studio home is a scratch folder, never the real one)
import json
import math
import struct

from rusemod.dxt import png_bytes
from rusemod.gltf import FLOAT, UINT, USHORT, _Glb

BOX_FACES = [(0, 1, 2), (0, 2, 3), (4, 6, 5), (4, 7, 6), (0, 4, 5), (0, 5, 1), (1, 5, 6), (1, 6, 2), (2, 6, 7),
             (2, 7, 3), (3, 7, 4), (3, 4, 0)]


def picture(w: int = 8, h: int = 8, rgb=(90, 110, 60), seed: int = 0) -> bytes:
    """A PNG picture of `w` x `h`, its colour `rgb` with a little pattern (`seed`), as a painter's would be."""
    out = bytearray()
    for i in range(w * h):
        out += bytes(((rgb[0] + seed + i) % 256, (rgb[1] + 3 * i) % 256, (rgb[2] + 7 * seed) % 256))
    return png_bytes(bytes(out), w, h)


def box(lo, hi) -> tuple[list, list, list, list]:
    """A box's 8 corners, 12 triangles (each pointing out), uvs and normals (from its middle), in glTF's axes."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1), (x0, y1, z0), (x1, y1, z0), (x1, y1, z1),
           (x0, y1, z1)]
    mid = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    normals = []
    for p in pts:
        d = [p[k] - mid[k] for k in range(3)]
        n = math.sqrt(sum(c * c for c in d)) or 1.0
        normals.append(tuple(c / n for c in d))
    uvs = [(0.25 * (k % 4), 0.5 * (k // 4)) for k in range(8)]
    return pts, list(BOX_FACES), uvs, normals


# a tank as a modeller makes one, in metres, y up, facing -z (glTF's front): hull 3 x 1.2 x 6.5, turret, gun
TANK_PARTS = [("Hull", (-1.5, 0.3, -3.25), (1.5, 1.5, 3.25)), ("Turret", (-1.0, 1.5, -1.5), (1.0, 2.3, 1.0)),
              ("Gun", (-0.1, 1.8, -5.5), (0.1, 2.0, -1.5))]


def tank_glb(parts=None, materials=None, part_material=None, scale: float = 1.0, root_scale=None, names=None,
             image_names=None, big_index: bool = False, mode: int | None = None,
             generator: str = "Khronos glTF Blender I/O", turret_turns: bool = False) -> bytes:
    """A static model (no bones) as Blender's glTF export writes one: each part a node with a mesh, materials with a
    base colour picture each. `parts` [(name, lo, hi)] (TANK_PARTS); `materials` [(name, png)] (one, "Paint");
    `part_material` [index of each part's material] (all 0); `scale`: every point that many times bigger (a file in
    centimetres: 100); `root_scale`: an empty above them all with that scale (Blender's "Apply scale" not done);
    `names` {part name: the node's and mesh's name}; `image_names` [each picture's name]; `big_index`: 32-bit indices;
    `mode`: the draw's mode (4 triangles when None; 0 points, 1 lines); `turret_turns`: the second part's node turns
    half round over two seconds in an animation called TurretTurn (no bones: a node animation)."""
    parts = parts or TANK_PARTS
    materials = materials or [("Paint", picture())]
    part_material = part_material or [0] * len(parts)
    names = names or {}
    g = _Glb()
    g.doc["asset"]["generator"] = generator
    for k, (name, png) in enumerate(materials):
        tex = g.image(png, (image_names or [name] * len(materials))[k])
        g.doc["materials"].append({"name": name, "pbrMetallicRoughness": {"baseColorTexture": {"index": tex},
                                                                          "metallicFactor": 0.0}})
    nodes = []
    for (name, lo, hi), mat in zip(parts, part_material):
        pts, tris, uvs, normals = box([c * scale for c in lo], [c * scale for c in hi])
        prim = {"attributes": {"POSITION": g.accessor(pts, "VEC3", FLOAT, minmax=True),
                               "NORMAL": g.accessor(normals, "VEC3", FLOAT),
                               "TEXCOORD_0": g.accessor(uvs, "VEC2", FLOAT)},
                "indices": g.accessor([i for t in tris for i in t], "SCALAR", UINT if big_index else USHORT, 34963),
                "material": mat}
        if mode is not None:
            prim["mode"] = mode
        shown = names.get(name, name)
        g.doc["meshes"].append({"name": shown, "primitives": [prim]})
        g.doc["nodes"].append({"name": shown, "mesh": len(g.doc["meshes"]) - 1})
        nodes.append(len(g.doc["nodes"]) - 1)
    if turret_turns and len(nodes) > 1:
        times = g.accessor([0.0, 1.0, 2.0], "SCALAR", FLOAT, target=None)
        g.doc["accessors"][times]["min"], g.doc["accessors"][times]["max"] = [0.0], [2.0]
        half = math.sqrt(0.5)
        turns = g.accessor([(0.0, 0.0, 0.0, 1.0), (0.0, half, 0.0, half), (0.0, 1.0, 0.0, 0.0)], "VEC4", FLOAT,
                           target=None)
        g.doc["animations"] = [{"name": "TurretTurn", "samplers": [{"input": times, "output": turns,
                                                                    "interpolation": "LINEAR"}],
                                "channels": [{"sampler": 0, "target": {"node": nodes[1], "path": "rotation"}}]}]
    if root_scale is not None:
        g.doc["nodes"].append({"name": "Empty", "children": nodes, "scale": [root_scale] * 3})
        nodes = [len(g.doc["nodes"]) - 1]
    g.doc["scenes"] = [{"name": "Scene", "nodes": nodes}]
    g.doc["scene"] = 0
    return g.to_bytes()


def grid_glb(side: int, picture_side: int = 8) -> bytes:
    """One flat mesh of side x side points (a scan or a sculpt, as Sketchfab's often are: tens of thousands of points in
    one part), 32-bit indices, one picture of `picture_side` pixels a side; laid out as a tank's length (6.5 m)."""
    g = _Glb()
    tex = g.image(picture(picture_side, picture_side), "Scan")
    g.doc["materials"].append({"name": "Scan", "pbrMetallicRoughness": {"baseColorTexture": {"index": tex}}})
    pts, uvs = [], []
    for j in range(side):
        for i in range(side):
            x, z = -1.5 + 3.0 * i / (side - 1), -3.25 + 6.5 * j / (side - 1)
            pts.append((x, 1.0 + 0.2 * math.sin(i * 0.3) * math.cos(j * 0.2), z))
            uvs.append((i / (side - 1), j / (side - 1)))
    idx = []
    for j in range(side - 1):
        for i in range(side - 1):
            a = j * side + i
            idx += [a, a + side, a + 1, a + 1, a + side, a + side + 1]
    data = struct.pack(f"<{len(pts) * 3}f", *[c for p in pts for c in p])
    pos = g.packed(data, len(pts), "VEC3", FLOAT, low=[min(p[k] for p in pts) for k in range(3)],
                   high=[max(p[k] for p in pts) for k in range(3)])
    uv = g.packed(struct.pack(f"<{len(uvs) * 2}f", *[c for u in uvs for c in u]), len(uvs), "VEC2", FLOAT)
    ind = g.packed(struct.pack(f"<{len(idx)}I", *idx), len(idx), "SCALAR", UINT, 34963)
    g.doc["meshes"].append({"name": "Scan", "primitives": [{"attributes": {"POSITION": pos, "TEXCOORD_0": uv},
                                                             "indices": ind, "material": 0}]})
    g.doc["nodes"].append({"name": "Scan", "mesh": 0})
    g.doc["scenes"] = [{"nodes": [0]}]
    g.doc["scene"] = 0
    return g.to_bytes()


def tank_gltf(folder, with_bin: bool = True, with_png: bool = True, turret_turns: bool = False):
    """tank_glb() written as Blender's "glTF Separate" export writes it: tank.gltf, tank.bin beside it and its picture
    paint.png (`with_bin`, `with_png`: those files left out, as when a player moves the .gltf alone). Returns the
    .gltf's path. `turret_turns`: the turret node turns half round in an animation of its own (a still model's
    animation, as a modeller makes to show a turret)."""
    from pathlib import Path
    from rusemod import gltf
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    raw = tank_glb(turret_turns=turret_turns)
    doc, views = gltf.glb_views(raw)
    png = views[doc["images"][0]["bufferView"]]
    doc["images"][0] = {"uri": "paint.png", "name": doc["images"][0].get("name", "Paint")}
    # (the picture's bytes out of the buffer: the rest packed as one .bin, the views renumbered)
    data = gltf.pack_glb(doc, views)
    doc2, binary = __import__("rusemod.modelin", fromlist=["glb_document"]).glb_document(data)
    doc2["buffers"] = [{"byteLength": len(binary), "uri": "tank.bin"}]
    (folder / "tank.gltf").write_text(json.dumps(doc2), encoding="utf-8")
    if with_bin:
        (folder / "tank.bin").write_bytes(binary)
    if with_png:
        (folder / "paint.png").write_bytes(png)
    return folder / "tank.gltf"


def repaint(send, colours: dict) -> None:
    """Blender's paint changed in what it sent (`send`, a path): each material named in `colours` ({name: (r, g, b)})
    shows a picture of that one colour, its size kept (a picture of another size gets the plain 144: alpha_sizes)."""
    from pathlib import Path
    from rusemod import gltf
    from rusemod.png import read_png
    send = Path(send)
    doc, views = gltf.glb_views(send.read_bytes())
    for m in doc["materials"]:
        if m["name"] in colours:
            image = doc["images"][doc["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
            w, h, _rgba = read_png(views[image["bufferView"]])
            image["bufferView"] = gltf.add_view(doc, views, png_bytes(bytes(colours[m["name"]]) * (w * h), w, h))
    send.write_bytes(gltf.pack_glb(doc, views))


def colours_in(model) -> dict:
    """{each picture of a model the mod keeps (rusemod.modelin.write_glb's), by its material's name: its first pixel's
    colour (r, g, b)}."""
    from pathlib import Path
    from rusemod import modelin
    from rusemod.png import read_png
    doc, binary = modelin.glb_document(Path(model).read_bytes())
    out = {}
    for m in doc["materials"]:
        k = m["pbrMetallicRoughness"]["baseColorTexture"]["index"]
        _w, _h, rgba = read_png(modelin.glb_image(doc, binary, doc["textures"][k]["source"]))
        out[m["name"]] = tuple(rgba[:3])
    return out


def broken_files(good: bytes) -> dict:
    """{what it is: its bytes} for the broken files a player can end up with (`good`: a sound .glb to break)."""
    js_len = struct.unpack_from("<I", good, 12)[0]
    doc = json.loads(good[20:20 + js_len])
    no_mesh = dict(doc)
    for k in ("meshes", "accessors", "materials", "textures", "images", "samplers"):
        no_mesh.pop(k, None)
    no_mesh["nodes"] = [{"name": "Camera"}]
    no_mesh["scenes"] = [{"nodes": [0]}]
    js = json.dumps(no_mesh).encode()
    js += b" " * (-len(js) % 4)
    rest = good[20 + js_len:]
    empty_scene = struct.pack("<4sII", b"glTF", 2, 20 + len(js) + len(rest)) + struct.pack("<I4s", len(js), b"JSON") \
        + js + rest
    bad_json = bytearray(good)
    bad_json[20:20 + 8] = b"{{{{{{{{"
    return {"empty": b"",
            "text renamed": "Ceci n'est pas un modèle 3D.\n".encode("utf-8"),
            "zip renamed": b"PK\x03\x04" + bytes(60),
            "cut in half": good[:len(good) // 2],
            "json broken": bytes(bad_json),
            "no mesh": empty_scene,
            "version 1": good[:4] + struct.pack("<I", 1) + good[8:]}
