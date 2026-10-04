"""The game's 3D models out to glTF 2.0 binary files (.glb), which Blender and other 3D tools open. Read-only.

One model becomes one mesh: each of its draw calls a primitive with its own texture. A unit texture's colour goes
into the .glb; its alpha is not see-through but the player's side colour (low) and shine (high), so it is written
as a grey picture of its own beside the .glb, with the colour as a picture too (for painting).

Skinned models (every unit) keep their bones: one joint per skeleton bone the model uses (through each material's
SkinningRemapping), all at the origin with identity bind matrices (the skeleton files' bone positions aren't read
yet), so the model shows as stored and every vertex keeps its bones and weights.

Axes: the game's model x, y, z (z up) are written as glTF's x, z, y (y up), times SCALE. That is a mirror, so
each triangle's winding is reversed too. Which way is right was checked on the T-26: its turret number reads
correctly in Blender this way. Each primitive's `extras` says which model, draw call and material it came from, and
each material's `extras` which texture (its .tgv in ZZ_Win.dat) it shows.

Propeller discs (material type `helice_1`, 43 draw calls on the planes, every one checked 2026-10-04) are a flat
square the game draws with a shader of its own, over the whole of the plane's picture. As a plain square that
picture is just in the way, so they go into a mesh of their own (`<model>_propeller`), which the Studio and Blender
keep hidden. Every unit model's other draw calls are material type `Standard`.
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

from .dxt import png_bytes
from .models import texture_member

SCALE = 0.01          # game model units -> glTF metres (a soldier is about 312 units tall)
MIRROR = True         # the game's (x, y, z) -> glTF (x, z, y); False: (x, z, -y)
PROPELLER = "helice"  # material types starting with this are propeller discs
FLOAT, UBYTE, USHORT, UINT = 5126, 5121, 5123, 5125


def _point(x: float, y: float, z: float, scale: float = SCALE) -> tuple[float, float, float]:
    return (x * scale, z * scale, y * scale) if MIRROR else (x * scale, z * scale, -y * scale)


class _Glb:
    """A glTF document being built, with one binary buffer."""

    def __init__(self):
        self.doc = {"asset": {"version": "2.0", "generator": "rusemod.gltf"}, "buffers": [], "bufferViews": [],
                    "accessors": [], "meshes": [], "nodes": [], "scenes": [], "materials": [], "textures": [],
                    "images": [], "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497,
                                                "wrapT": 10497}]}
        self.bin = bytearray()

    def view(self, data: bytes, target: int | None = None) -> int:
        while len(self.bin) % 4:
            self.bin.append(0)
        v = {"buffer": 0, "byteOffset": len(self.bin), "byteLength": len(data)}
        if target:
            v["target"] = target
        self.bin += data
        self.doc["bufferViews"].append(v)
        return len(self.doc["bufferViews"]) - 1

    def accessor(self, values: list, kind: str, ctype: int, target: int | None = 34962, minmax: bool = False,
                 normalized: bool = False) -> int:
        width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[kind]
        code = {FLOAT: "f", UBYTE: "B", USHORT: "H", UINT: "I"}[ctype]
        flat = [c for v in values for c in (v if width > 1 else (v,))]
        a = {"bufferView": self.view(struct.pack(f"<{len(flat)}{code}", *flat), target), "componentType": ctype,
             "count": len(values), "type": kind}
        if normalized:
            a["normalized"] = True
        if minmax:
            a["min"] = [min(v[i] for v in values) for i in range(width)]
            a["max"] = [max(v[i] for v in values) for i in range(width)]
        self.doc["accessors"].append(a)
        return len(self.doc["accessors"]) - 1

    def image(self, png: bytes, name: str) -> int:
        self.doc["images"].append({"bufferView": self.view(png), "mimeType": "image/png", "name": name})
        self.doc["textures"].append({"sampler": 0, "source": len(self.doc["images"]) - 1})
        return len(self.doc["textures"]) - 1

    def to_bytes(self) -> bytes:
        self.doc["buffers"] = [{"byteLength": len(self.bin)}]
        doc = {k: v for k, v in self.doc.items() if v != []}
        js = json.dumps(doc, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        binary = bytes(self.bin) + b"\0" * (-len(self.bin) % 4)
        total = 12 + 8 + len(js) + 8 + len(binary)
        return (struct.pack("<4sII", b"glTF", 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
                + struct.pack("<I4s", len(binary), b"BIN\0") + binary)


def _split(rgba: bytes) -> tuple[bytes, bytes]:
    """RGBA pixels -> (RGB colour, alpha as grey RGB)."""
    colour = bytearray(len(rgba) // 4 * 3)
    colour[0::3], colour[1::3], colour[2::3] = rgba[0::4], rgba[1::4], rgba[2::4]
    grey = bytearray(len(rgba) // 4 * 3)
    grey[0::3] = grey[1::3] = grey[2::3] = rgba[3::4]
    return bytes(colour), bytes(grey)


def model_glb(lib, name: str, side: int = 2048) -> tuple[bytes, dict[str, bytes], dict]:
    """One model of `lib` (rusemod.models.Library) as (.glb bytes, {picture file name: PNG bytes}, summary).
    Textures come from their mip level at most `side` pixels wide."""
    spk = lib.where[name]
    mats = spk.materials()
    parts = lib.parts(name)
    g = _Glb()
    pictures, summary = {}, {"model": name, "draw_calls": len(parts), "vertices": 0, "triangles": 0}
    stem = name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")

    # textures: colour into the .glb, colour and alpha as pictures beside it
    texture_of: dict[str, int] = {}
    for _part, tex in parts:
        if tex is None or tex in texture_of:
            continue
        pic = lib.picture(tex, most=side)
        if pic is None:
            continue
        w, h, rgba = pic
        colour, grey = _split(rgba)
        tname = tex.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        cpng = png_bytes(colour, w, h)
        pictures[f"{stem}_{tname}_colour.png"] = cpng
        pictures[f"{stem}_{tname}_alpha.png"] = png_bytes(grey, w, h)
        member = texture_member(tex)
        summary.setdefault("picture_of", {}).update({f"{stem}_{tname}_colour.png": (member, "colour"),
                                                     f"{stem}_{tname}_alpha.png": (member, "alpha")})
        texture_of[tex] = g.image(cpng, tname)
        g.doc["materials"].append({"name": tname, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": texture_of[tex]}, "metallicFactor": 0.0, "roughnessFactor": 0.8},
            "doubleSided": True, "extras": {"rusemod_texture": member}})
        texture_of[tex] = len(g.doc["materials"]) - 1

    # bones: every skeleton bone a vertex leans on
    def skeleton_bone(part, local: int) -> int:
        remap = mats[part.material].get("skinning") if part.material < len(mats) else None
        return remap[local] if remap and local < len(remap) else local

    used = {0}
    for part, _tex in parts:
        for b, w in zip(part.bones, part.weights):
            used.update(skeleton_bone(part, i) for i, x in zip(b, w) if x)
    joints = sorted(used)
    joint_of = {b: i for i, b in enumerate(joints)}
    skinned = any(part.bones for part, _t in parts)

    primitives, propellers = [], []
    for d, (part, tex) in enumerate(parts):
        n = len(part.positions) // 3
        pos = [_point(*part.positions[3 * i:3 * i + 3]) for i in range(n)]
        attrs = {"POSITION": g.accessor(pos, "VEC3", FLOAT, minmax=True)}
        if part.normals:
            nrm = []
            for i in range(n):
                x, y, z = _point(*part.normals[3 * i:3 * i + 3], scale=1.0)
                length = math.sqrt(x * x + y * y + z * z) or 1.0
                nrm.append((x / length, y / length, z / length))
            attrs["NORMAL"] = g.accessor(nrm, "VEC3", FLOAT)
        if part.uvs:
            attrs["TEXCOORD_0"] = g.accessor([(part.uvs[2 * i], part.uvs[2 * i + 1]) for i in range(n)], "VEC2", FLOAT)
        if skinned:
            js, ws = [], []
            for i in range(n):
                b = part.bones[i] if i < len(part.bones) else [0, 0, 0, 0]
                w = part.weights[i] if i < len(part.weights) else [255, 0, 0, 0]
                total = sum(w) or 0
                if total == 0:
                    js.append((joint_of[0], 0, 0, 0))
                    ws.append((1.0, 0.0, 0.0, 0.0))
                    continue
                js.append(tuple(joint_of[skeleton_bone(part, x)] if wx else 0 for x, wx in zip(b, w)))
                ws.append(tuple(wx / total for wx in w))
            attrs["JOINTS_0"] = g.accessor(js, "VEC4", USHORT)
            attrs["WEIGHTS_0"] = g.accessor(ws, "VEC4", FLOAT)
        tri = list(part.indices)
        if MIRROR:
            for k in range(0, len(tri) - 2, 3):
                tri[k + 1], tri[k + 2] = tri[k + 2], tri[k + 1]
        prim = {"attributes": attrs, "indices": g.accessor(tri, "SCALAR", UINT if n > 65535 else USHORT, 34963),
                "extras": {"rusemod_draw": d, "rusemod_material": part.material,
                           "rusemod_material_name": mats[part.material]["name"] if part.material < len(mats) else "",
                           "rusemod_texture": tex or ""}}
        if tex in texture_of:
            prim["material"] = texture_of[tex]
        kind = mats[part.material].get("type", "") if part.material < len(mats) else ""
        (propellers if kind.startswith(PROPELLER) else primitives).append(prim)
        summary["vertices"] += n
        summary["triangles"] += len(tri) // 3

    mesh_nodes = []
    for mesh_name, prims in ((stem, primitives), (f"{stem}_propeller", propellers)):
        if prims:
            g.doc["meshes"].append({"name": mesh_name, "primitives": prims})
            mesh_nodes.append({"name": mesh_name, "mesh": len(g.doc["meshes"]) - 1})
    g.doc["nodes"] += mesh_nodes
    roots = list(range(len(mesh_nodes)))
    summary["propellers"] = len(propellers)
    if skinned:
        first = len(g.doc["nodes"])
        g.doc["nodes"] += [{"name": f"bone_{b}"} for b in joints]
        rig = len(g.doc["nodes"])
        g.doc["nodes"].append({"name": f"{stem}_bones", "children": list(range(first, first + len(joints)))})
        identity = [1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0, 0, 0, 0, 0, 1.0]
        ibm = g.view(struct.pack(f"<{16 * len(joints)}f", *(identity * len(joints))))
        g.doc["accessors"].append({"bufferView": ibm, "componentType": FLOAT, "count": len(joints), "type": "MAT4"})
        g.doc["skins"] = [{"name": f"{stem}_skin", "joints": list(range(first, first + len(joints))),
                           "inverseBindMatrices": len(g.doc["accessors"]) - 1, "skeleton": rig}]
        for node in mesh_nodes:
            node["skin"] = 0
        roots.append(rig)
        summary["bones"] = joints
    g.doc["scenes"] = [{"name": stem, "nodes": roots}]
    g.doc["scene"] = 0
    g.doc["asset"]["extras"] = {"rusemod_model": name, "rusemod_scale": SCALE, "rusemod_mirror": MIRROR}
    return g.to_bytes(), pictures, summary


def export(lib, names: list[str], out: Path, side: int = 2048) -> list[dict]:
    """Write each model of `names` as <out>/<model>.glb with its pictures; returns each one's summary."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    done = []
    for name in names:
        glb, pictures, summary = model_glb(lib, name, side)
        stem = name.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")
        (out / f"{stem}.glb").write_bytes(glb)
        for fname, png in pictures.items():
            (out / fname).write_bytes(png)
        summary["file"] = str(out / f"{stem}.glb")
        summary["pictures"] = sorted(pictures)  # (summary["picture_of"]: each one's texture path and kind)
        done.append(summary)
    return done
