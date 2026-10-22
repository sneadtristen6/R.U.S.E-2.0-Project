"""A game model on its real skeleton, playing one of the game's animation clips, as one .glb: what RUSE Decoy's 3D
preview plays (three.js's AnimationMixer) and what Blender opens.

Mesh, UVs, normals, textures, bone numbers and weights come the way rusemod.gltf exports a model (the same axes,
mirror and 0.01 scale). What this adds (DomesticNukes' way, 2026-10-05: soldiers and horses seen running in Blender):
  - the skeleton from the model's skeleton pack (laid out as a clip's skeleton part): one node per bone at its rest
    pose from its parent, the inverse bind matrices from the inverse rest poses;
  - the clip (rusemod.baf): each bone's keys found by name (a clip moves the bones it names), every move, size and turn
    through the export's mirror M (x, y, z -> x, z, y): A' = M A M, moves x 0.01.
"""
from __future__ import annotations

import math
import struct

from . import baf, gltf
from .gltf import FLOAT, UINT, USHORT, _Glb, _point, _split, png_bytes, texture_member
from .unitpacks import NONE, MeshPack


class AnimGlbError(ValueError):
    pass


def _q_to_m(q):
    x, y, z, w = q
    return [[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]


def _m_to_q(r):
    tr = r[0][0] + r[1][1] + r[2][2]
    if tr > 0:
        k = math.sqrt(tr + 1.0) * 2
        q = ((r[2][1] - r[1][2]) / k, (r[0][2] - r[2][0]) / k, (r[1][0] - r[0][1]) / k, 0.25 * k)
    elif r[0][0] > r[1][1] and r[0][0] > r[2][2]:
        k = math.sqrt(1.0 + r[0][0] - r[1][1] - r[2][2]) * 2
        q = (0.25 * k, (r[0][1] + r[1][0]) / k, (r[0][2] + r[2][0]) / k, (r[2][1] - r[1][2]) / k)
    elif r[1][1] > r[2][2]:
        k = math.sqrt(1.0 + r[1][1] - r[0][0] - r[2][2]) * 2
        q = ((r[0][1] + r[1][0]) / k, 0.25 * k, (r[1][2] + r[2][1]) / k, (r[0][2] - r[2][0]) / k)
    else:
        k = math.sqrt(1.0 + r[2][2] - r[0][0] - r[1][1]) * 2
        q = ((r[0][2] + r[2][0]) / k, (r[1][2] + r[2][1]) / k, 0.25 * k, (r[1][0] - r[0][1]) / k)
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    return tuple(c / n for c in q)


_P = (0, 2, 1)   # the mirror: game axis _P[i] -> glTF axis i


def _mirror3(r):
    return [[r[_P[i]][_P[j]] for j in range(3)] for i in range(3)]


def _mirror_q(q):
    return _m_to_q(_mirror3(_q_to_m(q)))


def _rows(m):
    return [list(m[0:4]), list(m[4:8]), list(m[8:12])]


def _trs(m):
    """A 3x4 (the game's) -> glTF move, turn, size after the mirror."""
    m = _rows(m)
    r = _mirror3([row[:3] for row in m])
    t = _point(m[0][3], m[1][3], m[2][3])
    s = [math.sqrt(sum(r[i][j] ** 2 for i in range(3))) or 1.0 for j in range(3)]
    rot = [[r[i][j] / s[j] for j in range(3)] for i in range(3)]
    return list(t), list(_m_to_q(rot)), s


def _ibm(m):
    """A 3x4 (the game's, model -> bone) -> glTF column-major 4x4 after the mirror."""
    m = _rows(m)
    r = _mirror3([row[:3] for row in m])
    t = _point(m[0][3], m[1][3], m[2][3])
    return [r[0][0], r[1][0], r[2][0], 0.0, r[0][1], r[1][1], r[2][1], 0.0,
            r[0][2], r[1][2], r[2][2], 0.0, t[0], t[1], t[2], 1.0]


def model_skeleton(lib, model: str) -> dict | None:
    """A model's skeleton (rusemod.baf.skeleton's layout) from the game's skeleton packs, or None (no bones)."""
    for e in lib.arc.entries:
        p = e.path.lower()
        if not (p.startswith("gen_5\\pack\\") and p.endswith(".spk")):
            continue
        raw = bytes(lib.arc.read(e))
        if raw[:8] != b"MESHPCPC":
            continue
        try:
            pack = MeshPack.read(raw)
        except ValueError:
            continue
        item = pack.items.get(model)
        if item is not None and item[2] != NONE:
            return baf.skeleton(pack.skeletons[item[2]])
    return None


def glb(lib, model: str, clip: baf.Clip, side: int = 1024) -> tuple[bytes, dict]:
    """(the .glb, {"bones", "matched", "clip_bones", "seconds"}) for `model` (a name rusemod.models.Library knows)
    playing `clip`. A clip made for another skeleton moves only the bones whose names it shares."""
    sk = model_skeleton(lib, model)
    if sk is None:
        raise AnimGlbError(f"{model} has no skeleton: it can't play a clip")
    nb = sk["bones"]
    spk = lib.where[model]
    mats = spk.materials()
    parts = lib.parts(model)
    g = _Glb()
    stem = model.rsplit("\\", 1)[-1].replace("lod0.ase2ndfbin", "").replace(".ase2ndfbin", "")

    texture_of = {}
    for _part, tex in parts:
        if tex is None or tex in texture_of:
            continue
        pic = lib.picture(tex, most=side)
        if pic is None:
            continue
        w, h, rgba = pic
        colour, _grey = _split(rgba)
        tname = tex.rsplit("\\", 1)[-1].rsplit(".", 1)[0]
        idx = g.image(png_bytes(colour, w, h), tname)
        g.doc["materials"].append({"name": tname, "pbrMetallicRoughness": {
            "baseColorTexture": {"index": idx}, "metallicFactor": 0.0, "roughnessFactor": 0.8},
            "doubleSided": True, "extras": {"rusemod_texture": texture_member(tex)}})
        texture_of[tex] = len(g.doc["materials"]) - 1

    def skeleton_bone(part, local):
        remap = mats[part.material].get("skinning") if part.material < len(mats) else None
        return remap[local] if remap and local < len(remap) else local

    prims = []
    for part, tex in parts:
        n = len(part.positions) // 3
        attrs = {"POSITION": g.accessor([_point(*part.positions[3 * i:3 * i + 3]) for i in range(n)], "VEC3", FLOAT,
                                        minmax=True)}
        if part.normals:
            nrm = []
            for i in range(n):
                x, y, z = _point(*part.normals[3 * i:3 * i + 3], scale=1.0)
                L = math.sqrt(x * x + y * y + z * z) or 1.0
                nrm.append((x / L, y / L, z / L))
            attrs["NORMAL"] = g.accessor(nrm, "VEC3", FLOAT)
        if part.uvs:
            attrs["TEXCOORD_0"] = g.accessor([(part.uvs[2 * i], part.uvs[2 * i + 1]) for i in range(n)], "VEC2", FLOAT)
        js, ws = [], []
        for i in range(n):
            b = part.bones[i] if i < len(part.bones) else [0, 0, 0, 0]
            w = part.weights[i] if i < len(part.weights) else [255, 0, 0, 0]
            tot = sum(w)
            if not tot:
                js.append((0, 0, 0, 0))
                ws.append((1.0, 0.0, 0.0, 0.0))
                continue
            js.append(tuple(min(nb - 1, skeleton_bone(part, x)) if wx else 0 for x, wx in zip(b, w)))
            ws.append(tuple(wx / tot for wx in w))
        attrs["JOINTS_0"] = g.accessor(js, "VEC4", USHORT)
        attrs["WEIGHTS_0"] = g.accessor(ws, "VEC4", FLOAT)
        tri = list(part.indices)
        for k in range(0, len(tri) - 2, 3):
            tri[k + 1], tri[k + 2] = tri[k + 2], tri[k + 1]
        prim = {"attributes": attrs, "indices": g.accessor(tri, "SCALAR", UINT if n > 65535 else USHORT, 34963)}
        if tex in texture_of:
            prim["material"] = texture_of[tex]
        prims.append(prim)
    g.doc["meshes"].append({"name": stem, "primitives": prims})

    # the skeleton: node 0 the mesh, node 1 + b bone b
    g.doc["nodes"].append({"name": stem, "mesh": 0, "skin": 0})
    first = 1
    for b in range(nb):
        t, r, s = _trs(sk["local"][b])
        g.doc["nodes"].append({"name": sk["names"][b], "translation": t, "rotation": r, "scale": s})
    for b, p in enumerate(sk["parents"]):
        if p >= 0:
            g.doc["nodes"][first + p].setdefault("children", []).append(first + b)
    rig = len(g.doc["nodes"])
    g.doc["nodes"].append({"name": f"{stem}_rig", "children": [first + b for b, p in enumerate(sk["parents"]) if p < 0]})
    ibm = []
    for b in range(nb):
        ibm += _ibm(sk["bind"][b])
    g.doc["accessors"].append({"bufferView": g.view(struct.pack(f"<{len(ibm)}f", *ibm)), "componentType": FLOAT,
                               "count": nb, "type": "MAT4"})
    g.doc["skins"] = [{"name": f"{stem}_skin", "joints": list(range(first, first + nb)),
                       "inverseBindMatrices": len(g.doc["accessors"]) - 1, "skeleton": rig}]
    g.doc["scenes"] = [{"name": stem, "nodes": [0, rig]}]
    g.doc["scene"] = 0

    # the clip, bone by bone by name
    csk = baf.skeleton(clip.skeleton)
    dur = clip.duration if clip.frames > 1 and clip.duration > 0 else 1 / 30
    by_name = {n.lower(): i for i, n in enumerate(sk["names"])}
    samplers, channels, matched = [], [], 0
    for u, track in enumerate(clip.tracks):
        b = by_name.get(csk["names"][csk["index"][u]].lower())
        if b is None:
            continue
        matched += 1
        for path, keys in (("translation", track.T), ("scale", track.S), ("rotation", track.R)):
            ts = [0.0, dur] if len(keys) <= 2 else [k[0] / baf.LAST_TIME * dur for k in keys]
            if path == "translation":
                vals = [_point(*k[1:4]) for k in keys]
            elif path == "scale":
                vals = [(k[1], k[3], k[2]) for k in keys]
            else:
                vals = [_mirror_q(baf.unpack_quat(k[1:5])) for k in keys]
                for k in range(1, len(vals)):   # neighbours on the same side: no flips through 360 degrees
                    if sum(x * y for x, y in zip(vals[k], vals[k - 1])) < 0:
                        vals[k] = tuple(-x for x in vals[k])
            if len(keys) == 1:
                vals = vals * 2
            tin = g.accessor(ts, "SCALAR", FLOAT, target=None)
            g.doc["accessors"][tin]["min"], g.doc["accessors"][tin]["max"] = [min(ts)], [max(ts)]
            tout = g.accessor([tuple(v) for v in vals], "VEC4" if path == "rotation" else "VEC3", FLOAT, target=None)
            samplers.append({"input": tin, "output": tout, "interpolation": "LINEAR"})
            channels.append({"sampler": len(samplers) - 1, "target": {"node": first + b, "path": path}})
    g.doc["animations"] = [{"name": "clip", "samplers": samplers, "channels": channels}]
    return g.to_bytes(), {"bones": nb, "matched": matched, "clip_bones": clip.bones, "seconds": round(dur, 3)}
